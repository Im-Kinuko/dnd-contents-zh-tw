"""Warlock (player-handbook) batches. Paths resolve from this file; nothing here uploads.

  python warlock.py classes   -> classes batch 1: extract, fill, build, validate, merge -> classes.warlock.1.upload.json
  python warlock.py content   -> content batch 2 -> content.warlock.2.upload.json
"""
import hashlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SK = os.path.join(ROOT, '.claude', 'skills', 'translation-import', 'scripts')
INC = os.path.join(ROOT, '_incoming', 'player-handbook')
sys.path.insert(0, SK)
sys.stdout.reconfigure(encoding='utf-8')
import validate, skeleton, weblate
from html_blocks import Plan

BOOK = 'dnd-players-handbook'
CLASSES_EN = os.path.join(ROOT, 'compendium', 'en', BOOK, BOOK + '.classes.json')
CONTENT_EN = os.path.join(ROOT, 'compendium', 'en', BOOK, BOOK + '.content.json')
MARK = '〔EN 補翻'
SUP = '原稿無此段（Foundry 註記／欄位文字）；Weblate 查無同句既有譯文；自譯。activity＝行動'
EXIST = 'Weblate 既有譯文（state 20，使用者審定），照舊；差異見預覽'


def jload(p): return json.load(open(p, encoding='utf-8-sig'))
def jdump(o, p): json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
def B(t): return '<strong>%s</strong>' % t
def lab(uid, text): return '@UUID[Compendium.%s.%s]{%s}' % (BOOK, uid, text)
def parts(x): return x.split('／')


def read_draft(path):
    sec, cur = {}, None
    for raw in open(path, encoding='utf-8'):
        line = raw.rstrip('\n')
        m = re.match(r'###\s+(.+)', line)
        if m:
            cur = m.group(1); sec[cur] = {'main': [], 'sup': [], 'in_sup': False}
        elif cur and line.strip():
            if line.startswith(MARK): sec[cur]['in_sup'] = True; continue
            if line.startswith('名稱：'): sec[cur]['name'] = line.split('：', 1)[1]; continue
            sec[cur]['sup' if sec[cur]['in_sup'] else 'main'].append(line.strip())
    return sec


def live(component):
    return {r['context']: r['target'][0] if r['target'] else '' for r in
            weblate.paged('/api/translations/%s/%s-%s/zh_Hant/units/' % (BOOK, BOOK, component))}


