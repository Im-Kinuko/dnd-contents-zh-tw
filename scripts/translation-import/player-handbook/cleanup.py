"""Tidy `_incoming/player-handbook`: keep sources, drafts, previews/reports and `remaining` notes; drop regenerable dumps.

  python cleanup.py            # dry run: list what would be moved / deleted
  python cleanup.py --apply    # do it

Rules
- `_done/**`: keep *.md, *.draft.txt, *.remaining.txt, user source *.txt (not s2twp / log / validation / inventory / status /
  suggestions / segmented / unmapped / prior); every *.py is MOVED to scripts/translation-import/player-handbook/history/;
  everything else (json, html, caches) is deleted.
- `_source/`: derived conversions (`X.prep` / `X.s2twp`) are regenerable with `<class>.py prep`; deleted except the condition job.
- root: tool caches (term indexes, weblate dumps, spell-names, ack, terms reports, sheets) are deleted; user sources, *.remaining.txt,
  index notes, `subclasses/`, `_terms/`, `origins-restore/` and the `content.condition.*` job files are left alone.
- `_web/`: web extracts of finished barbarian work are deleted.
"""
import os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
INC = os.path.join(ROOT, '_incoming', 'player-handbook')
HIST = os.path.join(HERE, 'history')
APPLY = '--apply' in sys.argv
BAD_TXT = re.compile(r's2twp|\.log\.|validation|inventory|status|suggestions|segmented|unmapped|prior|\.prep\.')
ROOT_DELETE = {'ack.json', 'barbarian.equipment_names.json', 'barbarian.source.s2twp.txt', 'barbarian.term_index.json',
               'barbarian.weblate_units.json', 'classes.all_units.json', 'spell-names.json', 'terms-report.md', 'test_sheet.json'}

moves, deletes, kept = [], [], 0
def plan_done():
    global kept
    for dp, _, fs in os.walk(os.path.join(INC, '_done')):
        for f in fs:
            p = os.path.join(dp, f)
            if f.endswith('.py'): moves.append(p)
            elif f.endswith('.md') or f.endswith('.draft.txt') or f.endswith('.remaining.txt'): kept += 1
            elif f.endswith('.txt') and not BAD_TXT.search(f): kept += 1
            else: deletes.append(p)
def plan_rest():
    src = os.path.join(INC, '_source')
    for f in os.listdir(src):
        if not f.startswith('content.condition'): deletes.append(os.path.join(src, f))
    for f in os.listdir(INC):
        p = os.path.join(INC, f)
        if os.path.isfile(p) and (f in ROOT_DELETE or (re.match(r'(classes|content)\.[a-z\-]+\.\d+\.(sheet|aligned|upload|term_index|terms-sheet|all)\.json$', f))):
            deletes.append(p)
    web = os.path.join(INC, '_web')
    if os.path.isdir(web): deletes.append(web)

plan_done(); plan_rest()
size = lambda p: sum(os.path.getsize(os.path.join(a, b)) for a, _, c in os.walk(p) for b in c) if os.path.isdir(p) else os.path.getsize(p)
print('move scripts :', len(moves), '->', os.path.relpath(HIST, ROOT))
print('delete       :', len(deletes), 'items, %.1f MB' % (sum(size(p) for p in deletes) / 1e6))
print('kept in _done:', kept)
if not APPLY:
    for p in moves[:20]: print('  move  ', os.path.relpath(p, INC))
    print('(dry run; pass --apply)'); sys.exit(0)
os.makedirs(HIST, exist_ok=True)
for p in moves:
    dest = os.path.join(HIST, os.path.relpath(p, os.path.join(INC, '_done')).replace(os.sep, '__'))
    shutil.move(p, dest)
for p in deletes:
    if os.path.isdir(p): shutil.rmtree(p, ignore_errors=True)
    elif os.path.exists(p): os.remove(p)
for dp, ds, fs in os.walk(os.path.join(INC, '_done'), topdown=False):
    if not os.listdir(dp): os.rmdir(dp)
print('done')
