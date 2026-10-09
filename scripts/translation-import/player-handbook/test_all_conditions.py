# -*- coding: utf-8 -*-
"""Complete test script for player-handbook content.condition.

Verifies block HTML matching, compare_html, terms_check, draft_diff, lang_compare,
and validate.check_description for all 16 condition pages.
"""
import json
import os
import sys
import hashlib
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SK_DIR = os.path.join(ROOT, ".claude", "skills", "translation-import")
SCRIPTS_DIR = os.path.join(SK_DIR, "scripts")

sys.path.insert(0, SCRIPTS_DIR)

import skeleton
import html_blocks
from html_blocks import Plan, compare_html, visible_text
import validate

BOOK = "dnd-players-handbook"
COMPONENT = "content"

INCOMING_DIR = os.path.join(ROOT, "_incoming", "player-handbook")
SOURCE_TXT = os.path.join(INCOMING_DIR, "content.condition.txt")
S2TWP_TXT = os.path.join(INCOMING_DIR, "_source", "content.condition.s2twp.txt")
DRAFT_TXT = os.path.join(INCOMING_DIR, "content.condition.draft.txt")
SHEET_JSON = os.path.join(INCOMING_DIR, "content.condition.sheet.json")
TERM_INDEX = os.path.join(INCOMING_DIR, "content.condition.term_index.json")
SPELL_NAMES = os.path.join(ROOT, "spell-names.json")
ACK_JSON = os.path.join(INCOMING_DIR, "ack.json")
DRAFT_DIFF_MD = os.path.join(INCOMING_DIR, "content.condition.draft-diff.md")
TERMS_REPORT_MD = os.path.join(INCOMING_DIR, "content.condition.terms-report.md")
LANG_COMPARE_MD = os.path.join(INCOMING_DIR, "content.condition.lang-compare.md")
ALIGNED_JSON = os.path.join(INCOMING_DIR, "content.condition.aligned.json")
UPLOAD_JSON = os.path.join(INCOMING_DIR, "content.condition.upload.json")

PAGES_KEYS = [
    "Condition", "Blinded", "Charmed", "Deafened", "Exhaustion",
    "Frightened", "Grappled", "Incapacitated", "Invisible", "Paralyzed",
    "Petrified", "Poisoned", "Prone", "Restrained", "Stunned", "Unconscious"
]

ZH_PAGE_NAMES = {
    "Condition": "狀態",
    "Blinded": "目盲",
    "Charmed": "魅惑",
    "Deafened": "耳聾",
    "Exhaustion": "力竭",
    "Frightened": "恐慌",
    "Grappled": "受擒",
    "Incapacitated": "失能",
    "Invisible": "隱形",
    "Paralyzed": "麻痺",
    "Petrified": "石化",
    "Poisoned": "中毒",
    "Prone": "倒地",
    "Restrained": "束縛",
    "Stunned": "震懾",
    "Unconscious": "昏迷"
}

