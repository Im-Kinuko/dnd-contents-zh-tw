"""Source-first draft decisions, kept separate from HTML mapping."""
BOUNDS={'Grave Domain':(1,5),'Grave Domain Spells':(7,16),'Circle of Mortality':(18,22),'Path to the Grave':(24,26),"Sentinel at Death's Door":(28,30),'Divine Reaper':(32,35)}

def make(source,scope,live,Plan,visible,names):
    blocks={k:[visible(b.html) for b in Plan(live['entries.'+k+'.description']['target'][0]).blocks] for k in scope}
    reasons={};changes={};lines=source.splitlines()
    def edit(k,i,text,reason):
        blocks[k][i]=text;reasons[k+'|'+str(i)]=reason
    edit('Grave Domain',1,blocks['Grave Domain'][1].replace('亡靈','不死生物'),'定案詞：亡靈→不死生物；其餘現譯照舊。')
    edit('Grave Domain',2,blocks['Grave Domain'][2].replace('它的','其'),'禁用字：它的→其；其餘現譯照舊。')
    edit('Grave Domain Spells',0,blocks['Grave Domain Spells'][0].replace('生命領域','墳墓領域'),'規則：現譯誤用生命領域，EN及原稿均指墳墓領域。')
    # Keep accepted table headings and numbers; visible spell labels were missing.
    spells=[['Detect Evil and Good','False Life','Gentle Repose','Ray of Enfeeblement','Spare the Dying'],['Revivify','Vampiric Touch'],['Blight','Death Ward'],['Dispel Evil and Good','Raise Dead']]
    for i,group in zip([5,7,9,11],spells):
        edit('Grave Domain Spells',i,'、'.join(names[x] for x in group),'定案詞／標記：補上Weblate現行法術名；依EN順序排列，保留原有法術、等級與表格。')
    edit('Circle of Mortality',1,blocks['Circle of Mortality'][1].replace('透過法術或攻擊檢定','透過施放法術，或以攻擊檢定命中，').replace('1d4 黯蝕','1d4黯蝕'),'規則：補出施放法術與攻擊檢定命中兩種傷害來源，逗號界定兩種途徑；保留現譯其餘句子，還原EN傷害巨集。')
    edit('Circle of Mortality',2,blocks['Circle of Mortality'][2].replace('施放。','施放'+names['Spare the Dying']+'。'),'定案詞／標記：補上拯救瀕死的可見標籤；其他現譯照舊。')
    edit('Circle of Mortality',3,lines[21].replace('生命時','生命值時').replace('恢復8點。','恢復8點生命值。'),'規則：現譯「你可以不擲骰」錯誤變成可選；EN don’t roll是必須取最大值，依原稿補回一枚或多枚骰子及生命值為0條件。')
    edit('Path to the Grave',0,blocks['Path to the Grave'][0].replace('作為一個附贈動作，你展示','你可以採取一個附贈動作，展示').replace('直到你的下一回合開始前，詛咒一個30呎範圍內你所能看見的生物。','詛咒位於你30呎內一名你所能看見的生物，直到你的下一回合開始。'),'句式／使用者裁定：作為一個附贈動作→採取一個附贈動作；距離限定詞依位於你X呎內一名你所能看見的生物；持續時間接在詛咒後且直到回合開始不加前；其餘現譯照舊。')
    edit('Path to the Grave',1,blocks['Path to the Grave'][1].replace('暗蝕','黯蝕').replace('牧師等級的額外','牧師等級的'),'定案詞：暗蝕→黯蝕；規則／誤字：移除重複的額外，EN只有一次extra；保留現譯與傷害巨集。')
    edit("Sentinel at Death's Door",0,blocks["Sentinel at Death's Door"][0].replace('浴血','重傷').replace('爆擊','暴擊'),'定案詞：Bloodied＝重傷、Critical Hit＝暴擊；其餘現譯照舊。')
    # The only untranslated feature: draft directly from original lines 33–35.
    edit('Divine Reaper',0,lines[32].replace('深度聯絡','深度聯繫').replace('以下增益','下列好處'),'轉換修正：聯絡→聯繫；定案詞：以下增益→下列好處；其餘原稿照舊。')
    edit('Divine Reaper',1,lines[33].replace('增強死靈術Enhanced Necromancy。 ','【增強死靈術】').replace('施展','施放').replace('如果','若').replace('材料成分','材料構材'),'定案詞／格式：施展→施放、如果→若、材料成分→材料構材；移除英文小標，套用【】且不留句號；原稿其餘句子照舊。')
    edit('Divine Reaper',2,lines[34].replace('眾魂監守者Keeper of Souls。 ','【眾魂監守者】').replace('60尺','60呎').replace('你或你60呎範圍內你可見的一個生物','你或位於你60呎內一名你所能看見的生物').replace('直至你完成短休或長休','直到完成短休或長休前').replace('你也可以消耗','除非你消耗'),'單位／句式／規則：尺→呎；依限定詞一名你所能看見的生物；until採既定句式；unless明確譯成除非，六環法術位重置不需要動作。')
    nested={
        'entries.Divine Reaper.activities.Enhanced Necromancy.name':('增強死靈術','原稿第34行的小標。'),
        'entries.Divine Reaper.activities.Keeper of Souls.name':('眾魂監守者','原稿第35行的小標。'),
        'entries.Divine Reaper.activities.Keeper of Souls.condition':('一名敵人在範圍內死亡時','原稿無獨立欄位；全站同句搜尋無完整中文，依EN與第35行補翻。'),
        'entries.Divine Reaper.activities.Keeper of Souls.target':('可見','沿用同元件entries.Path to the Grave.activities.Curse.target的同句正式譯文。'),
        'entries.Divine Reaper.activities.Restore Keeper of Souls.name':('恢復眾魂監守者','原稿無獨立欄位；全站同句搜尋無中文，依第35行法術位重置句與特性名補翻。'),
        "entries.Sentinel at Death's Door.activities.utility.condition":(live["entries.Sentinel at Death's Door.activities.utility.condition"]['target'][0].replace('浴血','重傷'),'定案詞：浴血→重傷；其餘現譯照舊。'),
    }
    return blocks,reasons,nested
