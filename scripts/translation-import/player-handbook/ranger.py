"""Ranger (player-handbook) batches. Paths resolve from this file; nothing here uploads.

  python ranger.py prep      -> source conversion/headings, term index
  python ranger.py classes   -> classes.ranger.1.upload.json
  python ranger.py checks    -> terms / draft_diff / lang_compare / payload path audit
  python ranger.py content   -> content.ranger.2.upload.json
"""
import hashlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from warlock import (ROOT, SK, INC, BOOK, CLASSES_EN, CONTENT_EN, SUP, EXIST, jload, jdump, B, lab, parts, read_draft, live,
                     validate, skeleton, weblate, Plan)
from sorcerer import DIG, fix_labeled

NEW_KEYS = ['Favored Enemy', 'Roving', 'phbrgrExpertise0', 'Tireless', 'Relentless Hunter', "Nature's Veil", 'Precise Hunter',
            'Feral Senses', 'Foe Slayer', 'phbrgrEpicBoon00']
KEEP_KEYS = ['Deft Explorer', 'phbrgrFightingSt']
DRAFT_NAME = {'phbrgrExpertise0': 'Expertise', 'phbrgrEpicBoon00': 'Epic Boon', 'phbrgrFightingSt': 'Fighting Style'}
FIX = {'phbrgrFightingSt': [('以下選項', '下列選項')]}
P = os.path.join(INC, 'classes.ranger.1')
NL = chr(10)


def prep():
    import opencc
    conv = opencc.OpenCC('s2twp').convert(open(os.path.join(INC, 'ranger.txt'), encoding='utf-8').read())
    open(os.path.join(INC, '_source', 'ranger.s2twp.txt'), 'w', encoding='utf-8', newline='').write(conv)
    L = conv.replace(chr(13), '').split(NL)
    def r(a, b): return [x for x in L[a - 1:b] if x.strip()]
    secs = [('宿敵 Favored Enemy', r(66, 67)), ('越野 Roving', r(92, 92)), ('專精 Expertise', r(95, 95)), ('不知疲倦 Tireless', r(98, 100)),
            ('永恆追獵 Relentless Hunter', r(103, 103)), ("自然面紗 Nature's Veil", r(106, 107)), ('致命獵殺 Precise Hunter', r(110, 110)),
            ('野性感官 Feral Senses', r(113, 113)), ('屠滅眾敵 Foe Slayer', r(119, 119)), ('傳奇恩惠 Epic Boon', r(116, 116)),
            ('熟練探險家 Deft Explorer', r(74, 76)), ('戰鬥風格 Fighting Style', r(79, 80)), ('遊俠 Ranger', r(83, 83))]
    out = []
    for h, ls in secs: out += [h] + ls + ['']
    open(os.path.join(INC, '_source', 'ranger.prep.txt'), 'w', encoding='utf-8', newline=NL).write(NL.join(out))
    subprocess.call([sys.executable, os.path.join(SK, 'build_index.py'), '--skip-book', 'player-handbook', '--out', P + '.term_index.json'])