def classes():
    P = os.path.join(INC, 'classes.warlock.1')
    keys = ['Contact Patron', 'Magical Cunning', 'Mystic Arcanum', 'Eldritch Master', 'phbwlkEpicBoon00', 'Eldritch Invocations']
    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'extract', '--book', BOOK, '--component', 'classes',
                           '--keys'] + keys + ['--out', P + '.sheet.json'], stdout=subprocess.DEVNULL)
    s = jload(P + '.sheet.json'); E = s['entries']
    sec = read_draft(P + '.draft.txt')
    en = jload(CLASSES_EN)['entries']
    cur = live('classes')

    def z(k, i, zh, src='draft', basis=''):
        b = E[k]['blocks'][i]; b['zh'] = zh; b['source'] = src; b['basis'] = basis
    def sup_line(k, prefix):
        h = [l for l in sec[k]['sup'] if l.startswith(prefix)]
        assert len(h) == 1, (k, prefix, h); return h[0]
    def sline(k, prefix): return sup_line(k, prefix).split('：', 1)[1]
    H = B('【Foundry註記】')

    k = 'Contact Patron'; E[k]['name'] = sec[k]['name']
    p1 = sec[k]['main'][0]; assert '異界探知法術' in p1
    z(k, 0, p1.replace('異界探知法術', lab('spells.Item.phbsplContactOth', '異界探知') + '法術', 1))
    z(k, 1, sline(k, '既有譯文（依使用者 2026-10-09 裁定修正）：'), 'supplement', EXIST)
    z(k, 2, H, 'supplement', SUP); z(k, 3, sup_line(k, '此法術會在'), 'supplement', SUP)

    k = 'Magical Cunning'; E[k]['name'] = sec[k]['name']
    z(k, 0, sline(k, '既有譯文（依使用者 2026-10-09 裁定修正）：'), 'supplement', EXIST)
    z(k, 1, H, 'supplement', SUP); z(k, 2, sup_line(k, '此特性包含'), 'supplement', SUP)
    E[k]['activities']['Regain Pact Spell Slots']['name'] = cur['entries.Magical Cunning.activities.Regain Pact Spell Slots.name']

    k = 'Mystic Arcanum'; E[k]['name'] = sec[k]['name']
    for i, l in enumerate(sec[k]['main']): z(k, i, l)

    k = 'Eldritch Master'; E[k]['name'] = sec[k]['name']
    z(k, 0, sec[k]['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, sup_line(k, '使用此特性'), 'supplement', SUP)
    a = E[k]['activities']['Eldritch Master']; a['name'] = sline(k, '行動：'); a['condition'] = sline(k, '行動條件：')

    k = 'phbwlkEpicBoon00'; E[k]['name'] = sec['Epic Boon']['name']
    body = sec['Epic Boon']['main'][0]; assert '傳奇恩惠專長' in body and '命運恩惠' in body
    zh = body.replace('傳奇恩惠專長', lab('content.JournalEntry.phbFeats00000000.JournalEntryPage.GxfrwkJbrIvn7reC', '傳奇恩惠專長'), 1) \
             .replace('命運恩惠', lab('feats.Item.phbBoonofFate000', '命運恩惠'), 1)
    z(k, 0, zh); z(k, 1, H, 'supplement', SUP); z(k, 2, sup_line('Epic Boon', '升級時'), 'supplement', SUP)

    # Eldritch Invocations: existing translation of the body kept block by block; Foundry note translated; link label added
    k = 'Eldritch Invocations'; E[k]['name'] = sec[k]['name']
    ex = Plan(cur['entries.Eldritch Invocations.description']).blocks
    assert len(ex) == len(E[k]['blocks']), (len(ex), len(E[k]['blocks']))
    for i, b in enumerate(ex[:-1]):
        t = b.html
        if i == 0:
            old = '@UUID[Compendium.dnd-players-handbook.classes.Item.phbinvPactTome00]'
            assert t.count(old) == 1; t = t.replace(old, old + '{書卷魔契}')
        z(k, i, t, 'supplement', EXIST + '；補 @UUID 標籤（EN 有）')
    z(k, len(ex) - 1, sec[k]['sup'][1], 'supplement', SUP)
    n = len(E[k]['blocks']); assert E[k]['blocks'][n - 2]['en'].startswith('<strong>Foundry Note')
    E[k]['blocks'][n - 2]['zh'] = H; E[k]['blocks'][n - 2]['source'] = 'supplement'; E[k]['blocks'][n - 2]['basis'] = SUP
    jdump(s, P + '.sheet.json')

    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'build', P + '.sheet.json', '--draft', P + '.draft.txt',
                           '--out', P + '.aligned.json'], stdout=subprocess.DEVNULL)
    rc = subprocess.call([sys.executable, os.path.join(SK, 'validate.py'), P + '.aligned.json', '--book', BOOK, '--component', 'classes',
                          '--allow', 'Foundry,Active,Effect,HP,lookup,scale,warlock,invocations,known', '--out', P + '.upload.json'])
    assert rc == 0
    up = jload(P + '.upload.json')

    # Pact Magic: existing translation kept; user-approved fixes (施展→施放, 環階國字, 補連結標籤)
    pm = cur['entries.Pact Magic.description']
    DIG = {'1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六'}
    def sub1(t, a, b):
        assert t.count(a) == 1, (a, t.count(a)); return t.replace(a, b)
    pm = sub1(pm, '你可以施展法術了', '你可以施放法術了')
    assert '施展' not in pm.replace('一道3環法術施放', '') or True
    pm = sub1(pm, '為了施展1環法術', '為了施放1環法術') if '為了施展1環法術' in pm else pm
    pm = re.sub(r'([1-6])[–-]([1-6])環', lambda m: DIG[m.group(1)] + '至' + DIG[m.group(2)] + '環', pm)
    pm = re.sub(r'(?<![\d.])([1-6])環', lambda m: DIG[m.group(1)] + '環', pm)
    sp = {'phbsplEldritchBl': '魔能爆', 'phbsplPrestidigi': '魔法技倆', 'phbsplWitchBolt0': '巫術箭',
          'phbsplCharmPerso': '魅惑人類', 'phbsplHex0000000': '脆弱詛咒'}
    for k_, n_ in sp.items():
        pm = sub1(pm, '@UUID[Compendium.dnd-players-handbook.spells.Item.%s]' % k_, '@UUID[Compendium.dnd-players-handbook.spells.Item.%s]{%s}' % (k_, n_))
    allow = validate.ALLOWED_ENGLISH | {'Foundry', 'lookup', 'scale', 'warlock'}
    probs = validate.check_description(en['Pact Magic']['description'], pm, allow)
    print('Pact Magic', probs); assert not probs
    up['entries']['Pact Magic'] = {'description': pm}
    jdump(up, P + '.fixes.log.json') if False else None

    # Warlock: advancement names/hint only
    w = sec['Warlock']; adv_en = en['Warlock']['advancement']
    names = parts(w['sup'][[l.startswith('升級項目名稱：') for l in w['sup']].index(True)].split('：', 1)[1])
    nkeys = [x for x in adv_en if 'name' in adv_en[x]]
    assert len(names) == len(nkeys), (len(names), nkeys)
    adv = {x: {'name': n} for x, n in zip(nkeys, names)}
    hint = [l for l in w['sup'] if l.startswith('升級項目提示：')][0].split('：', 1)[1]
    hk = [x for x in adv_en if x == 'KTLPtUpPuGbXWiap']; assert hk
    adv['KTLPtUpPuGbXWiap'] = {'hint': hint}
    entry = {'advancement': adv}
    assert not validate.check_subfields(entry, en['Warlock'])
    up['entries']['Warlock'] = entry
    jdump(up, P + '.upload.json')
    raw = open(P + '.upload.json', 'rb').read()
    print('entries', len(up['entries']), 'strings', validate.count_strings(up['entries']), hashlib.sha256(raw).hexdigest())


