"""Rogue manuscript edits made before mapping. Existing compatible text is retained."""
import re
BOUNDS={'Arcane Trickster':(2,4),'Assassin':(54,56),'Soulknife':(80,82),'Thief':(139,141),'phbrgeSpellcasti':(7,16),'Mage Hand Legerdemain':(40,40),'Magical Ambush':(43,43),'Versatile Trickster':(46,46),'Spell Thief':(49,51),'Assassinate':(59,62),"Assassin's Tools":(65,65),'Infiltration Expertise':(68,71),'Envenom Weapons':(74,74),'Death Strike':(77,77),'phbrgePsionicPow':(85,112),'Psychic Blades':(115,122),'Psychic Blade':(115,122),'Soul Blades':(125,128),'Psychic Veil':(131,132),'Rend Mind':(135,136),'Fast Hands':(144,147),'Second-Story Work':(150,153),'Supreme Sneak':(156,158),'Use Magic Device':(161,165),"Thief's Reflexes":(168,168)}
def make(source,live,scope,visible,Plan,spells):
    lines=source.splitlines();S=lambda n:lines[n-1]
    old=lambda k,i:visible(Plan(live['entries.'+k+'.description']['target'][0]).blocks[i].html)
    proposed=['詭術師','刺客','魂刃','竊賊','施法','法師之手花招','詭術伏擊','萬能詭術','法術竊賊','暗殺','刺客工具','專業滲透','淬毒武器','致命襲殺','靈能力量','心靈之刃','心靈之刃','靈魂之刃','靈能面紗','撕裂心智','快手','樑上君子','極效潛行','使用魔法裝置','竊賊反射']
    names=dict(zip(scope,proposed))
    for k in names:
        existing=live['entries.'+k+'.name']['target'][0]
        if re.search('[一-鿿]',existing):names[k]=existing
    def regular(t):
        for a,b in [('施展','施放'),('如果','若'),('它們','其'),('它','其'),('以下','下列'),('增益','好處'),('型別','類型'),('遠端','遠程'),('成功透過','成功通過'),('受到','承受'),('毒素抗性','毒素傷害抗力'),('等於','等同於'),('尺','呎'),('一里','1哩'),('直至完成長休','直到完成長休前'),('子職','子職業')]:t=t.replace(a,b)
        return t
    def heading(t,en,zh):return t.replace(en+'。','】').replace(zh+'】','【'+zh+'】',1)
    main={
      'Arcane Trickster':[old('Arcane Trickster',0),old('Arcane Trickster',1)],
      'Assassin':[old('Assassin',0),old('Assassin',1)],
      'Soulknife':[old('Soulknife',0),old('Soulknife',1)],
      'Thief':[S(139),S(141).replace('子職','子職業')],
      'phbrgeSpellcasti':[
          old('phbrgeSpellcasti',0).replace('以下','下列'),
          '【戲法】你知曉三個戲法：'+spells['Mage Hand']+'和另外兩個從法師法術列表中你所選擇的戲法。推薦選擇'+spells['Mind Sliver']+'和'+spells['Minor Illusion']+'。',
          old('phbrgeSpellcasti',2).replace('Mage Hand',spells['Mage Hand']),
          old('phbrgeSpellcasti',3),old('phbrgeSpellcasti',4),
          old('phbrgeSpellcasti',5).split('推薦選擇')[0]+'推薦選擇'+spells['Charm Person']+'、'+spells['Disguise Self']+'、'+spells['Fog Cloud']+'。',
          old('phbrgeSpellcasti',6).removeprefix('T').replace('遊蕩者施法表','詭術師施法表').replace('選擇額外的法術','選擇額外的法師法術').replace('所選法術的環階必須是你擁有的法術位','所選法術的環階必須是你擁有的法術位對應的環階').replace('應該包括','可以包括'),
          old('phbrgeSpellcasti',7),old('phbrgeSpellcasti',8),old('phbrgeSpellcasti',9)],
      'Mage Hand Legerdemain':[old('Mage Hand Legerdemain',0).replace('你能以附贈動作施放','你可以採取附贈動作施放').replace('你能以附贈動作控制','你可以採取附贈動作控制').replace('來進行檢定','來進行敏捷（巧手）檢定')],
      'Magical Ambush':[regular(S(43)).replace('其在那個回合','該生物在同一個回合')],
      'Versatile Trickster':[regular(S(46)).replace('法師之手Mage Hand ',spells['Mage Hand']).replace('五呎','5呎')],
      'Spell Thief':[regular(S(49)).replace('獲得瞭','獲得了'),regular(S(50)).replace('當生物施放','緊接在一名生物施放').replace('的法術後，你可以立即執行反應','的法術後，你可以採取反應').replace('效應區域','效應範圍').replace('直至這八小時結束','直到這八小時結束前'),'當你以此特性偷得法術後，直到完成長休前，你都無法再次使用此特性。'],
      'Assassinate':[regular(S(59)),heading(regular(S(61)),'Initiative','先攻'),heading(regular(S(62)),'Surprising Strikes','驚擾突襲')],
      "Assassin's Tools":[old("Assassin's Tools",0)],
      'Infiltration Expertise':[regular(S(68)),heading(regular(S(70)),'Masterful Mimicry','模仿大師'),heading(regular(S(71)),'Roving Aim','機動瞄準').replace('穩定瞄準',live['entries.Steady Aim.name']['target'][0])],
      'Envenom Weapons':[regular(S(74)).replace('額外2D6','額外2d6').replace('其會承受','目標會承受')],
      'Death Strike':[regular(S(77)).replace('DC8+','DC為8＋').replace('+','＋')],
      'phbrgePsionicPow':[regular(S(85)), '魂刃靈能骰','遊蕩者等級','骰面','數量',
          *[x for i in [(3,'D6',4),(5,'D8',6),(9,'D8',8),(11,'D10',8),(13,'D10',10),(17,'D12',12)] for x in map(str,i)],
          regular(S(108)),regular(S(109)),heading(regular(S(110)),'Psi-Bolstered Knack','靈振訣竅'),
          heading(regular(S(111)),'Psychic Whispers','心靈低語').replace('以一個魔法動作，從可見的生物中','你可以採取一個魔法動作，從你所能看見的生物中').replace('你在投擲結果數的小時內','在等同於擲骰結果數的小時內'),
          '每次長休後第一次使用此異能時，你不會消耗靈能骰。除此之外，每次使用此異能你都得消耗一枚靈能骰。'],
      'Psychic Blades':[old('Psychic Blades',i) for i in range(7)],
      'Psychic Blade':[old('Psychic Blade',i) for i in range(3)],
      'Soul Blades':[regular(S(125)).replace('念刃','心靈之刃'),heading(regular(S(127)),'Homing Strikes','尋的斬擊').replace('念刃','心靈之刃'),heading(regular(S(128)),'Psychic Teleportation','心靈傳送').replace('以一個附贈動作','你可以採取一個附贈動作').replace('念刃','心靈之刃').replace('一處可見的未佔據空間','一處你所能看見的未佔據空間')],
      'Psychic Veil':[regular(S(131)).replace('以一個魔法動作，你獲得隱形狀態','你可以採取一個魔法動作，進入隱形狀態').replace('持續至多1小時','持續1小時').replace('造成傷害或迫使一個生物進行豁免檢定會導致隱形狀態立刻結束','緊接在你對一名生物造成傷害或迫使一名生物進行豁免檢定後，此隱形狀態會提前結束'),regular(S(132))],
      'Rend Mind':[regular(S(135)).replace('念刃','心靈之刃').replace('DC=8+','DC為8＋').replace('+','＋').replace('目標將在陷入長達一分鐘的震懾','目標將陷入震懾狀態，持續1分鐘').replace('在他的回合結束時','在其每個回合結束時'),regular(S(136))],
      'Fast Hands':[regular(S(144)).replace('透過附贈動作','採取附贈動作'),heading(regular(S(146)),'Sleight of Hand','巧手').replace('盜賊工具','盜賊工具組'),heading(regular(S(147)),'Use an Object','使用物件').replace('執行操作動作','採取利用動作').replace('執行魔法動作','採取魔法動作')],
      'Second-Story Work':[regular(S(150)),heading(regular(S(152)),'Climber','攀爬者'),heading(regular(S(153)),'Jumper','跳躍者')],
      'Supreme Sneak':[regular(S(156)),regular(S(158)).replace('無聲襲擊Stealth Attack (花費：1d6)。','【無聲襲擊（消耗：1d6）】').replace('四分之三掩護','四分之三掩蔽').replace('全身掩護','全掩蔽')],
      'Use Magic Device':[regular(S(161)).replace('曆險','歷險'),heading(regular(S(163)),'Attunement','同調'),heading(regular(S(164)),'Charges','充能'),heading(regular(S(165)),'Scrolls','卷軸').replace('施法關鍵屬性','施法屬性').replace('更高等級的法術','更高環階的法術').replace('必須透過一次成功的','必須先成功通過一次').replace('該法術的等級','該法術的環階').replace('卷軸化為塵埃','卷軸會瓦解')],
      "Thief's Reflexes":[S(168)]
    }
    main['Psychic Blades'][4]=main['Psychic Blades'][4].replace('精通：精通','精通：侵擾')
    main['Soul Blades'][2]=main['Soul Blades'][2].replace('將心靈之刃投擲到至多距離靈能骰結果數字十倍呎數的一處你所能看見的未佔據空間內','將心靈之刃投擲到一處你所能看見的未佔據空間，距離至多等同於靈能骰擲骰結果的十倍呎數')
    main['Soul Blades'][2]=main['Soul Blades'][2].replace('採取一個附贈動作，你塑造','採取一個附贈動作，塑造')
    main['Spell Thief'][1]=main['Spell Thief'][1].replace('該生物無法施放該法術直到這八小時結束前。','直到這八小時結束前，該生物無法施放該法術。')
    main['Use Magic Device'][2]=main['Use Magic Device'][2].replace('魔法物品的消耗充能的特性','魔法物品會消耗充能的屬性')
    main['Supreme Sneak'][1]=main['Supreme Sneak'][1].replace('四分之三掩蔽','四分之三掩護')
    names['Second-Story Work']='梁上君子'
    main['Rend Mind'][0]=main['Rend Mind'][0].replace('被震懾的目標可以在其每個回合結束時','被震懾的目標在其每個回合結束時')
    main['Infiltration Expertise'][1]=main['Infiltration Expertise'][1].replace('來進行鑽研後','來研究某人後').replace('模仿其他人的','模仿該人的')
    main['phbrgePsionicPow'][25]=main['phbrgePsionicPow'][25].replace('你可以投擲靈能骰','你可以投擲一枚靈能骰')
    main['Psychic Blades'][6]=main['Psychic Blades'][6].replace('就能以附贈動作','就能採取附贈動作')
    main['Psychic Blade'][2]=main['Psychic Blade'][2].replace('就能以附贈動作','就能採取附贈動作')
    supp={
      'Assassinate':['【Foundry註記】','此特性包含一項Active Effect，會自動為先攻擲骰提供優勢。','傷害行動可用來套用等同於你等級的額外傷害。你可以在擲骰對話框中選擇傷害類型。或者，你也可以將你的等級（當前遊蕩者等級）填入一般傷害擲骰的環境加值欄位。'],
      "Assassin's Tools":['【Foundry註記】','當你升級時，會自動獲得裝備及熟練。'],
      'Envenom Weapons':['【Foundry註記】','此特性的淬毒行動包含豁免與毒素傷害。','或者，若你已使用原本的行動，可以使用上方的行內擲骰。','【重要】此傷害不會自動無視抗力，請確認套用的傷害正確。'],
      'Death Strike':['【Foundry註記】','致命襲殺行動包含豁免與你的一般偷襲傷害。','選取目標後，你可以在傷害擲骰的聊天卡片上按右鍵並選擇應用雙倍傷害，或按下「2」按鈕，再按下應用按鈕。'],
      'phbrgePsionicPow':['【Foundry註記】','此特性會在短休時自動恢復一次使用次數，長休時恢復全部使用次數。','靈振訣竅行動會消耗一枚靈能骰，並包含加值擲骰。若檢定仍然失敗，你可以退回已消耗的靈能骰。','此特性包含心靈低語行動及心靈低語（免費）行動。兩者皆包含一項Active Effect，可用於追蹤你已納入的生物。'],
      'Psychic Blades':['【Foundry註記】','當你獲得此特性時，會獲得一把心靈之刃，其會出現在你的物品欄中，並包含上述特性。'],
      'Soul Blades':['【Foundry註記】','尋的斬擊行動會消耗一枚靈能骰，並提供擲骰。若檢定仍然失敗，你可以退回該骰。','心靈傳送行動會消耗一枚靈能骰，並提供擲骰。接著，你可以在擲出的射程內放置目標範本，以表示你想傳送的位置（但不會自動傳送）。'],
      'Psychic Veil':['【Foundry註記】','靈能面紗（免費）行動包含一次免費使用次數。靈能面紗行動會消耗一枚靈能骰。兩者皆包含一項Active Effect，可套用隱形狀態。'],
      'Rend Mind':['【Foundry註記】','撕裂心智（免費）行動包含此特性的一次免費使用次數。撕裂心智行動會消耗三枚靈能骰。兩個行動皆包含豁免及一項可套用震懾狀態的Active Effect。'],
      'Fast Hands':['【Foundry註記】','巧手與盜賊工具組行動包含相關檢定。','使用物件行動可用於追蹤附贈動作的使用。'],
      'Second-Story Work':['【Foundry註記】','此特性不會自動增加攀爬速度，必須手動新增。'],
      'Use Magic Device':['【Foundry註記】','此特性包含一項Active Effect，會自動提高你的同調數量上限。','使用會消耗充能的物品屬性時，擲d6，並取消勾選消耗選項，就能免費使用該屬性。']
    }
    labels={**names,'Spellcasting':'施法','Subclass Features':'子職業特性','Max Prepared Spells':'準備法術上限','Psionic Power':'靈能力量','Psi-Bolstered Knack':'靈振訣竅','Psychic Whispers':'心靈低語','Psychic Whispers (Free)':'心靈低語（免費）','Psychic Veil (Free)':'靈能面紗（免費）','Rend Mind (Free)':'撕裂心智（免費）','Stolen Spell':'被竊取的法術','Assasinate':'暗殺','Veiled':'受靈能面紗遮蔽','Attunement Bonus':'同調加值','Bonus Attack':'附贈攻擊','Poison':'淬毒','Damage':'傷害','Homing Strikes':'尋的斬擊','Psychic Teleportation':'心靈傳送','Sleight of Hand':'巧手',"Thieves' Tools":'盜賊工具組','Use an Object':'使用物件','Psionic Energy Die':'靈能骰','Psionic Bonus':'靈能加值','Max Throw Distance':'投擲距離上限','Bonus':'加值','Creatures you can see':'你所能看見的生物','Unoccupied space':'未佔據空間','Foundry Note':'【Foundry註記】','Cantrips':'戲法','Spell Slots':'法術位','Prepared Spells of Level 1+':'準備1環以上的法術','Changing Your Prepared Spells':'更換準備法術','Spellcasting Ability':'施法屬性','Spellcasting Focus':'施法法器','the rules on spellcasting':'施法規則','Wizard spell list':'法師法術列表','Arcane Trickster Spellcasting table':'詭術師施法表','Arcane Tricksters':'詭術師','Assassin’s':'刺客','Thief subclass':'竊賊子職業','Initiative':'先攻','Surprising Strikes':'驚擾突襲','Masterful Mimicry':'模仿大師','Roving Aim':'機動瞄準','Important':'【重要】','Attunement':'同調','Charges':'充能','Scrolls':'卷軸','Spell Scroll,':'法術卷軸','Climber':'攀爬者','Jumper':'跳躍者','Stealth Attack (Cost: 1d6)':'無聲襲擊（消耗：1d6）','Weapon Category:':'武器種類：','Damage on a Hit:':'命中傷害：','Properties:':'屬性：','Mastery:':'精通：'}
    fields={
      'When you fail an ability check using a skill or tool with which you\'re proficient':'當你使用具有熟練的技能或工具進行屬性檢定但失敗時',
      'Miss an Attack Roll with your Psychic Blades':'使用心靈之刃進行攻擊檢定但未命中',
      'When you deal Sneak Attack damage with your Psychic Blades':'當你使用心靈之刃造成偷襲傷害時',
      'When you deal Sneak Attack damage':'當你造成偷襲傷害時',
      'When you hit with your Sneak Attack on the first round of a combat':'當你在戰鬥的第一輪以偷襲命中時',
      'Your Sneak Attack hits any target during the first round':'你的偷襲在第一輪中命中任意目標',
      'Immediately after a creature casts a spell that targets you or includes you in its area of effect':'緊接在一名生物施放一道以你為目標或效應範圍包括你的法術後',
      '<p>This creature has had a spell stolen from it and cannot cast it for 8 hours.</p>':'<p>此生物有一道法術被竊取，8小時內無法施放該法術。</p>',
      '<p>You have Advantage on Initiative rolls.</p>':'<p>你的先攻擲骰具有優勢。</p>',
      '<p>The chosen creatures can speak telepathically with you, and you can speak telepathically with them. To send or receive a message (no action required), you and the other creature must be within 1 mile of each other. A creature can end the telepathic connection at any time (no action required).</p>':'<p>所選生物能透過心靈感應與你交流，你也能透過心靈感應與其交流。傳送或接收資訊時（無需動作），你與另一名生物之間的距離必須不超過1哩。生物可以隨時終止心靈感應的連結（無需動作）。</p>',
      '<p>You gain the Invisible condition for 1 hour or until you dismiss this effect (no action required). This invisibility ends early immediately after you deal damage to a creature or you force a creature to make a saving throw.</p>':'<p>你進入隱形狀態，持續1小時或直到你解除此效應（無需動作）。緊接在你對一名生物造成傷害或迫使一名生物進行豁免檢定後，此隱形狀態會提前結束。</p>',
      '<p>The target has the Stunned condition for 1 minute. The Stunned target repeats the save at the end of each of its turns, ending the effect on itself on a success.</p>':'<p>目標陷入震懾狀態，持續1分鐘。陷入震懾的目標在其每個回合結束時重複該豁免，成功則結束其身上的該效應。</p>',
      '<p>The Use Magic Device feature allows you to attune to up to four magic items at once.</p>':'<p>使用魔法裝置特性讓你可以同時同調至多四件魔法物品。</p>',
    }
    return names,main,supp,labels,fields
