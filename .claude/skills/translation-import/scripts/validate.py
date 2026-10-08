# -*- coding: utf-8 -*-
"""Mechanically check aligned zh-tw content against the EN template, then emit the upload file.

The EN block structure and protected technical content survive. Complete inline
phrases may change order within each block to follow the Chinese draft. This is a
mechanical check, not proof of rule semantics, terminology or natural Chinese.

Input (produced by the model during alignment):

{"entries": {
   "Arcane Artist": {
     "name": "奧法藝術家",
     "paragraphs": ["<p> 內容，不含 <p> 標籤本身", "..."],   # or "description": "<p>…</p>…"
     "activities": {"Inspiring Magic": {"name": "…", "condition": "…"}},
     "effects": {...}, "advancement": {...}
   }}}

Usage:
  python validate.py aligned.json --book dnd-arcana-unleashed --component feats --out upload.json
"""
import argparse, glob, json, os, re, sys
from html_blocks import Plan, compare_html, visible_text

REF = re.compile(r"&(?:amp;)?Reference\[([^\]]+)\](?:\{([^}]*)\})?")
UUID = re.compile(r"@UUID\[([^\]]+)\](?:\{([^}]*)\})?")
ASCII_WORD = re.compile(r"[A-Za-z]{3,}")
CJK_CHAR = re.compile(r"[一-鿿]")
TRANSLATABLE = ("activities", "effects", "advancement")

# Product and system names that stay in English on purpose. Without this the
# "英文殘留" check fires on every Foundry Note, which would block whole batches
# for text that is correctly translated. Extend with --allow when a batch needs it.
ALLOWED_ENGLISH = {"Foundry", "Babele", "Weblate", "GitHub", "Roll20"}


def description_of(entry):
    if "paragraphs" in entry:
        return "".join("<p>%s</p>" % p for p in entry["paragraphs"])
    return entry.get("description", "")


def check_description(en_html, zh_html, allowed=ALLOWED_ENGLISH):
    problems = compare_html(en_html, zh_html)
    if problems:
        return problems
    # All complete text blocks, including classed paragraphs and table cells.
    for block in Plan(zh_html).blocks:
        content = visible_text(block.html)
        if "它" in content:
            problems.append(block.id + " 出現「它」：改用適合的「其」或重複名詞")
        no_label = [r[0] for r in REF.findall(block.html) if not (r[1] and CJK_CHAR.search(r[1]))]
        if no_label:
            problems.append("%s &Reference 缺少中文 {標籤}：%s" % (block.id, no_label))
        missing_uuid_labels = [target for target, label in UUID.findall(block.html) if not label.strip()]
        if missing_uuid_labels:
            problems.append("%s @UUID 缺少可見 {標籤}：%s" % (block.id, missing_uuid_labels))
        leftover = [w for w in ASCII_WORD.findall(content) if w not in allowed]
        if leftover:
            problems.append("%s 疑似英文殘留：%s" % (block.id, leftover))
    return problems


def check_results(entry, en_entry, allowed):
    """RollTable rows: same range keys as EN, each row checked like a description block."""
    zh_rows, en_rows = entry.get("results"), en_entry.get("results")
    if zh_rows is None and en_rows is None:
        return []
    if not isinstance(zh_rows, dict) or not isinstance(en_rows, dict) or list(zh_rows) != list(en_rows):
        return ["results 區間鍵與 EN 不同或缺漏"]
    problems = []
    for rng, en_text in en_rows.items():
        problems += ["results[%s] %s" % (rng, p) for p in check_description(en_text, zh_rows[rng], allowed)]
    return problems


def check_subfields(entry, en_entry):
    problems = []
    for field in TRANSLATABLE:
        if field not in entry:
            continue
        en_field = en_entry.get(field) or {}
        for key, value in entry[field].items():
            if key not in en_field:
                problems.append("%s.%s 不在 EN 模板裡" % (field, key))
                continue
            for sub in (value if isinstance(value, dict) else {}):
                if sub not in en_field[key] and sub != "changes":
                    problems.append("%s.%s.%s 不在 EN 模板裡" % (field, key, sub))
    return problems


def count_strings(node):
    if isinstance(node, str):
        return 1
    if isinstance(node, dict):
        return sum(count_strings(v) for v in node.values())
    return 0


def main():
    ap = argparse.ArgumentParser(description="Validate aligned content and build the upload payload")
    ap.add_argument("aligned")
    ap.add_argument("--book", required=True)
    ap.add_argument("--component", required=True)
    ap.add_argument("--repo", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
    ap.add_argument("--out", default="upload.json")
    ap.add_argument("--allow", default="", help="逗號分隔，額外允許保留英文的專有名詞")
    args = ap.parse_args()
    allowed = ALLOWED_ENGLISH | {w.strip() for w in args.allow.split(",") if w.strip()}
    sys.stdout.reconfigure(encoding="utf-8")

    en_path = os.path.join(os.path.abspath(args.repo), "compendium", "en", args.book,
                           "%s.%s.json" % (args.book, args.component))
    if not os.path.exists(en_path):
        # Folder name and file prefix can differ (dnd-heros-faerun/dnd-heroes-faerun.*.json).
        matches = glob.glob(os.path.join(os.path.dirname(en_path), "*.%s.json" % args.component))
        if len(matches) == 1:
            en_path = matches[0]
    if not os.path.exists(en_path):
        sys.exit("找不到 EN 模板：%s" % en_path)
    # utf-8-sig: PowerShell's Set-Content writes a BOM, and json.load chokes on it.
    en_entries = json.load(open(en_path, encoding="utf-8-sig"))["entries"]
    aligned = json.load(open(args.aligned, encoding="utf-8-sig"))["entries"]

    payload, blocked, total = {}, 0, 0
    for key, entry in aligned.items():
        if key not in en_entries:
            print("⛔ %-26s EN 模板沒有這個條目 — 屬於上游缺漏，放進 remaining" % key)
            blocked += 1
            continue
        zh_html = description_of(entry)
        problems = check_description(en_entries[key].get("description", ""), zh_html, allowed)
        problems += check_subfields(entry, en_entries[key])
        problems += check_results(entry, en_entries[key], allowed)
        out = {k: v for k, v in entry.items() if k in ("name", "results") + TRANSLATABLE}
        if zh_html:
            out["description"] = zh_html
        if problems:
            blocked += 1
            print("🟡 %-26s %s" % (key, problems[0]))
            for extra in problems[1:]:
                print("%30s %s" % ("", extra))
            continue
        payload[key] = out
        strings = count_strings(out)
        total += strings
        print("✅ %-26s %-10s %d 個字串" % (key, entry.get("name", ""), strings))

    print("\n通過 %d 條（%d 個字串），未通過 %d 條" % (len(payload), total, blocked))
    if payload and not blocked:
        json.dump({"entries": payload}, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("已寫出", args.out)
    if blocked:
        print("本次不寫出 upload.json。修正後重跑，或另建只含確定條目的批次；不要使用舊 payload。")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
