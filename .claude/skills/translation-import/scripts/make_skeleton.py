# -*- coding: utf-8 -*-
"""Create zh-tw skeleton files for a book that Weblate has not seen yet.

Why this has to happen before Weblate ever touches the book: the components use the
filemask `compendium/*/<book>/<book>.<component>.json` with an empty
`language_code_style`. If no file matches under `compendium/zh-tw/<book>/`, Weblate
invents its own path from the default language code and writes
`compendium/zh_Hant/<book>/…` instead — which `register.js` never reads, so the whole
book silently fails to translate in Foundry.

The skeleton also carries `mapping`, which cannot be uploaded through the API because
Babele's converter config is not a translatable string in the EN template.

`mapping` follows the rule established in commit 548695e: include only the converters
whose field actually exists on the entries, with rangeActivities travelling alongside
activities. label/folders are filled from existing translations where an exact match
exists; anything unmatched is left out so it shows up as untranslated in Weblate
rather than as a guess.

Usage:
  python make_skeleton.py dnd-arcana-unleashed
"""
import argparse, collections, glob, json, os, sys

CONVERTERS = [
    ("activities", "activities", {"path": "system.activities", "converter": "activities"}),
    ("rangeActivities", "activities", {"path": "system.activities", "converter": "rangeActivities"}),
    ("effects", "effects", {"path": "effects", "converter": "effects"}),
    ("advancement", "advancement", {"path": "system.advancement", "converter": "advancement"}),
]


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def lookups(root, skip_book):
    """EN label / folder name -> most common existing zh translation."""
    labels = collections.defaultdict(collections.Counter)
    folders = collections.defaultdict(collections.Counter)
    for zh_path in glob.glob(os.path.join(root, "zh-tw", "*", "*.json")):
        book = os.path.basename(os.path.dirname(zh_path))
        if book == skip_book:
            continue
        en_path = os.path.join(root, "en", book, os.path.basename(zh_path))
        if not os.path.exists(en_path):
            continue
        try:
            zh, en = load(zh_path), load(en_path)
        except ValueError:
            continue
        if isinstance(zh.get("label"), str) and isinstance(en.get("label"), str) and zh["label"] != en["label"]:
            labels[en["label"]][zh["label"]] += 1
        for name, value in (zh.get("folders") or {}).items():
            if isinstance(value, str) and value != name:
                folders[name][value] += 1
    return labels, folders


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Generate zh-tw skeleton files for a book")
    ap.add_argument("book")
    ap.add_argument("--repo", default=os.path.join(here, "..", "..", "..", ".."))
    ap.add_argument("--known", help="JSON file: {component: {label: str, folders: {en: zh}}} for translations "
                                    "you already have (e.g. recovered from Weblate)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    root = os.path.join(os.path.abspath(args.repo), "compendium")
    known = load(os.path.abspath(args.known)) if args.known else {}
    label_lut, folder_lut = lookups(root, args.book)
    out_dir = os.path.join(root, "zh-tw", args.book)
    os.makedirs(out_dir, exist_ok=True)

    en_files = sorted(glob.glob(os.path.join(root, "en", args.book, "*.json")))
    if not en_files:
        sys.exit("找不到 EN 模板目錄：compendium/en/%s/" % args.book)

    for en_path in en_files:
        fname = os.path.basename(en_path)
        component = fname.rsplit(".", 2)[-2]
        en = load(en_path)
        hints = known.get(component, {})

        fields = set()
        for entry in (en.get("entries") or {}).values():
            if isinstance(entry, dict):
                fields.update(entry.keys())
        mapping = {name: value for name, need, value in CONVERTERS if need in fields}

        label = hints.get("label") or (label_lut[en["label"]].most_common(1)[0][0]
                                       if label_lut.get(en.get("label")) else None)
        folders, missing = {}, []
        for name in (en.get("folders") or {}):
            zh = hints.get("folders", {}).get(name) or (folder_lut[name].most_common(1)[0][0]
                                                        if folder_lut.get(name) else None)
            if zh:
                folders[name] = zh
            else:
                missing.append(name)

        doc = {}
        if label:
            doc["label"] = label
        if folders:
            doc["folders"] = folders
        doc["entries"] = {}
        if mapping:
            doc["mapping"] = mapping

        with open(os.path.join(out_dir, fname), "w", encoding="utf-8", newline="\n") as handle:
            json.dump(doc, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        print("%-14s label %-10s folders %d 已譯 / %d 待譯  mapping %s"
              % (component, label or "(待譯)", len(folders), len(missing), sorted(mapping) or "無"))
        for name in missing:
            print("%18s 待譯 folder: %s" % ("", name))

    print("\n寫入 compendium/zh-tw/%s/。請自行檢查 diff 後 commit 並 push，"
          "推上去之後再讓 Weblate pull 並重新掃描。" % args.book)


if __name__ == "__main__":
    main()
