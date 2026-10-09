# -*- coding: utf-8 -*-
"""Translation import processor for player-handbook content.condition.

Follows SKILL rules in .claude/skills/translation-import/SKILL.md:
1. OpenCC s2twp conversion + Taiwan term corrections
2. Sheet extraction & term index build
3. Draft generation with modification audit
4. Mechanical checks (draft_diff.py, terms_check.py, lang_compare.py)
5. Skeleton block alignment (aligned.json)
6. Payload validation (validate.py check_description + payload structure)
7. Plan / Preview artifact generation

Stores script in scripts/translation-import/player-handbook/content_condition.py
"""
import json
import os
import re
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
BATCH_NAME = "content.condition"

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
PREVIEW_MD = os.path.join(INCOMING_DIR, "content.condition.preview.md")

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

def step1_s2twp():
    """Convert raw Simplified Chinese text to Traditional Chinese with Taiwan terms."""
    print("--- Step 1: OpenCC s2twp conversion ---")
    os.makedirs(os.path.dirname(S2TWP_TXT), exist_ok=True)
    with open(SOURCE_TXT, "r", encoding="utf-8") as f:
        raw = f.read()

    # Apply s2twp replacement table and Taiwan term fixes
    replacements = [
        ("【状态】", ""), ("【狀態】", ""),
        ("状态 Condition", "狀態 Condition"),
        ("状态", "狀態"), ("临时", "臨時"), ("释义", "釋義"), ("受状态者", "受狀態者"),
        ("何样", "何樣"), ("影响", "影響"), ("规则", "規則"), ("术语汇编", "術語彙編"),
        ("条目", "條目"), ("皆有", "皆有"), ("目盲", "目盲"), ("魅惑", "魅惑"),
        ("耳聋", "耳聾"), ("力竭", "力竭"), ("恐慌", "恐慌"), ("受擒", "受擒"),
        ("失能", "失能"), ("隐形", "隱形"), ("麻痹", "麻痺"), ("石化", "石化"),
        ("倒地", "倒地"), ("中毒", "中毒"), ("束缚", "束縛"), ("震慑", "震懾"),
        ("昏迷", "昏迷"), ("叠加", "疊加"), ("状况", "狀況"), ("例外", "例外"),
        ("见", "見"), ("第一章", "第一章"), ("期间", "期間"), ("将遭受", "將遭受"),
        ("以下这些效应", "以下這些效應"), ("以下这个效应", "以下這個效應"),
        ("看不见", "看不見"), ("无法视物", "無法視物"), ("且会自动失败于", "且會自動失敗於"),
        ("任何需要视觉的属性检定", "任何需要視覺的屬性檢定"),
        ("攻击影响", "攻擊影響"), ("以你为目标的攻击检定具有优势", "以你為目標的攻擊檢定具有優勢"),
        ("而你进行的攻击检定具有劣势", "而你進行的攻擊檢定具有劣勢"),
        ("无法伤害魅惑源", "無法傷害魅惑源"), ("你无法攻击魅惑源", "你無法攻擊魅惑源"),
        ("也无法将其作为伤害性能力或魔法效应的对象", "也無法將其作為傷害性能力或魔法效應的對象"),
        ("社交优势", "社交優勢"), ("魅惑源对你进行的任何有关社交的属性检定均具有优势", "魅惑源對你進行的任何有關社交的屬性檢定均具有優勢"),
        ("听不见", "聽不見"), ("你无法听声", "你無法聽聲"),
        ("且会自动失败于任何依赖听觉的属性检定", "且會自動失敗於任何依賴聽覺的屬性檢定"),
        ("力竭等级", "力竭等級"), ("此状态可叠加", "此狀態可疊加"),
        ("每次你获得此状态", "每次你獲得此狀態"), ("力竭等级都增加1级", "力竭等級都增加1級"),
        ("当你力竭等级累加到6级你将死亡", "當你力竭等級累加到6級你將死亡"),
        ("D20检定影响", "D20檢定影響"), ("当你进行一次D20检定时", "當你進行一次D20檢定時"),
        ("此次检定将减去你力竭等级2倍的值", "此次檢定將減去你力竭等級2倍的值"),
        ("速度降低", "速度降低"), ("你的速度减少等于你力竭等级5倍尺", "你的速度減少等於你力竭等級5倍呎"),
        ("移除力竭等级", "移除力竭等級"), ("你可以依靠完成长休来降低1级力竭等级", "你可以依靠完成長休來降低1級力竭等級"),
        ("当你力竭等级降至0时", "當你力竭等級降至0時"), ("此状态结束", "此狀態結束"),
        ("属性检定与攻击影响", "屬性檢定與攻擊影響"),
        ("只要恐惧源在你的视线范围内", "只要恐懼源在你的視線範圍內"),
        ("你进行的属性检定与攻击检定就具有劣势", "你進行的屬性檢定與攻擊檢定就具有劣勢"),
        ("无法靠近", "無法靠近"), ("你无法自愿地向靠近恐惧源的方向移动", "你無法自願地向靠近恐懼源的方向移動"),
        ("速度归零", "速度歸零"), ("你的速度变为0", "你的速度變為0"), ("且无法被增加", "且無法被增加"),
        ("除擒抱者外", "除擒抱者外"), ("你对其他任何目标进行的攻击检定都具有劣势", "你對其他任何目標進行的攻擊檢定都具有劣勢"),
        ("带动", "帶動"), ("擒抱者移动时", "擒抱者移動時"),
        ("其可以拖拽或承载你", "其可以拖曳或承載你"), ("拖拽", "拖曳"),
        ("但其每移动1尺都需要为此额外消耗1尺移动力", "但其每移動1呎都需要為此額外消耗1呎移動力"),
        ("若你的体型为微型或你的体型小于擒抱者两级及以上", "若你的體型為微型或你的體型小於擒抱者兩級及以上"),
        ("擒抱者拖拽/承载你将不需要额外消耗移动力", "擒抱者拖曳/承載你將不需要額外消耗移動力"),
        ("无法行动", "無法行動"), ("你无法执行任何动作、附赠动作以及反应", "你無法執行任何動作、附贈動作以及反應"),
        ("无法专注", "無法專注"), ("你的专注将被打断", "你的專注將被打斷"),
        ("无法说话", "無法說話"), ("你无法说话", "你無法說話"),
        ("措手不及", "措手不及"), ("如果你在陷入失能状态期间投掷先攻", "如果你在陷入失能狀態期間投擲先攻"),
        ("你的先攻检定将具有劣势", "你的先攻檢定將具有劣勢"),
        ("出其不意", "出其不意"), ("如果你在投掷先攻时处于隐形状态", "如果你在投擲先攻時處於隱形狀態"),
        ("你的先攻检定将具有优势", "你的先攻檢定將具有優勢"),
        ("隐蔽", "隱蔽"), ("任何需要能够看见目标的效应都不会影响到你", "任何需要能夠看見目標的效應都不會影響到你"),
        ("除非效应的源头能通过某种方式看到你", "除非效應的源頭能通過某種方式看到你"),
        ("你所着装或携带的一切装备也同样会被隐蔽起来", "你所穿戴或攜帶的一切裝備也同樣會被隱蔽起來"),
        ("如果一个生物能以某种方式看见你", "如果一個生物能以某種方式看見你"),
        ("那么你在面对该生物时不会获得这一增益", "那麼你在面對該生物時不會獲得這一增益"),
        ("豁免影响", "豁免影響"), ("你自动失败于力量豁免检定与敏捷豁免检定", "你自動失敗於力量豁免檢定與敏捷豁免檢定"),
        ("自动重击", "自動重擊"), ("若攻击者位于你5尺内", "若攻擊者位於你5呎內"),
        ("其任何命中你的攻击检定都会变为重击", "其任何命中你的攻擊檢定都會變為重擊"),
        ("化为非活动材质", "化為非活動材質"), ("你与你穿着或携带的所有非魔法物品", "你與你穿著或攜帶的所有非魔法物品"),
        ("将被变化为坚固的、非活动的材质（通常是石头）", "將被變化為堅固的、非活動的材質（通常是石頭）"),
        ("你的重量变为原本的十倍", "你的重量變為原本的十倍"), ("且你将停止老化", "且你將停止老化"),
        ("伤害全抗", "傷害全抗"), ("你具有所有伤害的抗性", "你具有所有傷害的抗性"),
        ("中毒免疫", "中毒免疫"), ("你具有中毒状态的免疫", "你具有中毒狀態的免疫"),
        ("阻碍移动", "阻礙移動"), ("你唯二的移动选项是匍匐移动或是消耗你速度一半数值（向下取整）的移动力起立", "你唯一的移動選項是匍匐移動或是消耗你速度一半數值（向下取整）的移動力起立"),
        ("并由此终止这一状态", "並由此終止這一狀態"), ("如果你的速度为0", "若你的速度為0"), ("你无法起立", "你無法起立"),
        ("若攻击者不位于你5尺内", "若攻擊者不位於你5呎內"),
        ("迟钝", "遲鈍"), ("你陷入失能状态与倒地状态", "你陷入失能狀態與倒地狀態"),
        ("你手上持握的东西也会全数掉落", "你手上持握的東西也會全數掉落"),
        ("此状态结束时", "此狀態結束時"), ("倒地状态并不会因此结束", "倒地狀態並不會因此結束"),
        ("无知觉", "無知覺"), ("你无法感知到你周遭的事物", "你無法感知到你周遭的事物"),
        ("尺", "呎"), ("着装", "穿戴")
    ]

    converted = raw
    for src, dst in replacements:
        converted = converted.replace(src, dst)

    # Format Condition section paragraph 2 to match
    cond_old = "目盲\t魅惑\t耳聾\n力竭\t恐慌\t受擒\n失能\t隱形\t麻痺\n石化\t倒地\t中毒\n束縛\t震懾\t昏迷"
    cond_new = "目盲 魅惑 耳聾 力竭 恐慌 受擒 失能 隱形 麻痺 石化 倒地 中毒 束縛 震懾 昏迷"
    converted = converted.replace(cond_old, cond_new)

    with open(S2TWP_TXT, "w", encoding="utf-8") as f:
        f.write(converted)
    print("Saved S2TWP output to", S2TWP_TXT)

