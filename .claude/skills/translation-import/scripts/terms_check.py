# -*- coding: utf-8 -*-
"""Mechanical cross-check: Weblate `terms` (and current spell names) vs. a batch's draft.

Why this exists: SKILL step 2 asks for every term in the batch's visible EN text to be
checked against Weblate `terms`. Done by memory it drops ordinary words (take→承受,
immediately after→緊接在…後) and inflected forms (takes/taking). This script does the
lookup instead and prints one table that goes into the preview unchanged.

For every `terms` key found in the batch's EN text (all blocks plus activities / effects /
advancement strings) it checks that the term's Chinese appears in the same entry's draft
section. For spell names (optional) it checks link labels and multi-word names.

Status
  ✅   the Chinese term is in the draft section (counts are compared: EN n hits vs ZH m)
  ❌   missing or fewer occurrences than EN hits: fix the draft, or acknowledge with --ack
  ✅📝 missing but acknowledged in the --ack file (the reason is printed into the table)
  ℹ️   capitalised single-word keys (Hide, Magic, Attack…) at sentence start: could be
       ordinary prose; reviewed by eye, never blocking

Exit code 0 only when no ❌ remains.

Usage
  python terms_check.py sheet.json --draft batch.draft.txt --index batch.term_index.json
        [--names spell-names.json] [--ack ack.json] [--out terms-report.md]

ack.json: {"<Entry key>|<EN term>": "reason", "<EN term>": "reason for every entry"}
"""
import argparse, json, re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IRREGULAR = {
    "take": ["take", "takes", "took", "taken", "taking"],
    "make": ["make", "makes", "made", "making"],
    "have": ["have", "has", "had", "having"],
    "hit": ["hit", "hits", "hitting"],
    "roll": ["roll", "rolls", "rolled", "rolling"],
    "become": ["become", "becomes", "became", "becoming"],
    "choose": ["choose", "chooses", "chose", "chosen", "choosing"],
    "deal": ["deal", "deals", "dealt", "dealing"],
    "gain": ["gain", "gains", "gained", "gaining"],
    "lose": ["lose", "loses", "lost", "losing"],
    "spend": ["spend", "spends", "spent", "spending"],
    "regain": ["regain", "regains", "regained", "regaining"],
}


def word_forms(word):
    """Inflected surface forms of one lowercase English word."""
    w = word.lower()
    if w in IRREGULAR:
        return IRREGULAR[w]
    forms = {w, w + "s", w + "es", w + "ed", w + "ing"}
    if w.endswith("e"):
        forms |= {w + "d", w[:-1] + "ing"}
    if w.endswith("y") and len(w) > 2:
        forms |= {w[:-1] + "ies", w[:-1] + "ied"}
    if re.search(r"[^aeiou][aeiou][^aeiouwxy]$", w):
        forms |= {w + w[-1] + "ed", w + w[-1] + "ing"}
    return sorted(forms, key=len, reverse=True)


def key_regex(key):
    """Regex for a terms key; the last word may be inflected, case-insensitive for lower-case keys."""
    tokens = re.findall(r"[A-Za-z0-9'’/-]+|[^A-Za-z0-9'’/\s-]+", key.strip().strip("﻿"))
    words = [t for t in tokens if re.match(r"[A-Za-z]", t)]
    if not words:
        return None
    parts = []
    for i, token in enumerate(tokens):
        if re.match(r"[A-Za-z]", token) and token is words[-1]:
            forms = [f.capitalize() if token[0].isupper() else f for f in word_forms(token)]
            parts.append("(?:%s)" % "|".join(re.escape(f) for f in forms))
        else:
            parts.append(re.escape(token))
    body = r"\s*".join(parts) if len(tokens) > 1 else parts[0]
    body = body.replace("’", "['’]").replace("'", "['’]") if "'" in key or "’" in key else body
    return r"(?<![A-Za-z])" + body + r"(?![A-Za-z])"


def entry_texts(sheet):
    """EN visible text per entry: block HTML plus every string in activities/effects/advancement."""
    out = {}
    for key, entry in sheet["entries"].items():
        parts = [b["en"] for b in entry.get("blocks", [])]
        for row in entry.get("rows", []):
            parts.append(row["en"])

        def walk(node):
            if isinstance(node, str):
                parts.append(node)
            elif isinstance(node, dict):
                for k, v in node.items():
                    parts.append(k)
                    walk(v)
        for field in ("activities", "effects", "advancement"):
            walk(entry.get(field) or {})
        raw = " ".join(parts)
        labels = re.findall(r"@UUID\[[^\]]*\]\{([^}]*)\}", raw)
        plain = re.sub(r"@UUID\[[^\]]*\]\{([^}]*)\}", r"\1", raw)
        plain = re.sub(r"@UUID\[[^\]]*\]", " ", plain)
        plain = re.sub(r"\[\[[^\]]*\]\]\{([^}]*)\}", r"\1", plain)
        plain = re.sub(r"\[\[[^\]]*\]\]|@Embed\[[^\]]*\]|<[^>]+>|&amp;Reference\[[^\]]*\]", " ", plain)
        out[key] = {"plain": plain, "labels": labels, "raw": raw}
    return out


def draft_sections(path):
    sections, name = {}, None
    with open(path, encoding="utf-8-sig") as handle:
        for line in handle:
            m = re.match(r"\s*###\s+(.+?)\s*$", line)
            if m:
                name = m.group(1)
                sections[name] = ""
            elif name:
                sections[name] += line
    return {k: re.sub(r"\s+", "", v) for k, v in sections.items()}