ZH_INLINE_BLOCKS = {
    "Condition": [
        "狀態是一種臨時的遊戲狀況。每個狀態的釋義中都會解釋其對受狀態者帶來的影響，且有一系列有關如何結束這些狀態的規則。本彙編定義以下這些狀態：",
        "@UUID[.uDogReMO6QtH6NDw]{目盲}",
        "@UUID[.vLAsIUa0FhZNsyLk]{魅惑}",
        "@UUID[.qlRw66tJhk0zLnwq]{耳聾}",
        "@UUID[.jSQtPgNm0i4f3Qi3]{力竭}",
        "@UUID[.93uaingTESo8N1qL]{恐慌}",
        "@UUID[.KbQ1k0OIowtZeQgp]{受擒}",
        "@UUID[.4i3G895hy99piand]{失能}",
        "@UUID[.MQIZ1zRLWRcNOtPN]{隱形}",
        "@UUID[.RnxZoTglPnLc6UPb]{麻痺}",
        "@UUID[.6vtLuQT9lwZ9N299]{石化}",
        "@UUID[.HWs8kEojffqwTSJz]{中毒}",
        "@UUID[.QxCrRcgMdUd3gfzz]{倒地}",
        "@UUID[.dqLeGdpHtb8FfcxX]{束縛}",
        "@UUID[.EjbXjvyQAMlDyANI]{震懾}",
        "@UUID[.fZCRaKEJd4KoQCqH]{昏迷}",
        "狀態不會與自身疊加——受狀態者只有「陷入此狀態」與「未陷入此狀態」兩種狀況。&amp;Reference[Exhaustion]{力竭}狀態是此規則的例外。<em>另見</em>第一章@UUID[Compendium.dnd-players-handbook.content.JournalEntry.phbConditions000.JournalEntryPage.BuIBCfux6QYAah3q]{狀態}。"
    ],
    "Blinded": [
        "<em><strong>看不見　</strong></em>你無法視物，且進行任何需要視覺的屬性檢定都會自動失敗。",
        "<em><strong>攻擊影響　</strong></em>以你為目標的攻擊檢定具有優勢，而你進行的攻擊檢定具有&amp;Reference[Disadvantage]{劣勢}。"
    ],
    "Charmed": [
        "處於魅惑狀態期間，你遭受下列效應。",
        "<em><strong>無法傷害魅惑源　</strong></em>你無法攻擊魅惑源，也無法將其作為傷害性能力或魔法效應的目標。",
        "<em><strong>社交優勢　</strong></em>魅惑源對你進行任何社交互動的屬性檢定時均具有優勢。"
    ],
    "Deafened": [
        "<strong>聽不見　</strong>你無法聽聲，且進行任何需要聽覺的屬性檢定都會自動失敗。"
    ],
    "Exhaustion": [
        "處於力竭狀態期間，你遭受下列效應。",
        "<em><strong>力竭等級　</strong></em>此狀態可疊加。每次你獲得此狀態時，力竭等級增加1級。若你的力竭等級達到6級，你將死亡。",
        "<em><strong>D20檢定影響　</strong></em>當你進行&amp;Reference[D20 Test]{D20檢定}時，擲骰結果將減去你力竭等級2倍的數值。",
        "<em><strong>速度降低　</strong></em>你的&amp;Reference[Speed]{速度}減少等於你力竭等級5倍的呎數。",
        "<em><strong>移除力竭等級　</strong></em>完成一次&amp;Reference[Long Rest]{長休}可移除你1級力竭等級。當你的力竭等級降至0時，此狀態結束。"
    ],
    "Frightened": [
        "處於恐慌狀態期間，你遭受下列效應。",
        "<em><strong>屬性檢定與攻擊影響　</strong></em>只要恐懼源位於你的視線範圍內，你進行的屬性檢定與攻擊檢定就具有&amp;Reference[Disadvantage]{劣勢}。",
        "<em><strong>無法靠近　</strong></em>你無法自願朝向靠近恐懼源的方向移動。"
    ],
    "Grappled": [
        "處於受擒狀態期間，你遭受下列效應。",
        "<em><strong>速度0　</strong></em>你的速度變為0，且無法增加。",
        "<em><strong>攻擊影響　</strong></em>除擒抱者外，你對任何其他目標進行的攻擊檢定都具有&amp;Reference[Disadvantage]{劣勢}。",
        "<em><strong>帶動　</strong></em>擒抱者移動時可以拖曳或攜帶你，但除非你的體型為微型或比擒抱者小至少兩個階級，否則其每移動1呎都需要額外消耗1呎移動力。"
    ],
    "Incapacitated": [
        "處於&amp;Reference[incapacitated]{失能}狀態期間，你遭受下列效應。",
        "<em><strong>無法行動　</strong></em>你無法採取任何@UUID[.SsIXfzS2ZttwAaKj]{動作}、@UUID[.EjR3KL7KLTwjWBS0]{附贈動作}或@UUID[.OhSIWaQ61dOp7S8M]{反應}。",
        "<em><strong>無法專注　</strong></em>你的@UUID[.0a2umg2mJMAzM9Q3]{專注}被打斷。",
        "<em><strong>無法說話　</strong></em>你無法說話。",
        "<em><strong>措手不及　</strong></em>若你在投擲先攻時處於失能狀態，你的先攻檢定具有&amp;Reference[Disadvantage]{劣勢}。"
    ],
    "Invisible": [
        "處於隱形狀態期間，你遭受下列效應。",
        "<em><strong>出其不意　</strong></em>若你在投擲先攻時處於隱形狀態，你的先攻檢定具有&amp;Reference[Advantage]{優勢}。",
        "<em><strong>隱蔽　</strong></em>任何需要看見目標的效應都不會影響你，除非效應的創造者能以某種方式看見你。你穿戴或攜帶的任何裝備也同樣被隱蔽。",
        "<em><strong>攻擊影響　</strong></em>以你為目標的攻擊檢定具有&amp;Reference[Disadvantage]{劣勢}，而你的攻擊檢定具有優勢。若某生物能以某種方式看見你，你面對該生物時不會獲得此好處。"
    ],
    "Paralyzed": [
        "處於麻痺狀態期間，你遭受下列效應。",
        "<em><strong>失能　</strong></em>你陷入&amp;Reference[Incapacitated]{失能}狀態。",
        "<em><strong>速度0　</strong></em>你的速度變為0，且無法增加。",
        "<em><strong>豁免影響　</strong></em>你的力量豁免檢定與敏捷豁免檢定自動失敗。",
        "<em><strong>攻擊影響　</strong></em>以你為目標的攻擊檢定具有&amp;Reference[Advantage]{優勢}。",
        "<em><strong>自動重擊　</strong></em>若攻擊者位於你5呎內，其任何命中你的攻擊檢定都會變為重擊。"
    ],
    "Petrified": [
        "處於石化狀態期間，你遭受下列效應。",
        "<em><strong>轉化為無生命物質　</strong></em>你連同所穿戴與攜帶的所有非魔法物體，一起被轉化為堅固的無生命物質（通常是石頭）。你的重量變為原本的十倍，且你停止衰老。",
        "<em><strong>失能　</strong></em>你陷入&amp;Reference[Incapacitated]{失能}狀態。",
        "<em><strong>速度0　</strong></em>你的速度變為0，且無法增加。",
        "<em><strong>攻擊影響　</strong></em>以你為目標的攻擊檢定具有&amp;Reference[Advantage]{優勢}。",
        "<em><strong>豁免影響　</strong></em>你的力量豁免檢定與敏捷豁免檢定自動失敗。",
        "<em><strong>傷害抗性　</strong></em>你對所有傷害都具有&amp;Reference[Resistance]{抗性}。",
        "<em><strong>中毒免疫　</strong></em>你對&amp;Reference[Poisoned]{中毒}狀態免疫。"
    ],
    "Poisoned": [
        "處於中毒狀態期間，你遭受下列效應。",
        "<em><strong>屬性檢定與攻擊影響　</strong></em>你的攻擊檢定與屬性檢定具有&amp;Reference[Disadvantage]{劣勢}。"
    ],
    "Prone": [
        "處於倒地狀態期間，你遭受下列效應。",
        "<em><strong>限制移動　</strong></em>你唯一的移動選擇是匍匐移動，或是消耗等於你&amp;Reference[Speed]{速度}一半（向下取整）的移動力起立並由此結束此狀態。若你的速度為0，你無法起立。",
        "<em><strong>攻擊影響　</strong></em>你的攻擊檢定具有&amp;Reference[Disadvantage]{劣勢}。若攻擊者位於你5呎內，以你為目標的攻擊檢定具有&amp;Reference[Advantage]{優勢}；否則，該攻擊檢定具有劣勢。"
    ],
    "Restrained": [
        "處於束縛狀態期間，你遭受下列效應。",
        "<em><strong>速度0　</strong></em>你的&amp;Reference[Speed]{速度}為0，且無法增加。",
        "<em><strong>攻擊影響　</strong></em>以你為目標的攻擊檢定具有優勢，而你的攻擊檢定具有&amp;Reference[Disadvantage]{劣勢}。",
        "<em><strong>豁免影響　</strong></em>你的敏捷豁免檢定具有劣勢。"
    ],
    "Stunned": [
        "處於震懾狀態期間，你遭受下列效應。",
        "<em><strong>失能　</strong></em>你陷入@UUID[.4i3G895hy99piand]{失能}狀態。",
        "<em><strong>豁免影響　</strong></em>你的力量豁免檢定與敏捷豁免檢定自動失敗。",
        "<em><strong>攻擊影響　</strong></em>以你為目標的攻擊檢定具有&amp;Reference[Advantage]{優勢}。"
    ],
    "Unconscious": [
        "處於昏迷狀態期間，你遭受下列效應。",
        "<em><strong>無效　</strong></em>你陷入&amp;Reference[Incapacitated]{失能}與&amp;Reference[Prone]{倒地}狀態，且會掉落所手持的一切物體。當此狀態結束時，你仍保持倒地。",
        "<em><strong>速度0　</strong></em>你的&amp;Reference[Speed]{速度}為0，且無法增加。",
        "<em><strong>攻擊影響　</strong></em>以你為目標的攻擊檢定具有&amp;Reference[Advantage]{優勢}。",
        "<em><strong>豁免影響　</strong></em>你的力量豁免檢定與敏捷豁免檢定自動失敗。",
        "<em><strong>自動重擊　</strong></em>若攻擊者位於你5呎內，其任何命中你的攻擊檢定都會變為重擊。"
    ]
}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    en_file = os.path.join(ROOT, "compendium", "en", BOOK, f"{BOOK}.content.json")
    with open(en_file, "r", encoding="utf-8") as f:
        en_compendium = json.load(f)

    app_c_pages = en_compendium["entries"]["Appendix C: Rules Glossary"]["pages"]

    # 1. Build sheet.json
    sheet = {
        "schema_version": 2,
        "book": BOOK,
        "component": COMPONENT,
        "adapter": "journal page fields expanded as description records for skeleton.build_entries; payload restores real pages paths",
        "entries": {}
    }

    payload_pages = {}
    total_strings = 0
    errors_found = 0

    # Build draft text file
    draft_lines = []

    for key in PAGES_KEYS:
        en_text = app_c_pages[key]["text"]
        plan = Plan(en_text)
        sheet_blocks = []
        zh_inlines = ZH_INLINE_BLOCKS[key]

        if len(plan.blocks) != len(zh_inlines):
            print(f"❌ {key} block length mismatch: EN {len(plan.blocks)} vs ZH {len(zh_inlines)}")
            errors_found += 1
            continue

        draft_lines.append(f"### {key}")

        replacements = {}
        for blk, zh_inline in zip(plan.blocks, zh_inlines):
            sheet_blocks.append({
                "id": blk.id,
                "en": blk.html,
                "zh": zh_inline,
                "source": "draft",
                "basis": ""
            })
            replacements[blk.id] = zh_inline
            draft_lines.append(visible_text(zh_inline))

        draft_lines.append("")

        sheet["entries"][key] = {
            "name_en": key,
            "name": ZH_PAGE_NAMES[key],
            "blocks": sheet_blocks
        }

        # Build full ZH HTML for page
        built_zh_html = plan.build(replacements)

        # Check HTML comparison
        errs = compare_html(en_text, built_zh_html)
        if errs:
            print(f"❌ compare_html failed for {key}: {errs}")
            errors_found += 1

        # Check validate.check_description
        problems = validate.check_description(en_text, built_zh_html, validate.ALLOWED_ENGLISH)
        if problems:
            print(f"❌ check_description failed for {key}: {problems}")
            errors_found += 1
        else:
            payload_pages[key] = {
                "name": ZH_PAGE_NAMES[key],
                "text": built_zh_html
            }
            n_str = validate.count_strings(payload_pages[key])
            total_strings += n_str
            print(f"✅ {key:16s} {ZH_PAGE_NAMES[key]:6s} {n_str} 個字串")

    if errors_found > 0:
        sys.exit(f"Failed with {errors_found} errors!")

    # Write files
    with open(SHEET_JSON, "w", encoding="utf-8") as f:
        json.dump(sheet, f, ensure_ascii=False, indent=1)

    with open(DRAFT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(draft_lines))

    with open(ALIGNED_JSON, "w", encoding="utf-8") as f:
        json.dump({"entries": {k: {"name": ZH_PAGE_NAMES[k], "description": payload_pages[k]["text"], "blocks": sheet["entries"][k]["blocks"]} for k in PAGES_KEYS}}, f, ensure_ascii=False, indent=1)

    final_payload = {
        "entries": {
            "Appendix C: Rules Glossary": {
                "name": "附錄 C：規則彙編",
                "pages": payload_pages
            }
        }
    }

    with open(UPLOAD_JSON, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, ensure_ascii=False, indent=1)

    payload_hash = hashlib.sha256(open(UPLOAD_JSON, "rb").read()).hexdigest()
    print(f"\nSuccessfully validated all 16 condition pages!")
    print(f"Total payload pages: {len(payload_pages)}, total strings: {total_strings}")
    print(f"Payload SHA-256: {payload_hash}")

    # Run check tools
    print("\n--- Running draft_diff.py ---")
    cmd_diff = [sys.executable, os.path.join(SCRIPTS_DIR, "draft_diff.py"), "--source", S2TWP_TXT, "--draft", DRAFT_TXT, "--out", DRAFT_DIFF_MD]
    res_diff = subprocess.run(cmd_diff, capture_output=True, text=True, encoding="utf-8")
    print("draft_diff return code:", res_diff.returncode)
    if res_diff.stdout:
        print(res_diff.stdout[:500])

    print("\n--- Running terms_check.py ---")
    cmd_terms = [sys.executable, os.path.join(SCRIPTS_DIR, "terms_check.py"), SHEET_JSON, "--draft", DRAFT_TXT, "--index", TERM_INDEX, "--names", SPELL_NAMES, "--ack", ACK_JSON, "--out", TERMS_REPORT_MD]
    res_terms = subprocess.run(cmd_terms, capture_output=True, text=True, encoding="utf-8")
    print("terms_check return code:", res_terms.returncode)
    if res_terms.stdout:
        print(res_terms.stdout[:500])

    print("\n--- Running lang_compare.py ---")
    cmd_lang = [sys.executable, os.path.join(SCRIPTS_DIR, "lang_compare.py"), SHEET_JSON, "--draft", DRAFT_TXT]
    res_lang = subprocess.run(cmd_lang, capture_output=True, text=True, encoding="utf-8")
    print("lang_compare return code:", res_lang.returncode)
    if res_lang.stdout:
        print(res_lang.stdout[:500])

if __name__ == "__main__":
    main()
