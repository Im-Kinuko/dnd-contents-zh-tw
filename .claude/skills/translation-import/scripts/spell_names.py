# -*- coding: utf-8 -*-
"""Fetch the CURRENT Chinese spell names from Weblate (not the repo, which lags behind).

`build_index.py` reads entry names from compendium/zh-tw files, and its own docstring
warns they are not the live Weblate names. Spell lists inside magic items (spellbooks,
staffs, wands) must use the live names, so this script reads them from the API.

Output JSON: {"Fireball": "火球術", ...}. When the PHB project and dnd5e disagree the PHB
project wins and the conflict is printed.

Usage:
  python spell_names.py --out spell-names.json
  python spell_names.py --components dnd-players-handbook/dnd-players-handbook-spells dnd5e/dnd5e-spells24
Environment: WEBLATE_URL / WEBLATE_API_TOKEN (same as weblate.py).
"""
import argparse, json, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weblate as w

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT = ["dnd-players-handbook/dnd-players-handbook-spells", "dnd5e/dnd5e-spells24"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--components", nargs="*", default=DEFAULT, help="project/component，先出現的優先")
    ap.add_argument("--out", default="spell-names.json")
    args = ap.parse_args()
    names, conflicts = {}, []
    for spec in args.components:
        project, component = spec.split("/", 1)
        loaded = 0
        for unit in w.paged("/api/translations/%s/%s/zh_Hant/units/" % (project, component)):
            ctx = unit["context"]
            if not (ctx.startswith("entries.") and ctx.endswith(".name") and ctx.count(".") == 2):
                continue
            en, zh = ctx.split(".")[1], unit["target"][0]
            if not zh or zh == en:
                continue
            loaded += 1
            if en in names and names[en] != zh:
                conflicts.append((en, names[en], zh, spec))
            names.setdefault(en, zh)
        print("%s：%d 個法術名稱" % (spec, loaded))
        if loaded == 0:
            sys.exit("讀取 %s 失敗或沒有名稱；paged() 失敗時會靜默停止，先修好再繼續（不可當作「查無」）" % spec)
    for en, kept, other, spec in conflicts:
        print("⚠ %s：採用 %s，%s 為 %s" % (en, kept, spec, other))
    json.dump(names, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("共 %d 筆 -> %s" % (len(names), args.out))


if __name__ == "__main__":
    main()
