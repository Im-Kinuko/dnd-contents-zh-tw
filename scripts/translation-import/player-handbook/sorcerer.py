"""Sorcerer (player-handbook) batches. Paths resolve from this file; nothing here uploads.

  python sorcerer.py prep      -> source conversion/headings, term index
  python sorcerer.py classes   -> classes.sorcerer.1.upload.json
  python sorcerer.py checks    -> terms / draft_diff / lang_compare / payload path audit
  python sorcerer.py content   -> content.sorcerer.2.upload.json
"""
import hashlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from warlock import (ROOT, SK, INC, BOOK, CLASSES_EN, CONTENT_EN, SUP, EXIST, jload, jdump, B, lab, parts, read_draft, live,
                     validate, skeleton, weblate, Plan)

NEW_KEYS = ['Sorcery Incarnate', 'Arcane Apotheosis', 'phbscrEpicBoon00']
KEEP_KEYS = ['Innate Sorcery', 'Font of Magic', 'Metamagic', 'Sorcerous Restoration']
DRAFT_NAME = {'phbscrEpicBoon00': 'Epic Boon'}
P = os.path.join(INC, 'classes.sorcerer.1')
NL = chr(10)


def prep():
    import opencc
    conv = opencc.OpenCC('s2twp').convert(open(os.path.join(INC, 'sorcerer.txt'), encoding='utf-8').read())
    open(os.path.join(INC, '_source', 'sorcerer.s2twp.txt'), 'w', encoding='utf-8', newline='').write(conv)
    L = conv.replace(chr(13), '').split(NL)
    def r(a, b): return [x for x in L[a - 1:b] if x.strip()]
    secs = [('術法化身 Sorcery Incarnate', r(136, 137)), ('奧術化神 Arcane Apotheosis', r(143, 143)), ('傳奇恩惠 Epic Boon', r(140, 140)),
            ('先天術法 Innate Sorcery', r(68, 72)), ('魔力泉湧 Font of Magic', r(75, 80)), ('超魔法 Metamagic', r(121, 123)),
            ('術法復甦 Sorcerous Restoration', r(132, 133)), ('術士 Sorcerer', r(126, 126))]
    out = []
    for h, ls in secs: out += [h] + ls + ['']
    open(os.path.join(INC, '_source', 'sorcerer.prep.txt'), 'w', encoding='utf-8', newline=NL).write(NL.join(out))
    subprocess.call([sys.executable, os.path.join(SK, 'build_index.py'), '--skip-book', 'player-handbook', '--out', P + '.term_index.json'])


DIG = {'1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'}
FIX = {'Innate Sorcery': [('某個奇怪事件在你身上', '你過去的某個事件在你身上')],
       'Font of Magic': [('啟用以下選項', '啟用下列選項'), ('你可以創造的不高於5環的法術位', '你可以創造環階不高於五環的法術位')],
       'Metamagic': [('你獲得2個超魔法選項中你所選擇的超魔法選項。', '你從「超魔法選項」中選擇並獲得兩個超魔法選項。')]}