def zh_count(section, value):
    """Occurrences of a Chinese term in a draft section; `…` splits a term into ordered parts."""
    value = re.sub(r"\s+", "", value)
    parts = [p for p in value.split("…") if p]
    if not parts:
        return 0
    if len(parts) == 1:
        return section.count(parts[0])
    count, pos = 0, 0
    while True:
        cursor, ok = pos, True
        for p in parts:
            at = section.find(p, cursor)
            if at < 0:
                ok = False
                break
            cursor = at + len(p)
        if not ok:
            return count
        count += 1
        pos = cursor


def snippet(text, start, end):
    left, right = max(0, start - 28), min(len(text), end + 28)
    return re.sub(r"\s+", " ", text[left:right]).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sheet")
    ap.add_argument("--draft", required=True)
    ap.add_argument("--index", required=True, help="build_index.py 產生的 term_index.json")
    ap.add_argument("--names", help="spell_names.py 產生的法術現行名稱 JSON")
    ap.add_argument("--ack", help="登記理由的 JSON；沒登記的 ❌ 會讓指令失敗")
    ap.add_argument("--out", help="同時寫成 markdown 檔")
    args = ap.parse_args()

    sheet = json.load(open(args.sheet, encoding="utf-8-sig"))
    index = json.load(open(args.index, encoding="utf-8-sig"))
    terms = {k.strip("﻿").strip(): v for k, v in index["terms"].items()}
    names = json.load(open(args.names, encoding="utf-8-sig")) if args.names else {}
    ack = json.load(open(args.ack, encoding="utf-8-sig")) if args.ack else {}
    drafts = draft_sections(args.draft)
    texts = entry_texts(sheet)

    patterns = []
    for key, zh in terms.items():
        if len(key) < 3 or not zh:
            continue
        rx = key_regex(key)
        if rx:
            single_cap = key[0].isupper() and " " not in key
            patterns.append((key, zh, re.compile(rx, 0 if single_cap else re.I), single_cap))

    rows, failed = [], 0

    def record(entry, en, zh, n, m, status, note, ctx):
        rows.append((entry, en, zh, n, m, status, note, ctx))

    for entry, bundle in texts.items():
        base = entry
        section = drafts.get(entry)
        if section is None:
            base = re.sub(r"\s\+\d$", "", entry)
            section = drafts.get(base)
        if section is None:
            print("⛔ 底稿缺少 ### %s" % entry)
            failed += 1
            continue
        plain = bundle["plain"]
        for key, zh, rx, single_cap in patterns:
            hits = [m for m in rx.finditer(plain)]
            if single_cap:
                mid = [m for m in hits if m.start() > 0 and plain[max(0, m.start() - 2):m.start()].strip() not in ("", ".", "?", "!", ":")]
                info = len(hits) - len(mid)
                hits = mid
                if not hits:
                    if info:
                        record(entry, key, zh, info, "-", "ℹ️", "句首大寫，人工判斷是否為術語", "")
                    continue
            if not hits:
                continue
            m_count = zh_count(section, zh)
            ctx = snippet(plain, hits[0].start(), hits[0].end())
            if m_count >= len(hits):
                record(entry, key, zh, len(hits), m_count, "✅", "", ctx)
                continue
            reason = ack.get(entry + "|" + key) or ack.get(base + "|" + key) or ack.get(key)
            if reason:
                record(entry, key, zh, len(hits), m_count, "✅📝", reason, ctx)
            else:
                record(entry, key, zh, len(hits), m_count, "❌", "", ctx)
                failed += 1
        # spell names: link labels always, plain mentions only for multi-word names
        for en_name, zh_name in names.items():
            zh = zh_name if isinstance(zh_name, str) else next(iter(zh_name.values()))
            via_label = [l for l in bundle["labels"] if l.strip().lower() == en_name.lower()]
            via_plain = []
            if " " in en_name or "/" in en_name:
                via_plain = re.findall(r"(?<![A-Za-z])" + re.escape(en_name).replace("’", "['’]").replace("\\'", "['’]") + r"(?![A-Za-z])", plain, re.I)
            n = max(len(via_label), len(via_plain))
            if not n:
                continue
            m_count = section.count(zh)
            key = "法術名 " + en_name
            if m_count >= n:
                record(entry, key, zh, n, m_count, "✅", "", "")
            else:
                reason = ack.get(entry + "|" + en_name) or ack.get(base + "|" + en_name) or ack.get(en_name)
                if reason:
                    record(entry, key, zh, n, m_count, "✅📝", reason, "")
                else:
                    record(entry, key, zh, n, m_count, "❌", "", "")
                    failed += 1

    lines = ["| 條目 | EN 詞條 | terms／現行名稱 | EN 次數 | 底稿次數 | 狀態 | 說明／語境 |", "|---|---|---|---|---|---|---|"]
    for entry, en, zh, n, m, status, note, ctx in sorted(rows, key=lambda r: (r[5] != "❌", r[0], r[1])):
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (entry, en, zh, n, m, status, (note or ctx).replace("|", "\\|")))
    summary = "\n共 %d 項命中；❌ 未處理 %d 項。" % (len(rows), failed)
    text = "\n".join(lines) + summary
    print(text)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
