import json

sheet_path = '_incoming/dnd-arcana-unleashed/arcane-archer.sheet.json'
with open(sheet_path, encoding='utf-8') as f:
    sheet = json.load(f)

# Arcane Archer Lore Advancements
adv = sheet['entries']['Arcane Archer Lore']['advancement']
adv['TC6W4Mugmnci3Re3']['zh_hint'] = "<p>你獲得奧秘和自然技能的熟練。若你已熟練於其中之一，你改為獲得一個你選擇的1級戰士其他可學技能的熟練（或在熟練於二者時獲得兩個1級戰士其他可學技能的熟練）。</p><p><em>1級戰士其他可學技能：</em>特技、動物理學、運動、歷史、洞悉、威嚇、察覺、說服、求生</p>"
adv['LNsgAWw8x2cVxyWs']['zh_hint'] = "<p><em><strong>戲法。</strong></em>你知曉戲法 <em>@UUID[Compendium.dnd5e.spells24.Item.phbsplDruidcraft]{德魯伊伎倆}</em> 或 @UUID[Compendium.dnd5e.spells24.Item.phbsplPrestidigi]{魔法伎倆}。智力是你施展該戲法的施法屬性。</p>"

# Arcane Shot Advancement
adv = sheet['entries']['Arcane Shot']['advancement']
adv['fw8yHNCnQkj4nRqD']['zh_hint'] = "<p>你自後文奧術射擊選項一節習得兩種由你選擇的奧術射擊選項。</p><p>當你的戰士等級到達7級、10級、15級和18級時，你均可習得一種新的奧術射擊選項，同時你也可以將你已知的選項替換為另一種。</p>"

# Ever-Ready Shot Advancement
adv = sheet['entries']['Ever-Ready Shot']['advancement']
adv['UMD7ZTUmkPj4n9L2']['zh_hint'] = "<p>此進階修改奧術射擊為當你投擲先攻時自動恢復一次使用次數。</p>"

# Effects
eff = sheet['entries']['Banishing Shot']['effects']['Banishing Shot']
eff['zh_name'] = "放逐彈"
eff['zh_description'] = "<p>被放逐期間，目標具有&amp;Reference[Incapacitated apply=false]狀態且速度降至0。目標在其下個回合結束時重新出現在其原本所在的空間或最近的未佔據空間（若原空間已被佔據）。</p>"

eff = sheet['entries']['Beguiling Shot']['effects']['Beguiling Shot']
eff['zh_name'] = "欺詐彈"
eff['zh_description'] = "<p>目標具有&amp;Reference[Charmed apply=false]狀態直至你的下個回合開始，其將你或一名你選擇的位於目標30呎內的盟友作為魅惑源。該魅惑狀態在魅惑源對目標發動攻擊、造成傷害或迫使其進行豁免時提前結束。</p>"

eff = sheet['entries']['Enfeebling Shot']['effects']['Enfeebling Shot']
eff['zh_name'] = "虛弱彈"
eff['zh_description'] = "<p>目標具有&amp;Reference[Poisoned apply=false]狀態直至其下個回合結束。每當以此法中毒的目標的攻擊檢定命中時，其此次攻擊的總傷害減少你其中一枚奧術射擊骰的骰值。</p>"

eff = sheet['entries']['Grasping Shot']['effects']['Grasping Shot']
eff['zh_name'] = "纏繞彈"
eff['zh_description'] = "<p>目標具有&amp;Reference[Restrained apply=false]狀態，該狀態將持續1分鐘或在你再次使用此選項時提前結束。目標或其他在其觸及範圍內的生物能夠以動作進行一次力量（運動）檢定對抗你的奧術射擊豁免 DC，檢定成功則移除荊棘並結束目標的束縛狀態。</p>"

eff = sheet['entries']['Shadow Shot']['effects']['Shadow Shot']
eff['zh_name'] = "遮影彈"
eff['zh_description'] = "<p>目標具有&amp;Reference[Blinded apply=false]狀態直至其下個回合結束。</p>"

with open(sheet_path, 'w', encoding='utf-8') as f:
    json.dump(sheet, f, ensure_ascii=False, indent=2)
print("Done injecting advancements and effects.")