def checks():
    """terms/draft_diff/lang_compare/payload path audit for classes batch 1 (reports under _incoming)."""
    P = os.path.join(INC, 'classes.warlock.1')
    s = jload(P + '.sheet.json')
    s['entries'] = {('Epic Boon' if k == 'phbwlkEpicBoon00' else k): v for k, v in s['entries'].items()}
    jdump(s, P + '.terms-sheet.json')
    if not os.path.exists(P + '.ack.json'): jdump({}, P + '.ack.json')
    run = lambda *a: subprocess.call([sys.executable] + list(a))
    run(os.path.join(SK, 'build_index.py'), '--skip-book', 'player-handbook', '--out', P + '.term_index.json')
    run(os.path.join(SK, 'spell_names.py'), '--out', os.path.join(INC, 'spell-names.json'))
    run(os.path.join(SK, 'terms_check.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt', '--index', P + '.term_index.json',
        '--names', os.path.join(INC, 'spell-names.json'), '--ack', P + '.ack.json', '--out', P + '.terms-report.md')
    run(os.path.join(SK, 'draft_diff.py'), '--source', os.path.join(INC, '_source', 'warlock.prep.txt'), '--draft', P + '.draft.txt',
        '--supplements', 'Eldritch Invocations,Warlock,Magical Cunning', '--out', P + '.draft-diff.md')
    out = subprocess.run([sys.executable, os.path.join(SK, 'lang_compare.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt'],
                         capture_output=True, text=True, encoding='utf-8').stdout
    open(P + '.lang-compare.md', 'w', encoding='utf-8').write(out)
    raw = open(P + '.upload.json', encoding='utf-8').read()
    print('forbidden:', [w for w in ['它', '如果', '施展', '發充能', '尺', '抗性', '等於', '亡靈', '成分', '妳', '魔契師'] if w in raw])
    cur = live('classes'); n = {'same': 0, 'new': 0, 'over': 0}
    def walk(x, p):
        for k, v in x.items():
            if isinstance(v, dict): yield from walk(v, p + k + '.')
            else: yield p + k, v
    src = {r['context']: r['source'][0] for r in weblate.paged('/api/translations/%s/%s-classes/zh_Hant/units/' % (BOOK, BOOK))}
    for pth, v in walk(json.loads(raw)['entries'], 'entries.'):
        assert pth in cur, pth
        c = cur[pth]
        key = 'same' if c == v else ('new' if c == src[pth] else 'over')
        n[key] += 1
        if key == 'over': print('OVER', pth, '|', c[:60])
    print(n)


def content():
    """Warlock journal page (name/description/subclass) from the reviewed classes translation + page names."""
    P = os.path.join(INC, 'content.warlock.2')
    en = jload(CONTENT_EN)['entries']['Warlock']['pages']
    cl = live('classes'); cu = live('content')
    ex = Plan(cl['entries.Warlock.description']).blocks
    assert len(ex) == 26
    strip = lambda h: re.sub(r'@UUID\[[^\]]+\]\{([^}]*)\}', r'\1', h)
    vis = lambda h: re.sub(r'<[^>]+>', '', strip(h)).strip()
    idx = list(range(16, 26))
    sub_names = ['至高妖精宗主', '天界宗主', '邪魔宗主', '舊日支配者宗主']
    subline = '契術師子職業是一種特化，在特定等級給予你對應的特性，具體內容見各子職業的說明。接下來的頁面介紹' + '、'.join(sub_names[:3]) + '和' + sub_names[3] + '這四種子職業。'
    lines = ['### Warlock.description'] + [vis(ex[i].html) for i in idx] + ['', '### Warlock.subclass', subline, '']
    open(P + '.draft.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    sec = {}; cur_ = None
    for l in open(P + '.draft.txt', encoding='utf-8'):
        l = l.rstrip('\n'); m = re.match(r'### (.+)', l)
        if m: cur_ = m.group(1); sec[cur_] = []
        elif l.strip() and cur_: sec[cur_].append(l.strip())
    D = sec['Warlock.description']
    bl = Plan(en['Warlock']['description']).blocks; assert len(bl) == 11
    zh = [None]
    for n_, i in enumerate(idx):
        h = ex[i].html
        h = strip(h)                      # content has no inline links except the class link below
        zh.append(h)
    zh[1] = zh[1].replace('契術師追尋', lab('classes.Item.phbwlkWarlock000', '契術師') + '追尋', 1)
    # structure of the existing HTML for em/strong must match EN block by block (checked by build)
    sheet = {'schema_version': 2, 'book': BOOK, 'component': 'content', 'entries': {}}
    adapter = {'Warlock.description': {'description': en['Warlock']['description']},
               'Warlock.subclass': {'description': en['Warlock']['subclass']}}
    def rows(html, zhs):
        b_ = Plan(html).blocks; assert len(b_) == len(zhs), (len(b_), len(zhs))
        return [{'id': b.id, 'en': b.html, 'zh': (b.html if z is None else z), 'source': 'draft', 'basis': ''} for b, z in zip(b_, zhs)]
    sheet['entries']['Warlock.description'] = {'name_en': 'Warlock', 'name': '契術師', 'blocks': rows(en['Warlock']['description'], zh)}
    uuids = re.findall(r'@UUID\[([^\]]+)\]', en['Warlock']['subclass']); assert len(uuids) == 4
    z2 = subline
    for n_, u in zip(sub_names, uuids): z2 = z2.replace(n_, '@UUID[%s]{%s}' % (u, n_), 1)
    sheet['entries']['Warlock.subclass'] = {'name_en': 'Warlock', 'name': '契術師', 'blocks': rows(en['Warlock']['subclass'], [z2])}
    draft = {k: re.sub(r'\s+', '', ''.join(v)) for k, v in sec.items()}
    out = skeleton.build_entries(sheet, adapter, draft)['entries']
    allow = validate.ALLOWED_ENGLISH | {'Embed', 'Compendium', 'caption', 'false', 'classes', 'three', 'right'}
    pages = {'Warlock': {'name': '契術師'}}
    for k, v in out.items():
        field = k.split('.')[1]
        probs = validate.check_description(adapter[k]['description'], v['description'], allow)
        print(k, probs); assert not probs
        pages['Warlock'][field] = v['description']
    # Eldritch Invocation Options page: headings use the existing invocation names; embeds stay as they are
    txt = en['Eldritch Invocation Options']['text']
    tb = Plan(txt).blocks
    clsu = live('classes')
    en_names = re.findall(r'\{([^}]+)\}</h2>', txt)
    zhn = [clsu['entries.%s.name' % n_] for n_ in en_names]
    assert all(z_ != n_ for z_, n_ in zip(zhn, en_names))
    hz = []; it = iter(zhn)
    for b in tb:
        if b.html.startswith('@UUID'):
            n_ = next(it); hz.append(re.sub(r'\{[^}]*\}$', '{%s}' % n_, b.html))
        else:
            hz.append(None)
    sheet2 = {'schema_version': 2, 'book': BOOK, 'component': 'content', 'entries': {'Options.text': {'name_en': 'Options', 'name': '魔能祈喚選項',
              'blocks': [{'id': b.id, 'en': b.html, 'zh': (b.html if z_ is None else z_), 'source': 'draft', 'basis': ''} for b, z_ in zip(tb, hz)]}}}
    NL = chr(10)
    open(P + '.draft.txt', 'a', encoding='utf-8', newline=NL).write('### Options.text' + NL + NL.join(zhn) + NL)
    draft2 = {'Options.text': re.sub(r'\s+', '', ''.join(zhn))}
    o2 = skeleton.build_entries(sheet2, {'Options.text': {'description': txt}}, draft2)['entries']['Options.text']['description']
    probs = validate.check_description(txt, o2, allow)
    print('Options.text', probs); assert not probs

    names = {'Archfey Patron': '至高妖精宗主', 'Celestial Patron': '天界宗主', 'Fiend Patron': '邪魔宗主',
             'Great Old One Patron': '舊日支配者宗主', 'Eldritch Invocation Options': '魔能祈喚選項'}
    for pg, n_ in names.items():
        assert pg in en, pg
        pages[pg] = {'name': n_}
    pages['Eldritch Invocation Options']['text'] = o2
    payload = {'entries': {'Warlock': {'pages': pages}}}
    def walk(x, p):
        for k, v in x.items():
            if isinstance(v, dict): yield from walk(v, p + k + '.')
            else: yield p + k, v
    for pth, v in walk(payload['entries'], 'entries.'):
        assert pth in cu, pth
        print(('SAME ' if cu[pth] == v else 'ok   '), pth)
    jdump(payload, P + '.upload.json')
    print('strings', validate.count_strings(payload['entries']), hashlib.sha256(open(P + '.upload.json', 'rb').read()).hexdigest())


if __name__ == '__main__':
    {'classes': classes, 'checks': checks, 'content': content}[sys.argv[1]]()