def fix_labeled(cur, en, key, repl):
    """Existing description with user-approved fixes, 環階 digits→國字 and {labels} for unlabeled spell/equipment links."""
    t = cur['entries.%s.description' % key]
    for a, b in repl:
        assert t.count(a) == 1, (a, t.count(a)); t = t.replace(a, b)
    t = re.sub(r'(?<![\d.])([1-9])環', lambda m: DIG[m.group(1)] + '環', t)
    sn = jload(os.path.join(INC, 'spell-names.json'))
    eq = {}
    for r in weblate.paged('/api/translations/%s/%s-equipment/zh_Hant/units/' % (BOOK, BOOK)):
        if r['context'].endswith('.name'): eq[r['context'][len('entries.'):-len('.name')].lower()] = r['target'][0]
    for uid, label in re.findall(r'@UUID\[([^\]]+)\]\{([^}]*)\}', en[key]['description']):
        old = '@UUID[%s]' % uid
        if not re.search(re.escape(old) + r'(?!\{)', t): continue   # absent or already labeled
        label = label.replace(chr(173), '')
        if label.lower() in {'ranger spell list': 1}: zh = '遊俠法術列表'
        elif 'spells.Item' in uid: zh = sn[label]
        else:
            l = label.lower()
            zh = eq.get(l) or eq.get(l.rstrip('s')) or eq.get(l.replace('’', "'"))
            zh = zh or {'arcane focus': '奧術法器'}.get(l)
            zh = zh or next((v_ for k_, v_ in eq.items() if k_.startswith(l + ' (')), None)
            if not zh: print('missing equipment name', label, [k_ for k_ in eq if l[:5] in k_][:5])
        assert zh, (label,)
        t = re.sub(re.escape(old) + r'(?!\{)', lambda m_: old + '{%s}' % zh, t)
    probs = validate.check_description(en[key]['description'], t, validate.ALLOWED_ENGLISH | {'Foundry', 'lookup', 'scale'})
    assert not probs, probs
    return t


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
    def sup(k): return [l for l in D(k)['sup']]
    def sline(k, prefix):
        h = [l for l in D(k)['sup'] if l.startswith(prefix)]; assert len(h) == 1, (k, prefix); return h[0].split('：', 1)[1]
    def bold_first(line, phrase):
        assert phrase in line, (line, phrase); return line.replace(phrase, B(phrase), 1)

    # new entries from the source
    k = 'Sorcery Incarnate'; E[k]['name'] = D(k)['name']; M = D(k)['main']
    z(k, 0, M[0]); z(k, 1, M[1]); z(k, 2, H, 'supplement', SUP); z(k, 3, D(k)['sup'][1], 'supplement', SUP)
    E[k]['activities']['Restore Innate Sorcery']['name'] = sline(k, '行動：')
    k = 'Arcane Apotheosis'; E[k]['name'] = D(k)['name']
    z(k, 0, D(k)['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, D(k)['sup'][1], 'supplement', SUP)
    k = 'phbscrEpicBoon00'; E[k]['name'] = D(k)['name']; body = D(k)['main'][0]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en[k]['description']); assert len(uu) == 2
    assert '傳奇恩惠專長' in body and '次元旅行恩惠' in body
    z(k, 0, body.replace('傳奇恩惠專長', '@UUID[%s]{傳奇恩惠專長}' % uu[0], 1).replace('次元旅行恩惠', '@UUID[%s]{次元旅行恩惠}' % uu[1], 1))
    z(k, 1, H, 'supplement', SUP); z(k, 2, D(k)['sup'][1], 'supplement', SUP)

    # existing translations kept; Foundry notes and nested names translated
    for k in KEEP_KEYS:
        E[k]['name'] = D(k)['name']
        ex = Plan(cur['entries.%s.description' % k]).blocks
        bl = E[k]['blocks']; assert len(ex) == len(bl), (k, len(ex), len(bl))
        hi = [i for i, b in enumerate(bl) if b['en'].startswith('<strong>Foundry')][0]
        fx = FIX.get(k, [])
        htmls = [b.html for b in ex[:hi]]
        for a_, b_ in fx:
            n_ = sum(h.count(a_) for h in htmls); assert n_ == 1, (k, a_, n_)
            htmls = [h.replace(a_, b_) for h in htmls]
        for i in range(hi): z(k, i, htmls[i], 'supplement', EXIST + ('；使用者 2026-10-09 裁定修正' if fx else ''))
        z(k, hi, H, 'supplement', SUP)
        notes = D(k)['sup'][1:]
        notes = [l for l in notes if '：' not in l[:5] or l.startswith(('重獲', '此特性', '升級時', '使用'))]
        raw_notes = [l for l in D(k)['sup'][1:] if not l.startswith(('行動：', '效果：'))]
        assert len(raw_notes) == len(bl) - hi - 1, (k, raw_notes)
        for j, line in enumerate(raw_notes):
            i = hi + 1 + j
            if k == 'Font of Magic':
                line = bold_first(line, '重獲法術位' if j == 0 else '重獲術法點')
            z(k, i, line, 'supplement', SUP)
    # nested fields: existing values where present, new names from the draft
    k = 'Innate Sorcery'
    E[k]['activities']['Innate Sorcery']['name'] = sline(k, '行動：')
    E[k]['effects']['Innate Sorcery']['name'] = sline(k, '效果：')
    E[k]['effects']['Innate Sorcery']['description'] = cur['entries.Innate Sorcery.effects.Innate Sorcery.description']
    k = 'Font of Magic'
    for key in E[k]['activities']: E[k]['activities'][key]['name'] = cur['entries.Font of Magic.activities.%s.name' % key]
    k = 'Sorcerous Restoration'
    E[k]['activities']['Restore Sorcery Points']['name'] = sline(k, '行動：')
    jdump(s, P + '.sheet.json')

    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'build', P + '.sheet.json', '--draft', P + '.draft.txt',
                           '--out', P + '.aligned.json'], stdout=subprocess.DEVNULL)
    rc = subprocess.call([sys.executable, os.path.join(SK, 'validate.py'), P + '.aligned.json', '--book', BOOK, '--component', 'classes',
                          '--allow', 'Foundry,Active,Effect,lookup,scale,sorcerer,DC', '--out', P + '.upload.json'])
    assert rc == 0
    up = jload(P + '.upload.json')['entries']
    w = sec['Sorcerer']; adv_en = en['Sorcerer']['advancement']
    names = parts([l for l in w['sup'] if l.startswith('升級項目名稱：')][0].split('：', 1)[1])
    nkeys = [x for x in adv_en if 'name' in adv_en[x]]
    assert len(names) == len(nkeys), (len(names), nkeys)
    entry = {'advancement': {x: {'name': n} for x, n in zip(nkeys, names)}}
    assert not validate.check_subfields(entry, en['Sorcerer'])
    entry['description'] = fix_labeled(cur, en, 'Sorcerer', [('遊說', '說服'), ('法術槽', '法術位')])
    up['Sorcerer'] = entry
    up['phbscrSpellcasti'] = {'description': fix_labeled(cur, en, 'phbscrSpellcasti', [('以下資訊', '下列資訊')])}
    jdump({'entries': up}, P + '.upload.json')
    print(len(up), 'entries', validate.count_strings(up), 'strings', hashlib.sha256(open(P + '.upload.json', 'rb').read()).hexdigest())