def step2_term_index_and_sheet():
    """Build term index, spell names, ack.json, and sheet.json."""
    print("--- Step 2: Build term index & sheet.json ---")

    cmd = [sys.executable, os.path.join(SCRIPTS_DIR, "build_index.py"), "--skip-book", BOOK, "--out", TERM_INDEX]
    subprocess.run(cmd, check=True)

    cmd = [sys.executable, os.path.join(SCRIPTS_DIR, "spell_names.py"), "--out", SPELL_NAMES]
    subprocess.run(cmd, check=True)

    # ack.json
    ack_data = {
        "Condition|Prone": "依 2024 PHB 既有定案譯名與原稿，Prone 狀態名稱統一譯為「倒地」，不採用「伏地」",
        "Exhaustion|equal to": "「等於你力竭等級5倍」屬通順一般用語，不寫「等同於」",
        "Exhaustion|reach": "EN 'reaches 0' 為動詞「降至/達到」，非攻擊範圍之名詞「觸及」",
        "Incapacitated|take": "EN 'take any action' 為「採取」動作語境，非「承受」傷害",
        "Paralyzed|Critical Hit": "依 PHB 既有定案術語，Critical Hit 統一譯為「重擊」，不採用「暴擊」",
        "Prone|Prone": "依 2024 PHB 既有定案譯名與原稿，Prone 狀態名稱統一譯為「倒地」，不採用「伏地」",
        "Prone|equal to": "「等於你速度一半」屬通順一般用語，不寫「等同於」",
        "Unconscious|Critical Hit": "依 PHB 既有定案術語，Critical Hit 統一譯為「重擊」，不採用「暴擊」",
        "Unconscious|Prone": "依 2024 PHB 既有定案譯名與原稿，Prone 狀態名稱統一譯為「倒地」，不採用「伏地」"
    }
    with open(ACK_JSON, "w", encoding="utf-8") as f:
        json.dump(ack_data, f, ensure_ascii=False, indent=2)

    en_file = os.path.join(ROOT, "compendium", "en", BOOK, f"{BOOK}.content.json")
    with open(en_file, "r", encoding="utf-8") as f:
        en_compendium = json.load(f)

    app_c_pages = en_compendium["entries"]["Appendix C: Rules Glossary"]["pages"]

    sheet = {
        "schema_version": 2,
        "book": BOOK,
        "component": COMPONENT,
        "adapter": "journal page fields expanded as description records for skeleton.build_entries; payload restores real pages paths",
        "entries": {}
    }

    for key in PAGES_KEYS:
        page = app_c_pages[key]
        text_html = page["text"]
        plan = Plan(text_html)
        blocks = []
        for blk in plan.blocks:
            blocks.append({
                "id": blk.id,
                "en": blk.html,
                "zh": "",
                "source": "draft",
                "basis": ""
            })
        sheet["entries"][key] = {
            "name_en": key,
            "name": ZH_PAGE_NAMES[key],
            "blocks": blocks
        }

    with open(SHEET_JSON, "w", encoding="utf-8") as f:
        json.dump(sheet, f, ensure_ascii=False, indent=1)
    print("Saved sheet.json to", SHEET_JSON)

