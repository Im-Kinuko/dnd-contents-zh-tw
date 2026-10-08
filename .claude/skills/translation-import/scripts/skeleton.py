# -*- coding: utf-8 -*-
"""Map complete Chinese draft blocks to EN structure without fixing inline order.

extract emits schema_version=2 with stable block IDs, not English text keys.
Fill block.zh with a complete HTML fragment in the draft's Chinese order.
build verifies provenance and structure before writing. Legacy run sheets must
be extracted again because they do not express complete sentences.
"""
import argparse
import glob
import json
import os
import re
import sys

from html_blocks import Plan, compare_html, visible_text

FIELDS = ("activities", "effects", "advancement")


def load(path):
    with open(path, encoding="utf-8-sig") as handle:
        return json.load(handle)


def write(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=1)


def en_path(repo, book, component):
    folder = os.path.join(os.path.abspath(repo), "compendium", "en", book)
    path = os.path.join(folder, "%s.%s.json" % (book, component))
    if not os.path.exists(path):
        matches = glob.glob(os.path.join(folder, "*.%s.json" % component))
        if len(matches) == 1:
            return matches[0]
    return path


def norm(text):
    return re.sub(r"\s+", "", text)


def draft_sections(path):
    sections, name = {}, None
    with open(path, encoding="utf-8-sig") as handle:
        for line in handle:
            match = re.match(r"\s*###\s+(.+?)\s*$", line)
            if match:
                name = match.group(1)
                if name in sections:
                    raise ValueError("底稿條目標題重複：" + name)
                sections[name] = ""
            elif name:
                sections[name] += line
    return {key: norm(value) for key, value in sections.items()}


def cmd_extract(args):
    entries = load(en_path(args.repo, args.book, args.component))["entries"]
    keys = args.keys or list(entries)
    sheet = {"schema_version": 2, "book": args.book, "component": args.component, "entries": {}}
    for key in keys:
        if key not in entries:
            raise ValueError("EN 模板沒有此條目：" + key)
        entry = entries[key]
        row = {"name_en": entry.get("name", key), "name": "", "blocks": []}
        for block in Plan(entry.get("description", "")).blocks:
            row["blocks"].append({"id": block.id, "en": block.html, "zh": "",
                                  "source": "draft", "basis": ""})
        if "results" in entry:
            row["rows"] = [{"id": "r:" + rng, "en": unwrap(text)[0], "zh": "", "source": "draft", "basis": ""}
                           for rng, text in entry["results"].items()]
        for field in FIELDS:
            if field in entry:
                row[field] = json.loads(json.dumps(entry[field]))
        sheet["entries"][key] = row
    write(args.out, sheet)
    total = sum(len(row["blocks"]) + len(row.get("rows", [])) for row in sheet["entries"].values())
    print("%d 條、%d 個完整文字區塊 -> %s" % (len(keys), total, args.out))
    print("以底稿完整句段填入 block.zh；句內標記可隨中文語順移動。")


def check_block(location, en_html, translated, text):
    """Validate one filled block against its EN and the draft; return the zh fragment."""
    if translated.get("en") != en_html:
        raise ValueError(location + " EN 已變動，請重新 extract")
    zh = translated.get("zh")
    if not isinstance(zh, str) or not zh.strip():
        raise ValueError(location + " 未填寫完整中文；不自動補回英文")
    translated_plan = Plan(zh)
    if len(translated_plan.blocks) != 1 or translated_plan.structure() != ("BLOCK",):
        raise ValueError(location + " 只能填句內 HTML，不包含段落或區塊標籤")
    errors = compare_html(en_html, zh)
    if errors:
        raise ValueError(location + "：" + "；".join(errors))
    chinese = norm(visible_text(zh))
    if norm(visible_text(en_html)) and not chinese:
        raise ValueError(location + " 遺失可見文字或連結標籤")
    source = translated.get("source")
    if source == "draft":
        if chinese and chinese not in text:
            raise ValueError(location + " 完整中文不在底稿中；先修訂底稿，再映射")
    elif source == "supplement":
        if not isinstance(translated.get("basis"), str) or not translated["basis"].strip():
            raise ValueError(location + " 補翻須列明原稿缺漏與用詞依據")
        print("待確認補翻 %s：%s" % (location, visible_text(zh)))
    else:
        raise ValueError(location + " source 只能是 draft 或 supplement")
    return zh


def unwrap(text):
    """A row that is one whole <p>…</p> is filled as inline HTML and wrapped again on build."""
    match = re.fullmatch(r"<p>((?:(?!<p>).)*)</p>", text, re.S)
    return (match.group(1), True) if match else (text, False)


def build_results(key, en_results, rows, text):
    if [row.get("id") for row in rows] != ["r:" + rng for rng in en_results]:
        raise ValueError(key + " 表格列 ID／順序不同，請重新 extract")
    out = {}
    for rng, row in zip(en_results, rows):
        inner, wrapped = unwrap(en_results[rng])
        zh = check_block(key + "/r:" + rng, inner, row, text)
        out[rng] = "<p>%s</p>" % zh if wrapped else zh
    return out


def build_entries(sheet, entries, draft):
    if sheet.get("schema_version") != 2:
        raise ValueError("舊版 run sheet 不適用整段映射；請重新 extract，保留原稿與底稿")
    out = {}
    for key, row in sheet["entries"].items():
        if key not in entries:
            raise ValueError("EN 模板沒有此條目：" + key)
        if not isinstance(row.get("name"), str) or not row["name"].strip():
            raise ValueError(key + " 尚未填寫中文名稱")
        text = draft.get(key) or draft.get(row.get("name_en", ""))
        if not text:
            raise ValueError("底稿缺少 ### " + key + " 或條目內容")
        original = entries[key].get("description", "")
        plan = Plan(original)
        rows = row.get("blocks", [])
        if [block.id for block in plan.blocks] != [block.get("id") for block in rows]:
            raise ValueError(key + " 區塊 ID／順序不同，請重新 extract")
        replacements = {}
        for block, translated in zip(plan.blocks, rows):
            replacements[block.id] = check_block(key + "/" + block.id, block.html, translated, text)
        result = {"name": row["name"]}
        if original:
            result["description"] = plan.build(replacements)
        if "results" in entries[key]:
            result["results"] = build_results(key, entries[key]["results"], row.get("rows", []), text)
        for field in FIELDS:
            if field in row:
                result[field] = row[field]
        out[key] = result
    return {"entries": out}


def cmd_build(args):
    if not args.draft or not os.path.isfile(args.draft):
        raise ValueError("build 需要存在的 --draft <批次>.draft.txt")
    sheet = load(args.sheet)
    entries = load(en_path(args.repo, sheet["book"], sheet["component"]))["entries"]
    result = build_entries(sheet, entries, draft_sections(args.draft))
    write(args.out, result)
    print("%d 條 -> %s；仍須規則核對、術語核對與中文通讀" % (len(result["entries"]), args.out))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="以自然中文底稿整段映射 EN 區塊骨架")
    ap.add_argument("--repo", default=os.path.join(here, "..", "..", "..", ".."))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("extract")
    p.add_argument("--book", required=True)
    p.add_argument("--component", required=True)
    p.add_argument("--keys", nargs="*")
    p.add_argument("--out", default="sheet.json")
    p.set_defaults(func=cmd_extract)
    p = sub.add_parser("build")
    p.add_argument("sheet")
    p.add_argument("--draft", required=True)
    p.add_argument("--out", default="aligned.json")
    p.set_defaults(func=cmd_build)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        args.func(args)
    except (ValueError, OSError, KeyError) as exc:
        ap.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