def checks():
    s = jload(P + '.sheet.json')
    s['entries'] = {(DRAFT_NAME.get(k, k)): v for k, v in s['entries'].items() if k not in KEEP_KEYS}
    jdump(s, P + '.terms-sheet.json')
    if not os.path.exists(P + '.ack.json'): jdump({}, P + '.ack.json')
    run = lambda *a: subprocess.call([sys.executable] + list(a))
    run(os.path.join(SK, 'spell_names.py'), '--out', os.path.join(INC, 'spell-names.json'))
    run(os.path.join(SK, 'terms_check.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt', '--index', P + '.term_index.json',
        '--names', os.path.join(INC, 'spell-names.json'), '--ack', P + '.ack.json', '--out', P + '.terms-report.md')
    run(os.path.join(SK, 'draft_diff.py'), '--source', os.path.join(INC, '_source', 'sorcerer.prep.txt'), '--draft', P + '.draft.txt',
        '--supplements', 'Innate Sorcery,Font of Magic,Metamagic,Sorcerous Restoration,Sorcerer', '--out', P + '.draft-diff.md')
    out = subprocess.run([sys.executable, os.path.join(SK, 'lang_compare.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt'],
                         capture_output=True, text=True, encoding='utf-8').stdout
    open(P + '.lang-compare.md', 'w', encoding='utf-8').write(out)
    cur = live('classes')
    src = {r['context']: r['source'][0] for r in weblate.paged('/api/translations/%s/%s-classes/zh_Hant/units/' % (BOOK, BOOK))}
    def walk(x, p):
        for k, v in x.items():
            if isinstance(v, dict): yield from walk(v, p + k + '.')
            else: yield p + k, v
    raw = open(P + '.upload.json', encoding='utf-8').read()
    print('forbidden:', [w for w in ['它', '如果', '施展', '發充能', '尺', '抗性', '等於', '亡靈', '成分', '妳', '倒地', '無需', '以下'] if w in raw])
    c = {'same': 0, 'new': 0, 'over': 0}
    for pth, v in walk(json.loads(raw)['entries'], 'entries.'):
        assert pth in cur, pth
        key = 'same' if cur[pth] == v else ('new' if cur[pth] == src[pth] else 'over')
        c[key] += 1
        if key == 'over': print('  OVER', pth, '|', cur[pth][:50].replace(NL, ' '))
    print(c)


def content():
    C = os.path.join(INC, 'content.sorcerer.2')
    en = jload(CONTENT_EN)['entries']['Sorcerer']['pages']
    cl = live('classes'); cu = live('content')
    ex = Plan(cl['entries.Sorcerer.description']).blocks
    strip = lambda h: re.sub(r'@UUID\[[^\]]+\]\{([^}]*)\}', lambda m: m.group(1), h)
    vis = lambda h: re.sub(r'<[^>]+>', '', strip(h)).strip()
    idx = list(range(16, 26))
    subs = ['Aberrant Sorcery', 'Clockwork Sorcery', 'Draconic Sorcery', 'Wild Magic Sorcery']
    sub_names = [cl['entries.%s.name' % k_] for k_ in subs]
    subline = '術士子職業是一種特化，在特定等級給予你對應的特性，具體內容見各子職業的說明。接下來的頁面介紹' + '、'.join(sub_names[:3]) + '和' + sub_names[3] + '這四種子職業。'
    intro = '下列選項可供你的超魔法特性使用，並依英文字母順序排列。'
    txt = en['Metamagic Options']['text']
    mm = re.findall(r'\{([^}]+)\}</h3>', txt); assert mm
    mmz = [cl['entries.%s.name' % n_] for n_ in mm]
    assert all(a != b for a, b in zip(mmz, mm))
    lines = ['### Sorcerer.description'] + [vis(ex[i].html) for i in idx] + ['', '### Sorcerer.subclass', subline, '', '### Metamagic.text', intro] + mmz + ['']
    open(C + '.draft.txt', 'w', encoding='utf-8', newline=NL).write(NL.join(lines))
    sec = {}; cur_ = None
    for l in open(C + '.draft.txt', encoding='utf-8'):
        l = l.rstrip(NL); m = re.match(r'### (.+)', l)
        if m: cur_ = m.group(1); sec[cur_] = []
        elif l.strip() and cur_: sec[cur_].append(l.strip())
    zh = [None, None] + [strip(ex[i].html) for i in idx]
    zh[2] = zh[2].replace('術士', lab('classes.Item.phbscrSorcerer00', '術士'), 1)
    def rows(html, zhs):
        b_ = Plan(html).blocks; assert len(b_) == len(zhs), (len(b_), len(zhs))
        return [{'id': b.id, 'en': b.html, 'zh': (b.html if z is None else z), 'source': 'draft', 'basis': ''} for b, z in zip(b_, zhs)]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en['Sorcerer']['subclass']); assert len(uu) == 4
    z2 = subline
    for n_, u in zip(sub_names, uu): z2 = z2.replace(n_, '@UUID[%s]{%s}' % (u, n_), 1)
    tb = Plan(txt).blocks
    it = iter(mmz); tz = []
    for b in tb:
        if b.html.startswith('@UUID'): tz.append(re.sub(r'\{[^}]*\}$', lambda m: '{%s}' % next(it), b.html))
        elif b.html.startswith('The following options'): tz.append(intro)
        else: tz.append(None)
    sheet = {'schema_version': 2, 'book': BOOK, 'component': 'content', 'entries': {
        'Sorcerer.description': {'name_en': 'Sorcerer', 'name': '術士', 'blocks': rows(en['Sorcerer']['description'], zh)},
        'Sorcerer.subclass': {'name_en': 'Sorcerer', 'name': '術士', 'blocks': rows(en['Sorcerer']['subclass'], [z2, None])},
        'Metamagic.text': {'name_en': 'Metamagic', 'name': '超魔法選項', 'blocks': rows(txt, tz)}}}
    adapter = {'Sorcerer.description': {'description': en['Sorcerer']['description']}, 'Sorcerer.subclass': {'description': en['Sorcerer']['subclass']},
               'Metamagic.text': {'description': txt}}
    draft = {k_: re.sub(r'\s+', '', ''.join(v)) for k_, v in sec.items()}
    out = skeleton.build_entries(sheet, adapter, draft)['entries']
    allow = validate.ALLOWED_ENGLISH | {'Embed', 'Compendium', 'caption', 'false', 'classes', 'three', 'right', 'inline'}
    pages = {'Sorcerer': {'name': '術士'}}
    for k_, v in out.items():
        probs = validate.check_description(adapter[k_]['description'], v['description'], allow)
        print(k_, probs); assert not probs
    pages['Sorcerer']['description'] = out['Sorcerer.description']['description']
    pages['Sorcerer']['subclass'] = out['Sorcerer.subclass']['description']
    for pg, n_ in zip(subs, sub_names):
        assert pg in en; pages[pg] = {'name': n_}
    pages['Metamagic Options'] = {'name': '超魔法選項', 'text': out['Metamagic.text']['description']}
    payload = {'entries': {'Sorcerer': {'pages': pages}}}
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
