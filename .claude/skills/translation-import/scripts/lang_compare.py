# -*- coding: utf-8 -*-
"""Compare a batch's visible EN text against lang/en.json -> lang/zh-tw.json.

Terms and glossary are not enough: the game UI strings in lang/zh-tw.json are a
third source. Run this after the draft exists; it lists every lang entry whose
English value occurs in the batch and whether the lang Chinese shows up in the
draft. Differences are not errors, they are the "說明" the preview must carry:
adopt the lang word, or record why the user's ruling / terms / existing text wins.

Usage:
  python lang_compare.py sheet.json [--draft batch.draft.txt] [--min-len 4]
"""
import argparse, json, os, re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load(path):
    with open(path, encoding="utf-8-sig") as handle:
        return json.load(handle)


def flat(node, prefix=""):
    out = {}
    for key, value in node.items():
        if isinstance(value, dict):
            out.update(flat(value, prefix + key + "."))
        else:
            out[prefix + key] = value
    return out


def visible_text(sheet):
    parts = []
    for entry in sheet["entries"].values():
        for block in entry.get("blocks", []):
            parts.append(block["en"])
        for field in ("activities", "effects", "advancement"):
            for key, value in (entry.get(field) or {}).items():
                parts.append(key)
                if isinstance(value, dict):
                    parts.extend(v for v in value.values() if isinstance(v, str))
    text = " ".join(parts)
    text = re.sub(r"@UUID\[[^\]]*\]|\[\[[^\]]*\]\]|<[^>]+>", " ", text)
    return text.lower()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sheet")
    ap.add_argument("--draft")
    ap.add_argument("--repo", default=os.path.join(here, "..", "..", "..", ".."))
    ap.add_argument("--min-len", type=int, default=4)
    args = ap.parse_args()
    lang_dir = os.path.join(os.path.abspath(args.repo), "lang")
    en, zh = flat(load(os.path.join(lang_dir, "en.json"))), flat(load(os.path.join(lang_dir, "zh-tw.json")))
    text = visible_text(load(args.sheet))
    draft = ""
    if args.draft:
        with open(args.draft, encoding="utf-8-sig") as handle:
            draft = re.sub(r"\s+", "", handle.read())
    hits = {}
    for key, value in en.items():
        if not isinstance(value, str) or not args.min_len <= len(value) <= 40:
            continue
        needle = value.lower().strip()
        if re.search(r"(?<![a-z])" + re.escape(needle) + r"(?![a-z])", text) and zh.get(key):
            hits.setdefault(needle, []).append((key, zh[key]))
    print("| EN | lang/zh-tw | 底稿 | lang key |")
    print("|---|---|---|---|")
    for needle, items in sorted(hits.items()):
        zhs = sorted({z for _, z in items})
        if draft:
            mark = "有" if any(re.sub(r"\s+", "", z) in draft for z in zhs) else "無"
        else:
            mark = "-"
        print("| %s | %s | %s | %s |" % (needle, " ／ ".join(zhs)[:60], mark, items[0][0]))
    if draft:
        print("\n「無」不一定是錯：確認是不同語境、或使用者裁定／terms／既有譯文優先，並在預覽寫出說明。")


if __name__ == "__main__":
    main()
