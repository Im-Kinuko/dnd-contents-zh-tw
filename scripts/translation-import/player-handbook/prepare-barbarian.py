"""Local preparation only. No Weblate writes; original source and draft stay intact."""
import json, re, sys
from pathlib import Path
import opencc


ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
sys.path.insert(0, str(ROOT / '.claude/skills/translation-import/scripts'))
from html_blocks import Plan, visible_text, compare_html

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')

prefix = HERE / 'classes.barbarian.1'
sheet = read(Path(str(prefix) + '.sheet.json'))
draft_path = Path(str(prefix) + '.draft.txt')
draft = draft_path.read_text(encoding='utf-8')
sections = {}
for section in re.split(r'^### ', draft, flags=re.M)[1:]:
    lines = section.strip().splitlines()
    sections[lines[0]] = lines[1:]
source = next((HERE / '_web/barbarian').glob('*.htm.txt'))
source_text = source.read_text(encoding='utf-8')
(HERE / 'barbarian.source.s2twp.txt').write_text(opencc.OpenCC('s2twp').convert(source_text), encoding='utf-8')

supplement_text = {
    'Rage': ['<strong>【Foundry註記】</strong>', '此特性包含一項Active Effect，會自動套用抗力、額外傷害，以及力量檢定和力量豁免的優勢。此特性也會在短休和長休時自動恢復你的狂暴使用次數。'],
    'Danger Sense': ['<strong>【Foundry註記】</strong>', '此特性會自動套用敏捷豁免檢定的優勢，但在你失能時不會自動停用。你可以在效果分頁中暫時停用此特性。'],
    'Reckless Attack': ['<strong>【Foundry註記】</strong>', '此特性包含一項Active Effect，用來追蹤你是否處於魯莽狀態，但不會自動套用你的攻擊或以你為目標的攻擊所具有的優勢。'],
    'Primal Knowledge': ['<strong>【Foundry註記】</strong>', '此特性包含一項Active Effect；若你的力量調整值高於該技能通常使用的屬性值，該效果會讓這些技能自動使用你的力量調整值。'],
    'Fast Movement': ['<strong>【Foundry註記】</strong>', '此特性包含一項Active Effect，會自動提升你的移動速度。若你穿戴重甲，請停用快速移動的Active Effect。'],
}
supplements = []
for key, row in sheet['entries'].items():
    row['name'] = sections[key][0]
    plain = sections[key][1:]
    assert len(plain) + len(supplement_text.get(key, [])) == len(row['blocks']), key
    for block, text in zip(row['blocks'], plain):
        zh = text
        if key == 'Barbarian':
            if block['id'] in ['b0005','b0007','b0009','b0011','b0013','b0015']:
                zh = '<strong>' + zh + '</strong>'
            if block['id'] == 'b0010':
                zh = zh.replace('選擇2項：', '<em>選擇2項：</em>')
            if block['id'] == 'b0016':
                zh = zh.replace('選擇A或B：', '<em>選擇A或B：</em>')
                for name, target in [('巨斧','phbwepGreataxe00'),('手斧','phbwepHandaxe000'),('探索者套裝','phbagExplorersPa')]:
                    zh = zh.replace(name, '@UUID[Compendium.dnd-players-handbook.equipment.Item.' + target + ']{' + name + '}')
        if key == 'Rage' and block['id'] in ['b0004','b0005','b0006','b0007','b0008']:
            zh = re.sub(r'^【[^】]+】', lambda m: '<strong>' + m[0] + '</strong>', zh)
        if key == 'Danger Sense':
            zh = zh.replace('失能', '&amp;Reference[Incapacitated]{失能}')
        assert visible_text(zh) == visible_text(text), (key, block['id'])
        assert not compare_html(block['en'], zh), (key, block['id'], compare_html(block['en'], zh))
        block.update(zh=zh, source='draft', basis='')
    for block, zh in zip(row['blocks'][len(plain):], supplement_text.get(key, [])):
        block.update(zh=zh, source='supplement', basis='網頁原稿沒有Foundry註記；依本欄EN補翻。Active Effect保留英文依使用者裁定，其餘用語依terms、lang及現行PHB名稱。')
        supplements.append({'path':key+'/description/'+block['id'],'en':block['en'],'zh':visible_text(zh),'basis':block['basis']})

