# -*- coding: utf-8 -*-
"""Count how often candidate wordings appear in the existing zh-tw translations.

This is the project's tie-breaker. When a term or phrasing has competing options
(施展 vs 施放, 執行動作 vs 採取動作, 增益 vs 好處), counting real usage in the
files that are already published settles it with evidence instead of taste —
and the example lines let the user judge whether the hits mean what they look like.

Usage:
  python usage.py 施展 施放
  python usage.py --examples 2 增益 好處
"""
import argparse, glob, os, re, sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Count competing wordings in existing zh-tw files")
    ap.add_argument("terms", nargs="+")
    ap.add_argument("--zh-root", default=os.path.join(here, "..", "..", "..", "..", "compendium", "zh-tw"))
    ap.add_argument("--examples", type=int, default=2, help="example snippets to print per term")
    ap.add_argument("--width", type=int, default=18, help="context characters around each hit")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    blobs = []
    for path in glob.glob(os.path.join(os.path.abspath(args.zh_root), "*", "*.json")):
        try:
            blobs.append((os.path.basename(os.path.dirname(path)), open(path, encoding="utf-8").read()))
        except OSError:
            continue

    for term in args.terms:
        pattern = re.compile(r".{0,%d}%s.{0,%d}" % (args.width, re.escape(term), args.width))
        hits, samples = 0, []
        for book, blob in blobs:
            found = pattern.findall(blob)
            hits += len(found)
            for snippet in found[:args.examples]:
                if len(samples) < args.examples:
                    samples.append("%s: …%s…" % (book, snippet.replace("\n", " ")))
        print("%-14s %4d 次" % (term, hits))
        for sample in samples:
            print("      %s" % sample)


if __name__ == "__main__":
    main()
