"""查現有 zh-tw 條目與術語索引。用法：python scripts/aa_lookup.py out.txt"""
import json, re, sys
book = 'dnd-arcana-unleashed'
keys = ["Arcane Archer", "Arcane Archer Lore", "Arcane Shot", "Curving Shot", "Magical Ammunition", "Ever-Ready Shot",
        "Indomitable Teleport", "Masterful Shots", "Banishing Shot", "Beguiling Shot", "Bursting Shot", "Enfeebling Shot",
        "Grasping Shot", "Piercing Shot", "Seeking Shot", "Shadow Shot"]
z = json.load(open('compendium/zh-tw/%s/%s.subclasses.json' % (book, book), encoding='utf8'))
out = []
for k in keys:
    v = z['entries'].get(k)
    if not v:
        out.append('## %s : (無)' % k); continue
    out.append('## %s => %s' % (k, v.get('name')))
    out.append('  desc: ' + re.sub(r'</p><p>', '\n        ', re.sub(r'<(?!/p><p)[^>]+>', '', v.get('description', '')).replace('</p><p>', '</p><p>')))
    for f in ('activities', 'effects', 'advancement'):
        if v.get(f): out.append('  %s: %s' % (f, json.dumps(v[f], ensure_ascii=False)))
out.append('\n== folders ==')
out.append(json.dumps(z.get('folders'), ensure_ascii=False))
idx = json.load(open('_incoming/dnd-arcana-unleashed/_done/class.term_index.json', encoding='utf8'))
out.append('\n== terms ==')
for k, v in idx['terms'].items():
    out.append('%s => %s' % (k, v))
out.append('\n== entry_names (selected) ==')
want = ['druidcraft', 'prestidigitation', 'second wind', 'indomitable', 'opportunity', 'darkness', 'fighter', 'psychic', 'force', 'necrotic', 'poisoned', 'charmed', 'restrained', 'blinded', 'incapacitated', 'half cover', 'three-quarters', 'ammunition', 'arcana', 'nature', 'initiative', 'cantrip']
for k, v in idx['entry_names'].items():
    if any(w in k.lower() for w in want):
        out.append('%s => %s' % (k, list(v.keys()) if isinstance(v, dict) else v))
open(sys.argv[1], 'w', encoding='utf8').write('\n'.join(out))