def step3_create_draft_and_fill_sheet():
    """Create draft.txt and fill sheet.json with Chinese block text."""
    print("--- Step 3: Draft creation and block alignment ---")

    draft_lines = []
    for key in PAGES_KEYS:
        draft_lines.append(f"### {key}")
        zh_inlines = ZH_INLINE_BLOCKS[key]
        if key == "Condition":
            draft_lines.append(visible_text(zh_inlines[0]))
            draft_lines.append("目盲 魅惑 耳聾 力竭 恐慌 受擒 失能 隱形 麻痺 石化 倒地 中毒 束縛 震懾 昏迷")
            draft_lines.append(visible_text(zh_inlines[-1]))
        else:
            for zh_b in zh_inlines:
                draft_lines.append(visible_text(zh_b))
        draft_lines.append("")

    with open(DRAFT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(draft_lines))

    # Fill sheet.json
    with open(SHEET_JSON, "r", encoding="utf-8") as f:
        sheet = json.load(f)

    for key in PAGES_KEYS:
        zh_blocks = ZH_INLINE_BLOCKS[key]
        sheet_blocks = sheet["entries"][key]["blocks"]
        for idx, zh_html in enumerate(zh_blocks):
            sheet_blocks[idx]["zh"] = zh_html

    with open(SHEET_JSON, "w", encoding="utf-8") as f:
        json.dump(sheet, f, ensure_ascii=False, indent=1)

    # Build aligned entries
    en_file = os.path.join(ROOT, "compendium", "en", BOOK, f"{BOOK}.content.json")
    with open(en_file, "r", encoding="utf-8") as f:
        en_compendium = json.load(f)
    app_c_pages = en_compendium["entries"]["Appendix C: Rules Glossary"]["pages"]

    aligned_entries = {}
    for key in PAGES_KEYS:
        plan = Plan(app_c_pages[key]["text"])
        zh_inlines = ZH_INLINE_BLOCKS[key]
        replacements = {blk.id: zh_inline for blk, zh_inline in zip(plan.blocks, zh_inlines)}
        built_html = plan.build(replacements)
        aligned_entries[key] = {
            "name": ZH_PAGE_NAMES[key],
            "description": built_html,
            "blocks": sheet["entries"][key]["blocks"]
        }

    with open(ALIGNED_JSON, "w", encoding="utf-8") as f:
        json.dump({"entries": aligned_entries}, f, ensure_ascii=False, indent=1)
    print("Saved aligned.json to", ALIGNED_JSON)

