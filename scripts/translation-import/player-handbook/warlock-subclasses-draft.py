"""Source-based draft instructions; imported by warlock-subclasses.py."""
def make(source,live,scope,visible,Plan,spell_names):
    lines=source.splitlines()
    S=lambda n:lines[n-1]
    old=lambda k,i:visible(Plan(live['entries.'+k+'.description']['target'][0]).blocks[i].html)
    names=['至高妖精宗主','至高妖精法術','妖精步伐','霧遁','斗轉星移','醉心魔法','天界宗主','天界法術','治癒之光','光耀之魂','天族韌性','灼光復仇','邪魔宗主','邪魔法術','黑暗者賜福','黑暗強運','邪魔韌性','直墜噩夢','舊日支配者宗主','舊日支配者法術','喚醒心靈','心靈法術','洞若觀火','駭異惡咒','思維之盾','創造奴僕']
    names=dict(zip(scope,names))
    def regular(t):
        for a,b in [('魔契師','契術師'),('施展','施放'),('型別','類型'),('等於','等同於'),('受到','承受'),('倒地','伏地'),('成功透過','成功通過'),('傷害的抗性','傷害的抗力'),('傷害類型的抗性','傷害類型的抗力'),('直至完成長休 ','直到完成長休前'),('直至完成長休','直到完成長休前'),('直至完成短休或長休','直到完成短休或長休前'),('尺','呎')]:t=t.replace(a,b)
        for en,zh in spell_names.items():
            if en in t:
                aliases={'Misty Step':'迷蹤步','Summon Aberration':'異怪召喚術','Hex':'脆弱詛咒'}
                if en in aliases:t=t.replace(aliases[en]+en,zh)
        return t
    main={
      'Archfey Patron':[S(2),S(4)],
      'Steps of the Fey':[old('Steps of the Fey',0),old('Steps of the Fey',1),old('Steps of the Fey',2).replace('你或10呎內你所能看見的生物','你或位於你10呎內一名你所能看見的生物'),old('Steps of the Fey',3).replace('位於你傳送前5呎空間內','位於你離開的空間5呎內').replace('在你下個回合開始前','直到你下個回合開始')],
      'Misty Escape':[regular(S(33)).replace('可以用反應','可以採取反應'),regular(S(34)).replace('以下','下列'),regular(S(35)).replace('無蹤步伐Disappearing Step。','【無蹤步伐】').replace('你獲得隱形狀態','你可以進入隱形狀態').replace('或你進行','或緊接在你進行').replace('之後','後'),regular(S(36)).replace('驚懼步伐Dreadful Step。','【驚懼步伐】').replace('必須進行一次','必須成功通過一次').replace('，豁免失敗則承受','，否則承受')],
      'Beguiling Defenses':[S(39),regular(S(40)).replace('當一個你能看見的敵人的攻擊檢定命中你後','緊接在一名你所能看見的生物以攻擊檢定命中你後').replace('你可以立刻使用反應','你可以採取反應').replace('該次攻擊的傷害減半','你承受的傷害減半')],
      'Bewitching Magic':[regular(S(43)).replace('當你以一個動作消耗法術位施放一道幻術或惑控法術時','緊接在你以一個動作消耗法術位施放一道幻術學派或惑控學派法術後').replace('無需消耗法術位地立刻施放迷蹤步Misty Step 作為該動作的一部分','以該動作的一部分，不消耗法術位施放迷蹤步').replace('無需消耗法術位地立刻施放迷蹤步 作為該動作的一部分','以該動作的一部分，不消耗法術位施放迷蹤步')],
      'Celestial Patron':[S(46),S(48).replace('令你沐浴在','讓你體驗到些許').replace('聖潔輝光之下','聖潔輝光')],
      'Healing Light':[old('Healing Light',0),old('Healing Light',1).replace('作為一個附贈動作，你可以','你可以採取一個附贈動作，')],
      'Radiant Soul':[regular(S(77))],
      'Celestial Resilience':[regular(S(80)).replace('秘法迴流','魔法機靈').replace('你可見的生物','你所能看見的生物')],
      'Searing Vengeance':[regular(S(83)).replace('承受2d8','承受等同於2d8'),regular(S(84))],
      'Fiend Patron':[S(87),S(89)+'而你的道路，取決於你在多大程度上努力對抗那些目標。'],
      "Dark One's Blessing":[old("Dark One's Blessing",0)],
      "Dark One's Own Luck":[S(115).replace('其結果生效前','任何擲骰效應生效前'),regular(S(116)).replace('你在一次檢定中只能','每次擲骰只能')],
      'Fiendish Resilience':[regular(S(119))],
      'Hurl Through Hell':[regular(S(122)).replace('則它會','則目標會').replace('必須進行一次','必須成功通過一次').replace('，豁免失敗則','，否則').replace('直至你的下一回合結束','直到你的下個回合結束前'),regular(S(123))],
      'Great Old One Patron':[old('Great Old One Patron',0),old('Great Old One Patron',1)],
      'Awakened Mind':[old('Awakened Mind',0).replace('作為一個附贈動作，你可以','你可以採取一個附贈動作，').replace('30尺','30呎').replace('哩）的哩數','）的哩數').replace('當前','當前魅力調整值'),old('Awakened Mind',1)],
      'Psychic Spells':[old('Psychic Spells',0)],
      'Clairvoyant Combatant':[old('Clairvoyant Combatant',0).replace('智力豁免','感知豁免'),old('Clairvoyant Combatant',1)],
      'Eldritch Hex':[regular(S(162)).replace('脆弱詛咒',spell_names['Hex'])],
      'Thought Shield':[regular(S(165))],
      'Create Thrall':[regular(S(168)),regular(S(169)).replace('脆弱詛咒',spell_names['Hex'])],
    }
    # Table text and translated body are kept exactly; only untranslated cells and current spell labels are filled.
    for k in [k for k in scope if k.endswith(' Spells') and k!='Psychic Spells']:
        blocks=Plan(live['entries.'+k+'.description']['target'][0]).blocks
        main[k]=[visible(b.html) for b in blocks[:-2]]
        main[k]=['法術' if t=='Spells' else t for t in main[k]]
        import re
        enblocks=Plan(scope[k]['description']).blocks
        for i,b in enumerate(enblocks[:len(main[k])]):
            enlabels=re.findall(r'@UUID\[[^\]]+\]\{([^}]+)\}',b.html)
            if enlabels:main[k][i]='、'.join(spell_names[e] for e in enlabels)
    supp={
      'Steps of the Fey':['【Foundry註記】','振奮步伐行動包含臨時生命值。','嘲弄步伐行動包含豁免與一項用於追蹤的Active Effect，但不會自動套用該效應。','當你升級時，會獲得可免費使用的該法術。'],
      'Misty Escape':['【Foundry註記】','無蹤步伐行動包含一項Active Effect，可套用隱形狀態。'],
      'Beguiling Defenses':['【Foundry註記】','斗轉反應行動包含豁免。','選取你的指示物後，你可以在傷害擲骰的聊天卡片上按右鍵並選擇應用半傷，或按下「1/2」按鈕，再按下應用按鈕。'],
      'Healing Light':['【Foundry註記】','治療行動允許你調整從骰池中消耗的骰子數量，並自動將數量限制為你的魅力調整值。'],
      'Radiant Soul':['【Foundry註記】','當你升級時，會自動獲得對光耀傷害的抗力。','傷害行動包含傷害擲骰，讓你在擲骰對話框中選擇傷害類型。你也可以在擲傷害骰時，將你的魅力調整值填入該法術的環境加值欄位。'],
      'Celestial Resilience':['【Foundry註記】','你的臨時生命值與所選生物生命值行動皆包含各自目標應獲得的正確臨時生命值數值。'],
      'Searing Vengeance':['【Foundry註記】','恢復至生命值上限一半的治療並未自動處理，但傷害行動包含相關目標範本與傷害擲骰，也包含一項可套用目盲狀態的Active Effect。'],
      'Fiendish Resilience':['【Foundry註記】','此特性為每種傷害類型提供一項Active Effect，可賦予對應的抗力。當你更換傷害類型時，視需要應用與停用這些效果。'],
      'Hurl Through Hell':['【Foundry註記】','此特性包含一次有限的使用次數。','重獲使用次數行動會消耗一個契約魔法法術位，並恢復此特性的一次使用次數。'],
      'Clairvoyant Combatant':['【Foundry註記】','豁免行動包含一項Active Effect，可用來追蹤劣勢，但不會自動套用優勢或劣勢。','重獲使用次數行動會扣除一個契約魔法法術位，並恢復此特性的一次使用次數。'],
      'Create Thrall':['【Foundry註記】','脆弱詛咒行動包含額外傷害。','奴僕臨時生命值行動包含在不需專注召喚奴僕時，要賦予奴僕的臨時生命值。','當你升級時，會自動獲得該法術。']
    }
    for k in [k for k in scope if k.endswith(' Spells') and k!='Psychic Spells']:supp[k]=['【Foundry註記】','當你升級時，會自動獲得這些法術。']
    nested={}
    labels={'Subclass Features':'子職業特性','Refreshing Step':'振奮步伐','Taunting Step':'嘲弄步伐','Disappearing Step':'無蹤步伐','Dreadful Step':'驚懼步伐','Beguiling Reaction':'斗轉反應','Heal':'治療','Damage':'傷害','Your Temporary Hit Points':'你的臨時生命值','Chosen Creatures Hit Points':'所選生物生命值','Luck':'幸運','Bonus':'加值','Regain Use':'重獲使用次數','Telepathic Connection':'心靈感應連結','A Powerful Curse':'強大的詛咒','Hex Damage':'詛咒傷害','Thrall Temporary HP':'奴僕臨時生命值','Hex':spell_names['Hex'],'Save':'豁免','Foundry Note':'【Foundry註記】',**names}
    conditions={
      'Immediately after you teleport':'緊接在你傳送後','That you can see':'你所能看見的','After teleporting':'傳送後','Of the space you just left':'你剛離開的空間周圍','That you choose':'由你選擇的','After taking damage':'承受傷害後',
      'Immediately after a creature you can see hits you with an attack roll':'緊接在一名你所能看見的生物以攻擊檢定命中你後',
      'Whenever you use your Magical Cunning or finish a Short or Long Rest':'每當你使用魔法機靈，或完成短休或長休時','You can see when you gain the points':'你獲得臨時生命值時所能看見的',
      'When you or an ally within 60 feet of you is about to make a Death Saving Throw':'當你或位於你60呎內的一名盟友將要進行一次死亡豁免時',
      'When you reduce an enemy to 0 Hit Points or  an enemy within 10 feet of you is reduced to 0 Hit Points':'當你將一名敵人的生命值降至0，或位於你10呎內的一名敵人的生命值降至0時',
      'When you make an ability check or saving throw':'當你進行屬性檢定或豁免檢定時','Once per turn when you hit a creature with an attack roll':'每回合一次，當你以攻擊檢定命中一名生物時',
      'When you form a telepathic bond using Awakened Mind':'當你使用喚醒心靈建立心靈連結時','When your thrall hits a creature under the effect of your Hex':'當你的奴僕命中一名受你脆弱詛咒影響的生物時',
      'When you cast Hex without Concentration':'當你不需專注施放脆弱詛咒時',
      'This creature has Disadvantage on attack rolls against creatures other than you until the start of your next turn.':'直到你的下個回合開始，該生物對你之外的生物進行攻擊檢定時具有劣勢。',
    }
    dmg={'Acid':'強酸','Bludgeoning':'鈍擊','Cold':'寒冷','Fire':'火焰','Lightning':'閃電','Necrotic':'黯蝕','Piercing':'穿刺','Poison':'毒素','Psychic':'心靈','Radiant':'光耀','Slashing':'揮砍','Thunder':'雷鳴'}
    for en,zh in dmg.items():labels['Fiendish Resilience: '+en]='邪魔韌性：'+zh
    return names,main,supp,labels,conditions
