# -*- coding: utf-8 -*-
"""Pull a static web page and the pages it links to (same host, same path prefix) into
plain-text files under _incoming/, split into one entry per heading.

  list   <start-url> [--prefix P] [--toc URL]          print the pages that would be fetched
  fetch  <start-url> --out DIR [--prefix P] [--toc URL] save raw html + text per page, manifest.json
  split  --out DIR [--book B --component C]            cut each saved page into entries, write index.md

WinCHM "webhelp" shells (?page=<path>) are resolved to /topics/<path> automatically.
Only the standard library is used.
"""
import argparse, concurrent.futures as cf, glob, html, json, os, re, sys, time, unicodedata
import urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (translation-import web-source-extract)"}


def get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            raw = urllib.request.urlopen(req, timeout=60).read()
            return raw.decode("utf-8", "ignore")
        except Exception as e:  # noqa: BLE001 - report the last failure to the caller
            last = e
            time.sleep(1 + i)
    raise RuntimeError("%s: %s" % (url, last))


def resolve(url):
    """?page=X on a webhelp shell means the content lives at /topics/X."""
    u = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qs(u.query)
    if "page" in q:
        return "%s://%s/topics/%s" % (u.scheme, u.netloc, urllib.parse.quote(q["page"][0]))
    return url


def links(page_url, text):
    out = []
    for h in re.findall(r'href="([^"#]+)', text):
        absu = urllib.parse.urljoin(page_url, html.unescape(h))
        out.append(absu)
    return out


def candidates(start, prefix, toc):
    start = resolve(start)
    host = urllib.parse.urlparse(start).netloc
    pages = {start}
    for src in [start] + ([toc] if toc else []):
        for l in links(src, get(src)):
            p = urllib.parse.urlparse(l)
            path = urllib.parse.unquote(p.path)
            if p.netloc == host and not re.search(r"\.(css|js|png|jpe?g|gif|svg|ico|woff2?|pdf|zip)$", path, re.I) and (not prefix or prefix in path):
                pages.add(l.split("#")[0])
    return sorted(pages)


def to_text(raw):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</?(p|div|tr|td|th|li|h[1-6]|table|thead|tbody|section)\b[^>]*>", "\n", t, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    t = unicodedata.normalize("NFKC", t)  # kangxi radicals such as ⼔⾸ become 刀首-style normal forms
    lines = [l.strip() for l in t.split("\n")]
    return "\n".join(l for l in lines if l) + "\n"


def slug(url):
    p = urllib.parse.unquote(urllib.parse.urlparse(url).path).strip("/")
    return re.sub(r"[\/:*?\"<>|]+", "_", p) or "index"


def cmd_list(a):
    for p in candidates(a.start, a.prefix, a.toc):
        print(urllib.parse.unquote(p))


def cmd_fetch(a):
    os.makedirs(os.path.join(a.out, "_raw"), exist_ok=True)
    pages = candidates(a.start, a.prefix, a.toc)

    def one(u):
        try:
            raw = get(u)
            n = slug(u)
            open(os.path.join(a.out, "_raw", n + ".html"), "w", encoding="utf-8").write(raw)
            open(os.path.join(a.out, n + ".txt"), "w", encoding="utf-8").write(to_text(raw))
            return u, "ok", n
        except Exception as e:  # noqa: BLE001
            return u, "failed: %s" % e, None

    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(one, pages))
    json.dump([{"url": u, "status": s, "file": n} for u, s, n in res], open(os.path.join(a.out, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    bad = [r for r in res if r[1] != "ok"]
    print("%d 頁，成功 %d，失敗 %d" % (len(res), len(res) - len(bad), len(bad)))
    for u, s, _ in bad:
        print("  ", u, s)


HEAD = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.S | re.I)


def cmd_split(a):
    keys = {}
    if a.book:
        # 資料夾名與檔名不一定相同（dnd-heros-faerun/dnd-heroes-faerun.options.json）
        hits = glob.glob("compendium/en/%s/*.%s.json" % (a.book, a.component))
        if len(hits) != 1:
            sys.exit("找不到唯一的 EN 模板：compendium/en/%s/*.%s.json → %s" % (a.book, a.component, hits))
        en = json.load(open(hits[0], encoding="utf-8"))["entries"]
        keys = {k.lower(): k for k in en}
    raw_dir = os.path.join(a.out, "_raw")
    rows, unmatched = [], []
    for f in sorted(os.listdir(raw_dir)):
        raw = open(os.path.join(raw_dir, f), encoding="utf-8").read()
        body = raw.split("<body", 1)[-1]
        parts = HEAD.split(body)  # [pre, level, heading, content, level, heading, content ...]
        entries = []
        for i in range(1, len(parts) - 2, 3):
            head = re.sub(r"\s+", " ", to_text(parts[i + 1])).strip()
            entries.append((head, to_text(parts[i + 2]).strip()))
        if not entries:
            continue
        name = os.path.splitext(f)[0]
        open(os.path.join(a.out, name + ".entries.txt"), "w", encoding="utf-8").write("\n\n".join("%s\n%s" % e for e in entries) + "\n")
        for head, _ in entries:
            m = re.search(r"([A-Za-z][A-Za-z'’\-, +0-9()]*)$", head)
            en_name = m.group(1).strip() if m else ""
            key = keys.get(en_name.lower(), "") if keys else ""
            rows.append((name, head, key))
            if keys and not key:
                unmatched.append((name, head))
    with open(os.path.join(a.out, "index.md"), "w", encoding="utf-8") as w:
        w.write("| 檔案 | 標題 | EN key |\n|---|---|---|\n")
        for r in rows:
            w.write("| %s | %s | %s |\n" % r)
        if unmatched:
            w.write("\n## 對不上 EN 模板\n")
            for n, h in unmatched:
                w.write("- %s：%s\n" % (n, h))
    print("條目 %d，對不上 EN %d" % (len(rows), len(unmatched)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("list", "fetch"):
        p = sub.add_parser(n)
        p.add_argument("start")
        p.add_argument("--prefix", default="", help="只保留路徑（已解碼）包含此字串的連結")
        p.add_argument("--toc", default="", help="另一個用來列出連結的目錄頁網址")
        if n == "fetch":
            p.add_argument("--out", required=True)
    p = sub.add_parser("split")
    p.add_argument("--out", required=True)
    p.add_argument("--book", default="")
    p.add_argument("--component", default="")
    a = ap.parse_args()
    {"list": cmd_list, "fetch": cmd_fetch, "split": cmd_split}[a.cmd](a)


if __name__ == "__main__":
    main()