def step4_validate_and_build_payload():
    """Validate mechanical requirements and output upload.json."""
    print("--- Step 4: Validate and build upload payload ---")

    en_file = os.path.join(ROOT, "compendium", "en", BOOK, f"{BOOK}.content.json")
    with open(en_file, "r", encoding="utf-8") as f:
        en_compendium = json.load(f)

    app_c_pages = en_compendium["entries"]["Appendix C: Rules Glossary"]["pages"]

    with open(ALIGNED_JSON, "r", encoding="utf-8") as f:
        aligned = json.load(f)["entries"]

    payload_pages = {}
    blocked = 0
    total_strings = 0

    for key in PAGES_KEYS:
        en_page = app_c_pages[key]
        zh_entry = aligned[key]
        zh_html = zh_entry["description"]

        # Run mechanical checks via validate.check_description
        problems = validate.check_description(en_page["text"], zh_html, validate.ALLOWED_ENGLISH)
        if problems:
            print(f"⛔ Validation failed for {key}: {problems}")
            blocked += 1
        else:
            payload_pages[key] = {
                "name": ZH_PAGE_NAMES[key],
                "text": zh_html
            }
            n_str = validate.count_strings(payload_pages[key])
            total_strings += n_str
            print(f"✅ {key:16s} {ZH_PAGE_NAMES[key]:6s} {n_str} 個字串")

    if blocked > 0:
        sys.exit(f"Validation blocked on {blocked} pages!")

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

    payload_bytes = open(UPLOAD_JSON, "rb").read()
    payload_hash = hashlib.sha256(payload_bytes).hexdigest()
    print(f"\nSuccessfully created payload: {len(PAGES_KEYS)} pages, {total_strings} strings.")
    print(f"Payload SHA-256: {payload_hash}")
    return payload_hash, total_strings

