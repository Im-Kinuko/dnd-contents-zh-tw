"""查 lang 技能名與既有「升級效應」寫法。用法：python scripts/aa_lookup2.py out.txt"""
import json, re, sys, glob
l = json.load(open('lang/zh-tw.json', encoding='utf8'))
out = []
for k, v in l.items():
    if re.match(r'DND5E\.Skill[A-Z][a-z]{2}$', k) or k in ('DND5E.AbilityInt', 'DND5E.AbilityCon', 'DND5E.AbilityWis', 'DND5E.AbilityDex', 'DND5E.AbilityStr', 'DND5E.AbilityCha'):
        out.append('%s %s' % (k, v))
for k, v in l.items():
    if isinstance(v, str) and re.search(r'Passive|被動|penalty|Penalty', k + v) and len(v) < 30:
        out.append('%s %s' % (k, v))
pat = re.compile(r'At Higher Levels')
cnt = {}
for f in glob.glob('compendium/zh-tw/**/*.json', recursive=True):
    t = open(f, encoding='utf8').read()
    for m in re.finditer(r'<strong>(【[^】]{1,12}】)</strong>', t):
        s = m.group(1)
        if any(w in s for w in ('升', '等級', '提升', '更高')):
            cnt[s] = cnt.get(s, 0) + 1
out.append('升級類小標: ' + json.dumps(cnt, ensure_ascii=False))
for w in ['減值', '劣勢', '懲罰', '被動察覺', '被動感知', '半身掩', '四分之三掩', '借機', '藉機', '射程', '光環', '發散']:
    n = 0
    for f in glob.glob('compendium/zh-tw/**/*.json', recursive=True):
        n += open(f, encoding='utf8').read().count(w)
    out.append('%s %d' % (w, n))
open(sys.argv[1], 'w', encoding='utf8').write('\n'.join(out))
