# -*- coding: utf-8 -*-
"""Weblate REST client + CLI for the translation-import skill.

Reads WEBLATE_URL and WEBLATE_API_TOKEN from the environment (falling back to the
Windows user environment registry, because `setx` only reaches newly spawned
processes). The token is never printed.

Absolute URLs returned by the API are ignored on purpose: this instance has
WEBLATE_SITE_DOMAIN misconfigured (it returns http://weblate.com/...), so
following `next` links would hit a public website instead of localhost.
"""
import argparse, json, os, sys, urllib.error, urllib.parse, urllib.request, uuid

try:
    import winreg
except ImportError:
    winreg = None


def env(name):
    value = os.environ.get(name)
    if value:
        return value
    if winreg is not None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                return winreg.QueryValueEx(key, name)[0]
        except OSError:
            pass
    sys.exit("環境變數 %s 未設定。請先執行：setx %s \"<值>\"" % (name, name))


BASE = env("WEBLATE_URL").rstrip("/")
TOKEN = env("WEBLATE_API_TOKEN")


def call(method, path, data=None, headers=None, raw=False):
    hdrs = {"Authorization": "Token " + TOKEN}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(BASE + path, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return resp.status, (body if raw else json.loads(body or b"null"))
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def form(method, path, fields):
    data = urllib.parse.urlencode(fields).encode()
    return call(method, path, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})


def paged(path):
    """Yield results across pages, building page URLs ourselves."""
    page, joiner = 1, ("&" if "?" in path else "?")
    while True:
        status, body = call("GET", "%s%spage=%d" % (path, joiner, page))
        if status != 200 or not isinstance(body, dict):
            return
        for row in body.get("results", []):
            yield row
        if not body.get("next"):
            return
        page += 1


def upload(project, component, path, method="suggest", lang="zh_Hant"):
    """Upload a json-nested file. `suggest` never writes to the repo."""
    payload = open(path, "rb").read()
    boundary = uuid.uuid4().hex

    def part(name, value):
        return ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                % (boundary, name, value)).encode("utf-8")

    body = part("method", method)
    body += ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"upload.json\"\r\n"
             "Content-Type: application/json\r\n\r\n" % boundary).encode("utf-8")
    body += payload + b"\r\n" + ("--%s--\r\n" % boundary).encode("utf-8")
    return call("POST", "/api/translations/%s/%s/%s/file/" % (project, component, lang),
                data=body, headers={"Content-Type": "multipart/form-data; boundary=" + boundary})


def translation_path(project, component, lang="zh_Hant"):
    status, body = call("GET", "/api/translations/%s/%s/%s/" % (project, component, lang))
    return (status, body.get("filename") if status == 200 else body)


def main():
    ap = argparse.ArgumentParser(description="Weblate helper for translation-import")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status", help="repository + translation state for one component")
    p.add_argument("project"); p.add_argument("component")

    p = sub.add_parser("upload", help="upload a json-nested file (default: as suggestions)")
    p.add_argument("project"); p.add_argument("component"); p.add_argument("file")
    p.add_argument("--method", default="suggest",
                   choices=["suggest", "translate", "fuzzy", "approve", "replace", "add", "source"])

    p = sub.add_parser("repo", help="pull / commit / push the component repository")
    p.add_argument("project"); p.add_argument("component")
    p.add_argument("operation", choices=["pull", "commit", "push"])

    p = sub.add_parser("suggestions", help="list units that currently carry suggestions")
    p.add_argument("project"); p.add_argument("component")

    p = sub.add_parser("samples", help="已翻譯字串，當作句式範本")
    p.add_argument("project"); p.add_argument("component")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("glossary-add", help="add EN->zh entries to a glossary component")
    p.add_argument("project"); p.add_argument("component")
    p.add_argument("pairs", help="TSV file: english<TAB>chinese per line")

    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if args.cmd == "status":
        status, repo = call("GET", "/api/components/%s/%s/repository/" % (args.project, args.component))
        info = {k: repo.get(k) for k in ("needs_commit", "needs_push", "needs_merge", "merge_failure")} if status == 200 else repo
        print("repository:", json.dumps(info, ensure_ascii=False))
        status, comp = call("GET", "/api/components/%s/%s/" % (args.project, args.component))
        print("push url set:", bool(comp.get("push")) if status == 200 else comp)
        status, filename = translation_path(args.project, args.component)
        print("zh_Hant 檔案:", filename)
        if status == 200 and filename and not filename.startswith("compendium/zh-tw/"):
            print("⚠ 路徑不是 compendium/zh-tw/，譯文不會被 Babele 讀到。停止上傳，先修正路徑。")
        status, stats = call("GET", "/api/translations/%s/%s/zh_Hant/statistics/" % (args.project, args.component))
        if status == 200:
            print("統計:", json.dumps({k: stats.get(k) for k in ("total", "translated", "fuzzy", "suggestions")}, ensure_ascii=False))

    elif args.cmd == "upload":
        status, body = upload(args.project, args.component, args.file, args.method)
        print(status, json.dumps(body, ensure_ascii=False) if not isinstance(body, str) else body)

    elif args.cmd == "repo":
        status, body = form("POST", "/api/components/%s/%s/repository/" % (args.project, args.component),
                            {"operation": args.operation})
        print(status, body)

    elif args.cmd == "suggestions":
        query = urllib.parse.quote("has:suggestion")
        rows = list(paged("/api/translations/%s/%s/zh_Hant/units/?q=%s" % (args.project, args.component, query)))
        print("帶有建議的字串:", len(rows))
        for row in rows:
            print("  ", row["context"])

    elif args.cmd == "samples":
        # Weblate fills untranslated strings with the English source, so a unit only
        # counts as a real sample when its target differs from its source.
        query = urllib.parse.quote("state:>=translated")
        shown = 0
        for row in paged("/api/translations/%s/%s/zh_Hant/units/?q=%s" % (args.project, args.component, query)):
            source = (row.get("source") or [""])[0]
            target = (row.get("target") or [""])[0]
            if not target or target == source:
                continue
            print("--- %s" % row["context"])
            print("EN  %s" % source[:400])
            print("zh  %s" % target[:400])
            shown += 1
            if shown >= args.limit:
                break
        print("\n共 %d 則句式範本。使用者在 Weblate 上的編輯權威最高，對齊時照這些寫法。" % shown)

    elif args.cmd == "glossary-add":
        pairs = []
        for line in open(args.pairs, encoding="utf-8"):
            line = line.rstrip("\n")
            if not line or line.startswith("#") or "\t" not in line:
                continue
            english, chinese = line.split("\t", 1)
            pairs.append((english.strip(), chinese.strip()))
        # A glossary term must exist in the source language before it can be translated.
        added = []
        for english, chinese in pairs:
            status, body = form("POST", "/api/translations/%s/%s/en/units/" % (args.project, args.component),
                                {"key": english, "value": english})
            if status in (200, 201):
                added.append((english, chinese))
            else:
                print("來源字串新增失敗:", english, status, str(body)[:120])
        ids = {(row.get("source") or [""])[0]: row["id"]
               for row in paged("/api/translations/%s/%s/zh_Hant/units/?" % (args.project, args.component))}
        done = 0
        for english, chinese in added:
            unit = ids.get(english)
            if not unit:
                print("找不到對應單元:", english)
                continue
            status, body = form("PATCH", "/api/units/%d/" % unit, {"state": 20, "target": chinese})
            done += status == 200
        print("新增 %d 條，設定譯文 %d 條" % (len(added), done))


if __name__ == "__main__":
    main()
