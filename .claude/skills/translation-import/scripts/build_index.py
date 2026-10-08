# -*- coding: utf-8 -*-
"""Build the terminology index used when aligning a batch.

Three sources, in the priority the project settled on:
  1. Weblate glossaries (`terms`, `spells-glossary`) — deliberate decisions, fetched live
  2. entry names harvested from the current zh-tw files — covers spells/feats/items by name
  3. glossary.tsv — 簡體或非慣用譯名 -> English, so mainland wording can be traced back

Entry names win over spells-glossary when they disagree, because spells-glossary
came from an older edition. Disagreements are reported rather than silently resolved.

Weblate fills untranslated strings with the English source when it writes a file,
so any value equal to its key is treated as "not translated" and skipped.
"""
import argparse, collections, glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from weblate import paged

GLOSSARIES = [("dnd-5e-2024-zh-tw", "terms"), ("dnd-5e-2024-zh-tw", "spells-glossary")]


def glossary(project, component):
    out = {}
    for unit in paged("/api/translations/%s/%s/zh_Hant/units/?" % (project, component)):
        source = (unit.get("source") or [""])[0]
        target = (unit.get("target") or [""])[0]
        if source and target and target != source:
            out[source] = target
    return out


def entry_names(zh_root, skip_book=None):
    index = collections.defaultdict(lambda: collections.defaultdict(list))
    for path in glob.glob(os.path.join(zh_root, "*", "*.json")):
        book = os.path.basename(os.path.dirname(path))
        if book == skip_book:
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for key, entry in (data.get("entries") or {}).items():
            if isinstance(entry, dict):
                name = entry.get("name")
                if isinstance(name, str) and name.strip() and name != key:
                    index[key][name].append(book)
    return index


def aliases(path):
    """簡體/非慣用譯名 -> English, from glossary.tsv."""
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#") or "\t" not in line:
            continue
        variant, english = line.split("\t", 1)
        out[variant.strip()] = english.strip()
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Build term_index.json")
    ap.add_argument("--zh-root", default=os.path.join(here, "..", "..", "..", "..", "compendium", "zh-tw"))
    ap.add_argument("--glossary-tsv", default=os.path.join(here, "..", "glossary.tsv"))
    ap.add_argument("--skip-book", help="exclude this book (its names are the ones being imported)")
    ap.add_argument("--out", default="term_index.json")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    terms = glossary(*GLOSSARIES[0])
    spells = glossary(*GLOSSARIES[1])
    names = entry_names(os.path.abspath(args.zh_root), args.skip_book)
    alias = aliases(os.path.abspath(args.glossary_tsv))

    conflicts_internal = {k: dict(v) for k, v in names.items() if len(v) > 1}
    conflicts_sources = {k: {"entry": sorted(v), "spells_glossary": spells[k]}
                         for k, v in names.items() if k in spells and spells[k] not in v}

    json.dump({"terms": terms,
               "spells_glossary": spells,
               "entry_names": {k: dict(v) for k, v in names.items()},
               "aliases": alias,
               "conflicts_internal": conflicts_internal,
               "conflicts_sources": conflicts_sources},
              open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("terms %d | spells-glossary %d | 條目名稱 %d | 別名 %d -> %s"
          % (len(terms), len(spells), len(names), len(alias), args.out))
    if conflicts_internal:
        print("同一來源內部衝突（要問使用者）:", len(conflicts_internal))
        for key, variants in list(conflicts_internal.items())[:10]:
            print("   %-28s %s" % (key, variants))
    if conflicts_sources:
        print("2024 條目名稱 vs 舊版 spells-glossary（採用前者，列入報告）:", len(conflicts_sources))
        for key, info in list(conflicts_sources.items())[:10]:
            print("   %-28s %s ← 舊版 %s" % (key, info["entry"], info["spells_glossary"]))


if __name__ == "__main__":
    main()