barb = sheet['entries']['Barbarian']
adv_titles = {'Rage Damage':'狂暴傷害','Weapon Masteries Known':'已知武器精通','Class Features':'職業特性','Primal Knowledge':'原初知識','Brutal Strike':'殘暴打擊','Saving Throws Proficiencies':'豁免檢定熟練','Skill Proficiencies':'技能熟練','Weapon Proficiencies':'武器熟練','Armor Training':'護甲訓練','Weapon Mastery':'武器精通','Rages':'狂暴'}
for key, row in barb['advancement'].items():
    row['title'] = adv_titles[key]
barb['advancement']['Primal Knowledge']['hint'] = sections['Primal Knowledge'][1]
barb['advancement']['Weapon Mastery']['hint'] = '你對武器的訓練使你能夠使用更多種武器的精通屬性。'

rage = sheet['entries']['Rage']
rage['activities']['Expend Rage']['name'] = '消耗狂暴使用次數'
rage['effects']['Rage']['name'] = '狂暴'
rage['effects']['Rage']['description'] = ''.join('<p>' + rage['blocks'][i]['zh'] + '</p>' for i in [3,4,5])
for key in ['Unarmored Defense','Primal Knowledge','Fast Movement','Feral Instinct']:
    sheet['entries'][key]['effects'][key]['name'] = sheet['entries'][key]['name']
sheet['entries']['Danger Sense']['effects']['Danger Sense'] = {
    'name':'危險感知', 'description':'<p>只要你未陷入&amp;Reference[Incapacitated]{失能}狀態，你的敏捷豁免檢定就具有優勢。</p>'}
sheet['entries']['Reckless Attack']['effects']['Reckless']['name'] = '魯莽'

en = read(ROOT / 'compendium/en/dnd-players-handbook/dnd-players-handbook.classes.json')['entries']
units = read(HERE / 'barbarian.weblate_units.json')['units']
def leaves(d, prefix=''):
    if isinstance(d, dict):
        for k,v in d.items():
            yield from leaves(v, prefix + '.' + k if prefix else k)
    elif isinstance(d, str):
        yield prefix, d
for key,row in sheet['entries'].items():
    for field in ['activities','effects','advancement']:
        for path,zh in leaves(row.get(field, {}), key+'.'+field):
            en_path = path.split('.')[2:]
            original = en[key][field]
            for p in en_path:
                original = original[p]
            current = units.get('entries.'+path, {}).get('target',[''])[0]
            supplements.append({'path':path,'en':original,'zh':zh,'basis': '沿用現行Weblate中文。' if current == zh else '介面欄位：依EN語意，沿用正文用詞、現行名稱與lang；未變更技術key。','current':current})
for key in ['Feral Instinct']:
    supplements.append({'path':key+'.name','en':key,'zh':sheet['entries'][key]['name'],'basis':'現行Weblate與全庫查無中文名稱，沿用原稿s2twp；待本批確認。'})

write(Path(str(prefix)+'.sheet.json'), sheet)
write(Path(str(prefix)+'.supplements.json'), supplements)

# A transparent normalized derivative works around draft_sections() not stripping
# unchanged enrichers. Only technical markup is removed; no Chinese is rewritten.
normalized = '\n\n'.join('### '+key+'\n'+'\n'.join(visible_text(line) for line in lines) for key,lines in sections.items())+'\n'
Path(str(prefix)+'.draft.validation.txt').write_text(normalized, encoding='utf-8')
print('Draft mapped without Chinese changes; supplements:', len(supplements))
