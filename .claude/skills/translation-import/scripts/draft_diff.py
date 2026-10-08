# -*- coding: utf-8 -*-
"""Measure how far a draft strays from its Chinese source (the s2twp-converted 原稿).

SKILL step 2 says the draft keeps the source's wording and changes only what the
allowed change classes permit. A draft that was written from scratch, or derived from
the finished mapping, passes the later "text is in the draft" check trivially. This
script compares each draft paragraph with the best-matching source paragraph(s) and
prints the similarity plus the exact replaced / inserted / deleted fragments, so the
preview's change list is produced from the data rather than from memory.

Draft paragraphs that match no source sentence run (ratio below --floor) are labelled
`無原稿`: they are supplements; entries that are supplements as a whole are named in
--supplements, any other `無原稿` fails the run. Paragraphs below --threshold are
`改動大`: informational, every listed fragment still needs a reason in the preview.
Matching runs over sentence runs, so merged, split and reordered paragraphs are found.

Source file: the converted 原稿 txt; a heading is a line that ends with an English name
(`中文 English Name` or `中文|English Name`). Draft: `### English Name` sections whose
`+1/+2/+3` suffix is ignored when finding the source section. Lines from `〔EN 補翻`
onward in a draft section are field supplements and are skipped.

Usage:
  python draft_diff.py --source src.s2twp.txt --draft batch.draft.txt [--threshold 0.85]
        [--floor 0.45] [--out diff-report.md]
Exit code 1 when a paragraph is 無原稿 outside --supplements (use --report-only to always exit 0).
"""
import argparse, difflib, re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HEAD = re.compile(r"^\s*[^\x00-\x7f]+[^\x00-\x7f\s|｜]*\s*[|｜ ]\s*([A-Za-z][A-Za-z0-9'’,./ -]*?)\s*$")


def norm_name(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower().replace("’", "'"))


def source_sections(path):
    sections, cur = {}, None
    with open(path, encoding="utf-8-sig") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            m = HEAD.match(line)
            if m and not re.search(r"[，。、；：]", line):
                cur = norm_name(m.group(1))
                sections[cur] = []
            elif cur is not None and line.strip():
                sections[cur].append(line.strip())
    return sections


def draft_sections(path):
    out, name, skip = {}, None, False
    with open(path, encoding="utf-8-sig") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            m = re.match(r"\s*###\s+(.+?)\s*$", line)
            if m:
                name, skip = m.group(1), False
                out[name] = []
            elif name is not None and line.strip():
                if line.startswith("〔EN 補翻"):
                    skip = True
                if not skip and not line.startswith("名稱："):
                    out[name].append(line.strip())
    return out


def sentences(src_lines):
    """Flatten source paragraphs into (paragraph_no, sentence) pairs, keeping the closing 。"""
    out = []
    for n, line in enumerate(src_lines, 1):
        for part in re.findall(r"[^。！？]+[。！？]?", line):
            if part.strip():
                out.append((n, part.strip()))
    return out


def candidates(src_lines):
    """Every run of 1–6 consecutive sentences, so merged, split and reordered paragraphs all find their source."""
    sent = sentences(src_lines)
    for i in range(len(sent)):
        for span in range(1, 7):
            if i + span <= len(sent):
                yield sent[i][0], sent[i + span - 1][0], "".join(t for _, t in sent[i:i + span])


def best_match(par, src_lines):
    best = (0.0, None, None, "")
    for a, b, text in candidates(src_lines):
        r = difflib.SequenceMatcher(None, text, par, autojunk=False).ratio()
        if r > best[0]:
            best = (r, a, b, text)
    return best


def fragments(src, par):
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, src, par, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        out.append("「%s」→「%s」" % (src[i1:i2], par[j1:j2]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--draft", required=True)
    ap.add_argument("--threshold", type=float, default=0.85)
    ap.add_argument("--floor", type=float, default=0.45)
    ap.add_argument("--out")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--supplements", default="", help="逗號分隔：整條沒有原稿、本來就是補翻的條目（不算失敗）")
    args = ap.parse_args()
    src, drafts = source_sections(args.source), draft_sections(args.draft)
    supplements = {k.strip() for k in args.supplements.split(",") if k.strip()}
    rows, flagged = [], 0
    for key, pars in drafts.items():
        base = norm_name(re.sub(r"\s\+\d$", "", key))
        if base not in src:
            rows.append((key, "-", "-", "無原稿", "來源檔找不到此標題", ""))
            flagged += key not in supplements
            continue
        for i, par in enumerate(pars, 1):
            ratio, a, b, text = best_match(par, src[base])
            if ratio < args.floor:
                status = "無原稿"
            elif ratio < args.threshold:
                status = "改動大"
            elif text == par:
                status = "原句"
            else:
                status = "微調"
            flagged += status == "無原稿" and key not in supplements
            where = ("來源第 %d 段" % a if a == b else "來源第 %d–%d 段" % (a, b)) if a is not None else "-"
            rows.append((key, "p%d" % i, "%.2f" % ratio, status, where, "；".join(fragments(text, par))[:600]))
    lines = ["| 條目 | 底稿段 | 相似度 | 判定 | 對應 | 與原稿差異（原→底稿） |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |")
    big = sum(1 for r in rows if r[3] == "改動大")
    lines.append("\n共 %d 段；改動大 %d 段（逐項寫理由）；無原稿且未列為補翻 %d 段（失敗）。" % (len(rows), big, flagged))
    text = "\n".join(lines)
    print(text)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text + "\n")
    return 0 if (args.report_only or not flagged) else 1


if __name__ == "__main__":
    sys.exit(main())
