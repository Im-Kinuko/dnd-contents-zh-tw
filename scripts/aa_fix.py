import json
import re

# Fix draft
with open(r'd:\TRPG\D&D\Service\dnd-contents-zh-tw\_incoming\dnd-arcana-unleashed\arcane-archer.draft.txt', 'r', encoding='utf-8') as f:
    text = f.read()

new_text = re.sub(r'## (.*?) => (.*)', r'### \1', text)

with open(r'd:\TRPG\D&D\Service\dnd-contents-zh-tw\_incoming\dnd-arcana-unleashed\arcane-archer.draft.txt', 'w', encoding='utf-8') as f:
    f.write(new_text)

# Fill sheet names
with open(r'd:\TRPG\D&D\Service\dnd-contents-zh-tw\_incoming\dnd-arcana-unleashed\arcane-archer.sheet.json', 'r', encoding='utf-8') as f:
    sheet = json.load(f)

# Extract mappings from old draft text
names = {}
for line in text.split('\n'):
    m = re.match(r'## (.*?) => (.*)', line)
    if m:
        names[m.group(1)] = m.group(2)

for key, entry in sheet['entries'].items():
    if key in names:
        entry['name'] = names[key]
    else:
        entry['name'] = "Name"

with open(r'd:\TRPG\D&D\Service\dnd-contents-zh-tw\_incoming\dnd-arcana-unleashed\arcane-archer.sheet.json', 'w', encoding='utf-8') as f:
    json.dump(sheet, f, ensure_ascii=False, indent=1)

print("Done")