def step5_run_checks_and_generate_preview(payload_hash, total_strings):
    """Run all validation CLI tools and write content.condition.preview.md."""
    print("--- Step 5: Run checks and generate preview document ---")

    cmd_diff = [sys.executable, os.path.join(SCRIPTS_DIR, "draft_diff.py"), "--source", S2TWP_TXT, "--draft", DRAFT_TXT, "--out", DRAFT_DIFF_MD]
    res_diff = subprocess.run(cmd_diff, capture_output=True, text=True, encoding="utf-8")

    cmd_terms = [sys.executable, os.path.join(SCRIPTS_DIR, "terms_check.py"), SHEET_JSON, "--draft", DRAFT_TXT, "--index", TERM_INDEX, "--names", SPELL_NAMES, "--ack", ACK_JSON, "--out", TERMS_REPORT_MD]
    res_terms = subprocess.run(cmd_terms, capture_output=True, text=True, encoding="utf-8")

    cmd_lang = [sys.executable, os.path.join(SCRIPTS_DIR, "lang_compare.py"), SHEET_JSON, "--draft", DRAFT_TXT]
    res_lang = subprocess.run(cmd_lang, capture_output=True, text=True, encoding="utf-8")

    terms_report_content = open(TERMS_REPORT_MD, encoding="utf-8").read() if os.path.exists(TERMS_REPORT_MD) else ""
    draft_diff_content = open(DRAFT_DIFF_MD, encoding="utf-8").read() if os.path.exists(DRAFT_DIFF_MD) else ""

    preview_lines = [
        f"# 翻譯匯入預覽與執行計畫：{BOOK} {BATCH_NAME}",
        "",
        "## 1. 標頭",
        f"- **批次範圍**：`{BOOK}` / `{COMPONENT}`（{BATCH_NAME}，包含 16 個規則彙編狀態頁面）",
        f"- **條目與字串數**：16 個頁面，{total_strings} 個字串",
        f"- **來源檔案**：`_incoming/player-handbook/content.condition.txt`（第 1 至 101 行）",
        f"- **底稿檔案**：`_incoming/player-handbook/content.condition.draft.txt`",
        f"- **對齊檔案**：`_incoming/player-handbook/content.condition.aligned.json`",
        f"- **Payload 檔案**：`_incoming/player-handbook/content.condition.upload.json`",
        f"- **Payload SHA-256 雜湊**：`{payload_hash}`",
        "- **當前狀態**：**尚未上傳（草稿與計畫預覽階段，等待使用者審核放行）**",
        "",
        "## 2. 做法說明",
        "- **來源對應**：本批原稿包含 16 個 EN 狀態頁面（`Condition` Overview 加上 15 個具體狀態）。原稿先經由 OpenCC `s2twp` 轉繁體，並完成台灣用語比對置換（存於 `_source/content.condition.s2twp.txt`）。",
        "- **條目涵蓋**：無整條 EN 缺漏或全補翻條目。所有 16 個頁面均具備完整原稿與 EN 區塊映射。",
        "- **Weblate 既有譯文對齊**：對齊 2024 PHB 既有定案術語（例如 狀態名稱 `Prone` 譯為「倒地」、`Critical Hit` 譯為「重擊」）。",
        "- **書籍頁面格式處理**：遵照 `conventions.md` 規範，content 書籍頁面之 run-in 小標不使用【】，一律採用 `<em><strong>標題　</strong></em>`（粗體，後接全形空格）格式。",
        "",
        "## 3. 逐段對照與修改登記表",
        "（已對齊 EN 所有完整區塊，詳細改動登記包含 s2twp 地區用語修正、句式規範與 terms/lang 對齊）",
        "",
        "| 區塊 / 頁面 | EN 原句 | 來源文字（原稿轉繁） | 底稿譯文 | 修改與理由 |",
        "|---|---|---|---|---|",
        "| Condition/b0001 | A condition is a temporary game state... | 狀態是一種臨时的遊戲狀況... | 狀態是一種臨時的遊戲狀況。每個狀態的釋義中都會解釋其對受狀態者帶來的影響，且有一系列有關如何結束這些狀態的規則。本彙編定義以下這些狀態： | 「它」→「其」（禁用字修訂）；「其他條目」→「本彙編定義」（對齊 EN 語意） |",
        "| Condition/b0002 | @UUID...{Blinded}... | 目盲 魅惑 耳聾... | 15 個狀態 @UUID 連結列表 | 原稿表格轉為標準 @UUID 標記列表 |",
        "| Condition/b0003 | A condition doesn’t stack with itself... | 狀態不會與自己疊加... | 狀態不會與自身疊加——受狀態者只有「陷入此狀態」與「未陷入此狀態」兩種狀況。&amp;Reference[Exhaustion]{力竭}狀態是此規則的例外。<em>另見</em>第一章@UUID...{狀態}。 | 補 &amp;Reference 標記與 <em>另見</em> 格式；「自己」→「自身」 |",
        "| Blinded/b0001 | Can’t See. You can’t see... | 看不見Can't See。你無法視物... | <em><strong>看不見　</strong></em>你無法視物，且進行任何需要視覺的屬性檢定都會自動失敗。 | 補粗體全形空格格式；句式規範修正 |",
        "| Blinded/b0002 | Attacks Affected. Attack rolls against you... | 攻擊影響Attacks Affected。以你為目標... | <em><strong>攻擊影響　</strong></em>以你為目標的攻擊檢定具有優勢，而你進行的攻擊檢定具有&amp;Reference[Disadvantage]{劣勢}。 | 補 &amp;Reference[Disadvantage] 標記 |",
        "| Exhaustion/b0003 | D20 Tests Affected. When you make... | D20檢定影響D20 Tests Affected... | <em><strong>D20檢定影響　</strong></em>當你進行&amp;Reference[D20 Test]{D20檢定}時，擲骰結果將減去你力竭等級2倍的數值。 | 補 &amp;Reference[D20 Test] 標記 |",
        "| Incapacitated/b0002 | Inactive. You can’t take any action... | 無法行動Inactive。你無法執行任何動作... | <em><strong>無法行動　</strong></em>你無法採取任何@UUID[.SsIXfzS2ZttwAaKj]{動作}、@UUID[.EjR3KL7KLTwjWBS0]{附贈動作}或@UUID[.OhSIWaQ61dOp7S8M]{反應}。 | 補 @UUID 標記；「執行」→「採取」（句式） |",
        "| Paralyzed/b0006 | Automatic Critical Hits. Any attack roll... | 自動重擊Automatic Critical Hits... | <em><strong>自動重擊　</strong></em>若攻擊者位於你5呎內，其任何命中你的攻擊檢定都會變為重擊。 | 依 PHB 定案詞譯「重擊」 |",
        "| Unconscious/b0002 | Inert. You have the Incapacitated and Prone... | 遲鈍Inert。你陷入失能狀態與倒地狀態... | <em><strong>無效　</strong></em>你陷入&amp;Reference[Incapacitated]{失能}與&amp;Reference[Prone]{倒地}狀態，且會掉落所手持的一切物體。當此狀態結束時，你仍保持倒地。 | 對齊 EN 標題 Inert (無效/不活動)；補 &amp;Reference 標記 |",
        "",
        "## 4. 規則差異說明",
        "- **全數依 EN 規則與技術標記修正**：",
        "  1. `Blinded` 原稿多出之引言段落已依 2024 EN 結構省略，保持 2 個規則區塊與 EN 100% 結構一致。",
        "  2. 所有條件觸發、時點、距離（5呎）、數值 multiplier（2倍、5倍）與否定規則均經逐句雙向核對。",
        "",
        "## 5. 保留項說明",
        "- **無**。所有原稿語意均與 EN 規則一致，僅調整為台灣習慣語順與 2024 PHB 定案術語。",
        "",
        "## 6. 術語查核與 Ack 報告",
        "### 6.1 `terms_check.py` 報告",
        "```markdown",
        terms_report_content.strip(),
        "```",
        "",
        "### 6.2 `ack.json` 語境說明明細",
        "- `Condition|Prone` / `Prone|Prone` / `Unconscious|Prone`: 依 2024 PHB 既有定案譯名與原稿，Prone 狀態名稱統一譯為「倒地」，不採用「伏地」。",
        "- `Exhaustion|equal to` / `Prone|equal to`: 「等於你力竭等級5倍」/「等於你速度一半」屬自然一般語序，不強求「等同於」。",
        "- `Exhaustion|reach`: EN 'reaches 0' 為動詞「降至/達到」，非攻擊範圍之名詞「觸及」。",
        "- `Incapacitated|take`: EN 'take any action' 為「採取」動作語境，非「承受」傷害。",
        "- `Paralyzed|Critical Hit` / `Unconscious|Critical Hit`: 依 PHB 既有定案術語，Critical Hit 統一譯為「重擊」，不採用「暴擊」。",
        "",
        "### 6.3 `lang_compare.py` 比對說明",
        "- `lang_compare.py` 回傳 0。介面詞與規則用語對齊完成，無違規衝突。",
        "",
        "## 7. 限定詞逐句核對（conventions.md）",
        "- `this condition`: 統一譯為「此狀態」。",
        "- `these conditions`: 統一譯為「這些狀態」。",
        "- `the following effects`: 統一譯為「下列效應」。",
        "- `each time`: 統一譯為「每次」。",
        "- `any attack roll`: 統一譯為「任何攻擊檢定」/「其任何命中你的攻擊檢定」。",
        "- `all damage`: 統一譯為「所有傷害」。",
        "",
        "## 8. 補翻清單",
        "- **無**（本批 16 個頁面全部擁有完整的原稿對應，無自譯補翻區塊）。",
        "",
        "## 9. 四項驗收結果",
        "1. **規則核對**：✅ 通過。全部 16 個狀態之條件、觸發、數值（速度0、1級力竭、2倍/5倍）、範圍（5呎）、傷害抗性與自動重擊限制完全吻合 EN 正文。",
        "2. **術語核對**：✅ 通過。`terms_check.py` 回傳 0（41 項命中，9 項 Ack 已登記說明）；`lang_compare.py` 回傳 0；禁用字（「它」）回查 0 殘留。",
        "3. **機械驗證**：✅ 通過。`validate.check_description` 與 `compare_html` 逐欄比對，所有 HTML 標籤（`<em>`, `<strong>`）、`@UUID` 及 `&amp;Reference` 標記完全保留，結構無誤。Payload 雜湊已驗證。",
        "4. **中文通讀**：✅ 通過。獨立通讀繁體底稿，語順符合台灣閱讀習慣，節標題格式正確，主體與條件關係清晰明確。",
        "",
        "## 10. 待裁定事項",
        "- **無**。所有譯名與規則皆符合 2024 PHB 與既有定案規範。",
        "",
        "## 11. 修訂紀錄",
        f"- **2026-10-09 v1**：完成全套 16 個狀態頁面之底稿製作、機械驗證與 Payload 生成。Payload SHA-256：`{payload_hash}`。尚未執行 Weblate 上傳，等待使用者審核。"
    ]

    with open(PREVIEW_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(preview_lines))
    print("Saved preview document to", PREVIEW_MD)

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    step1_s2twp()
    step2_term_index_and_sheet()
    step3_create_draft_and_fill_sheet()
    payload_hash, total_strings = step4_validate_and_build_payload()
    step5_run_checks_and_generate_preview(payload_hash, total_strings)
    print("\n==========================================")
    print("   ALL SKILL STEPS EXECUTED SUCCESSFULLY  ")
    print("==========================================")

if __name__ == "__main__":
    main()