def classes():
    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'extract', '--book', BOOK, '--component', 'classes', '--keys']
                          + NEW_KEYS + KEEP_KEYS + ['--out', P + '.sheet.json'], stdout=subprocess.DEVNULL)
    s = jload(P + '.sheet.json'); E = s['entries']
    sec = read_draft(P + '.draft.txt')
    en = jload(CLASSES_EN)['entries']
    cur = live('classes')
    H = B('【Foundry註記】')
    def D(k): return sec.get(k) or sec[DRAFT_NAME[k]]
    def z(k, i, zh, src='draft', basis=''):
        b = E[k]['blocks'][i]; b['zh'] = zh; b['source'] = src; b['basis'] = basis
    def sline(k, prefix):
        h = [l for l in D(k)['sup'] if l.startswith(prefix)]; assert len(h) == 1, (k, prefix); return h[0].split('：', 1)[1]
    def nm(k): E[k]['name'] = D(k)['name']
    def run_in(line):
        m = re.match(r'(【[^】]+】)(.*)', line, re.S); return B(m.group(1)) + m.group(2)
    def bold(line, phrase):
        assert phrase in line, (line, phrase); return line.replace(phrase, B(phrase), 1)
    def notes_of(k):
        return [l for l in D(k)['sup'][1:] if not l.startswith(('行動：', '效果：', '行動條件：', '升級項目名稱：'))]
    def sn(k):
        return jload(os.path.join(INC, 'spell-names.json'))

    SPELL = lambda label, zhn, uid: '@UUID[Compendium.dnd-players-handbook.spells.Item.%s]{%s}' % (uid, zhn)
    uid_hm = re.findall(r'@UUID\[[^\]]*Hunter[^\]]*\]|@UUID\[[^\]]+\]', en['Favored Enemy']['description'])[0]

    # --- Favored Enemy
    k = 'Favored Enemy'; nm(k); M = D(k)['main']
    z(k, 0, M[0].replace('獵人印記法術', uid_hm + '{獵人印記}法術', 1)); z(k, 1, M[1])
    # blocks: the EN description has 2 paragraphs plus the Foundry note that the EN template lacks -> check
    print('Favored Enemy EN blocks', len(E[k]['blocks']))
    E[k]['advancement']['Favored Enemy']['name'] = sline(k, '升級項目名稱：')
    # --- Roving
    k = 'Roving'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, notes_of(k)[0], 'supplement', SUP)
    E[k]['effects']['Roving']['name'] = sline(k, '效果：')
    # --- Expertise
    k = 'phbrgrExpertise0'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, notes_of(k)[0], 'supplement', SUP)
    # --- Tireless
    k = 'Tireless'; nm(k); M = D(k)['main']
    z(k, 0, M[0]); z(k, 1, run_in(M[1])); z(k, 2, run_in(M[2])); z(k, 3, H, 'supplement', SUP)
    n = notes_of(k); z(k, 4, bold(n[0], '臨時生命值'), 'supplement', SUP); z(k, 5, bold(n[1], '減少力竭'), 'supplement', SUP)
    a = E[k]['activities']; assert list(a) == ['Temporary Hit Points', 'Decrease Exhaustion']
    for key, nn in zip(a, parts(sline(k, '行動：'))): a[key]['name'] = nn
    a['Decrease Exhaustion']['condition'] = sline(k, '行動條件：')
    # --- Relentless Hunter / Precise Hunter
    k = 'Relentless Hunter'; nm(k); z(k, 0, D(k)['main'][0])
    k = 'Precise Hunter'; nm(k); z(k, 0, D(k)['main'][0])
    # --- Nature's Veil
    k = "Nature's Veil"; nm(k); M = D(k)['main']
    z(k, 0, M[0]); z(k, 1, M[1]); z(k, 2, H, 'supplement', SUP); z(k, 3, notes_of(k)[0], 'supplement', SUP)
    E[k]['activities']['Veil']['name'] = sline(k, '行動：'); E[k]['effects']['Veiled']['name'] = sline(k, '效果：')
    # --- Feral Senses
    k = 'Feral Senses'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, notes_of(k)[0], 'supplement', SUP)
    E[k]['effects']['Feral Senses']['name'] = sline(k, '效果：')
    # --- Foe Slayer
    k = 'Foe Slayer'; nm(k); body = D(k)['main'][0]
    assert '獵人印記' in body
    z(k, 0, body.replace('獵人印記', uid_hm.replace(uid_hm, re.findall(r'@UUID\[[^\]]+\]', en[k]['description'])[0]) + '{獵人印記}', 1))
    z(k, 1, H, 'supplement', SUP)
    nt = notes_of(k)[0]; assert '獵人印記法術' in nt and '額外標記傷害行動' in nt
    nt = nt.replace('獵人印記法術', '<em>獵人印記</em>法術', 1).replace('額外標記傷害行動', '<strong>額外標記傷害</strong>行動', 1)
    z(k, 2, nt, 'supplement', SUP)
    E[k]['activities']["Improved Hunter's Mark Damage"]['name'] = sline(k, '行動：')
    # --- Epic Boon
    k = 'phbrgrEpicBoon00'; nm(k); body = D(k)['main'][0]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en[k]['description']); assert len(uu) == 2
    z(k, 0, body.replace('傳奇恩惠專長', '@UUID[%s]{傳奇恩惠專長}' % uu[0], 1).replace('次元旅行恩惠', '@UUID[%s]{次元旅行恩惠}' % uu[1], 1))
    z(k, 1, H, 'supplement', SUP); z(k, 2, notes_of(k)[0], 'supplement', SUP)
    # --- existing translations kept
    for k in KEEP_KEYS:
        nm(k)
        ex = Plan(cur['entries.%s.description' % k]).blocks
        bl = E[k]['blocks']; assert len(ex) == len(bl), (k, len(ex), len(bl))
        hi = next((i for i, b in enumerate(bl) if b['en'].startswith('<strong>Foundry')), len(bl))
        htmls = [b.html for b in ex]
        for a_, b_ in FIX.get(k, []):
            assert sum(h.count(a_) for h in htmls) == 1, (k, a_)
            htmls = [h.replace(a_, b_) for h in htmls]
        for i in range(hi): z(k, i, htmls[i], 'supplement', EXIST + ('；使用者裁定修正' if k in FIX else ''))
        if hi < len(bl):
            z(k, hi, H, 'supplement', SUP); z(k, hi + 1, notes_of(k)[0], 'supplement', SUP)
    jdump(s, P + '.sheet.json')

    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'build', P + '.sheet.json', '--draft', P + '.draft.txt',
                           '--out', P + '.aligned.json'], stdout=subprocess.DEVNULL)
    rc = subprocess.call([sys.executable, os.path.join(SK, 'validate.py'), P + '.aligned.json', '--book', BOOK, '--component', 'classes',
                          '--allow', 'Foundry,Active,Effect,lookup,scale,ranger', '--out', P + '.upload.json'])
    assert rc == 0
    up = jload(P + '.upload.json')['entries']
    w = sec['Ranger']; adv_en = en['Ranger']['advancement']
    names = parts([l for l in w['sup'] if l.startswith('升級項目名稱：')][0].split('：', 1)[1])
    nkeys = [x for x in adv_en if 'name' in adv_en[x]]
    assert len(names) == len(nkeys), (len(names), nkeys)
    entry = {'advancement': {x: {'name': n} for x, n in zip(nkeys, names)}}
    assert not validate.check_subfields(entry, en['Ranger'])
    entry['description'] = fix_labeled(cur, en, 'Ranger', [('施展', '施放'), ('以下', '下列')])
    up['Ranger'] = entry
    up['phbrgrSpellcasti'] = {'description': fix_labeled(cur, en, 'phbrgrSpellcasti', [('以下資訊', '下列資訊')])}
    jdump({'entries': up}, P + '.all.json')
    b1 = {k_: v for k_, v in up.items() if k_ in NEW_KEYS}; b2 = {k_: v for k_, v in up.items() if k_ not in NEW_KEYS}
    for n_, d_ in (('1', b1), ('2', b2)):
        f_ = os.path.join(INC, 'classes.ranger.%s.upload.json' % n_)
        jdump({'entries': d_}, f_)
        print('batch', n_, len(d_), 'entries', validate.count_strings(d_), 'strings', hashlib.sha256(open(f_, 'rb').read()).hexdigest())


def checks():
    s = jload(P + '.sheet.json')
    s['entries'] = {(DRAFT_NAME.get(k, k)): v for k, v in s['entries'].items() if k not in KEEP_KEYS}
    jdump(s, P + '.terms-sheet.json')
    if not os.path.exists(P + '.ack.json'): jdump({}, P + '.ack.json')
    run = lambda *a: subprocess.call([sys.executable] + list(a))
    run(os.path.join(SK, 'spell_names.py'), '--out', os.path.join(INC, 'spell-names.json'))
    run(os.path.join(SK, 'terms_check.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt', '--index', P + '.term_index.json',
        '--names', os.path.join(INC, 'spell-names.json'), '--ack', P + '.ack.json', '--out', P + '.terms-report.md')
    run(os.path.join(SK, 'draft_diff.py'), '--source', os.path.join(INC, '_source', 'ranger.prep.txt'), '--draft', P + '.draft.txt',
        '--supplements', 'Deft Explorer,Fighting Style,Ranger', '--out', P + '.draft-diff.md')
    out = subprocess.run([sys.executable, os.path.join(SK, 'lang_compare.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt'],
                         capture_output=True, text=True, encoding='utf-8').stdout
    open(P + '.lang-compare.md', 'w', encoding='utf-8').write(out)
    cur = live('classes')
    src = {r['context']: r['source'][0] for r in weblate.paged('/api/translations/%s/%s-classes/zh_Hant/units/' % (BOOK, BOOK))}
    def walk(x, p):
        for k, v in x.items():
            if isinstance(v, dict): yield from walk(v, p + k + '.')
            else: yield p + k, v
    raw = open(P + '.all.json', encoding='utf-8').read()
    print('forbidden:', [w for w in ['它', '如果', '施展', '發充能', '尺', '抗性', '等於', '亡靈', '成分', '妳', '倒地', '無需', '以下', '法術槽'] if w in raw])
    c = {'same': 0, 'new': 0, 'over': 0}
    for pth, v in walk(json.loads(raw)['entries'], 'entries.'):
        assert pth in cur, pth
        key = 'same' if cur[pth] == v else ('new' if cur[pth] == src[pth] else 'over')
        c[key] += 1
        if key == 'over': print('  OVER', pth, '|', cur[pth][:50].replace(NL, ' '))
    print(c)


def content():
    C = os.path.join(INC, 'content.ranger.2')
    en = jload(CONTENT_EN)['entries']['Ranger']['pages']
    cl = live('classes'); cu = live('content')
    ex = Plan(cl['entries.Ranger.description']).blocks
    assert len(ex) == 25, len(ex)
    strip = lambda h: re.sub(r'@UUID\[[^\]]+\]\{([^}]*)\}', lambda m: m.group(1), h)
    vis = lambda h: re.sub(r'<[^>]+>', '', strip(h)).strip()
    idx = list(range(16, 25))
    subs = ['Beast Master', 'Fey Wanderer', 'Gloom Stalker', 'Hunter']
    sub_names = [cl['entries.%s.name' % k_] for k_ in subs]
    subline = '遊俠子職業是一種特化，在特定等級給予你對應的特性，具體內容見各子職業的說明。接下來的頁面介紹' + '、'.join(sub_names[:3]) + '和' + sub_names[3] + '這四種子職業。'
    lines = ['### Ranger.description'] + [vis(ex[i].html) for i in idx] + ['', '### Ranger.subclass', subline, '']
    open(C + '.draft.txt', 'w', encoding='utf-8', newline=NL).write(NL.join(lines))
    sec = {}; cur_ = None
    for l in open(C + '.draft.txt', encoding='utf-8'):
        l = l.rstrip(NL); m = re.match(r'### (.+)', l)
        if m: cur_ = m.group(1); sec[cur_] = []
        elif l.strip() and cur_: sec[cur_].append(l.strip())
    zh = [None, None] + [strip(ex[i].html) for i in idx]
    zh = [x.replace('施展', '施放') if x else x for x in zh]
    zh[2] = zh[2].replace('遊俠', lab('classes.Item.phbrgrRanger0000', '遊俠'), 1)
    sec['Ranger.description'] = [x.replace('施展', '施放') for x in sec['Ranger.description']]
    def rows(html, zhs):
        b_ = Plan(html).blocks; assert len(b_) == len(zhs), (len(b_), len(zhs))
        return [{'id': b.id, 'en': b.html, 'zh': (b.html if z is None else z), 'source': 'draft', 'basis': ''} for b, z in zip(b_, zhs)]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en['Ranger']['subclass']); assert len(uu) == 4, uu
    z2 = subline
    for n_, u in zip(sub_names, uu): z2 = z2.replace(n_, '@UUID[%s]{%s}' % (u, n_), 1)
    nsub = len(Plan(en['Ranger']['subclass']).blocks)
    sheet = {'schema_version': 2, 'book': BOOK, 'component': 'content', 'entries': {
        'Ranger.description': {'name_en': 'Ranger', 'name': '遊俠', 'blocks': rows(en['Ranger']['description'], zh)},
        'Ranger.subclass': {'name_en': 'Ranger', 'name': '遊俠', 'blocks': rows(en['Ranger']['subclass'], [z2] + [None] * (nsub - 1))}}}
    adapter = {'Ranger.description': {'description': en['Ranger']['description']}, 'Ranger.subclass': {'description': en['Ranger']['subclass']}}
    draft = {k_: re.sub(r'\s+', '', ''.join(v)) for k_, v in sec.items()}
    out = skeleton.build_entries(sheet, adapter, draft)['entries']
    allow = validate.ALLOWED_ENGLISH | {'Embed', 'Compendium', 'caption', 'false', 'classes', 'three', 'right'}
    pages = {'Ranger': {'name': '遊俠'}}
    for k_, v in out.items():
        probs = validate.check_description(adapter[k_]['description'], v['description'], allow)
        print(k_, probs); assert not probs
        pages['Ranger'][k_.split('.')[1]] = v['description']
    for pg, n_ in zip(subs, sub_names):
        assert pg in en; pages[pg] = {'name': n_}
    payload = {'entries': {'Ranger': {'pages': pages}}}
    def walk(x, p_):
        for k_, v in x.items():
            if isinstance(v, dict): yield from walk(v, p_ + k_ + '.')
            else: yield p_ + k_, v
    for pth, v in walk(payload['entries'], 'entries.'):
        assert pth in cu, pth
        print(('SAME ' if cu[pth] == v else 'ok   '), pth)
    jdump(payload, C + '.upload.json')
    print('strings', validate.count_strings(payload['entries']), hashlib.sha256(open(C + '.upload.json', 'rb').read()).hexdigest())


if __name__ == '__main__':
    {'prep': prep, 'classes': classes, 'checks': checks, 'content': content}[sys.argv[1]]()
