"""Fighter (player-handbook) batches. Paths resolve from this file; nothing here uploads.

  python fighter.py prep      -> source conversion/headings, term index
  python fighter.py classes   -> classes.fighter.{1,2}.upload.json
  python fighter.py checks    -> terms / draft_diff / lang_compare / payload path audit
  python fighter.py content   -> content.fighter.3.upload.json
"""
import hashlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sorcerer import fix_labeled
from warlock import (ROOT, SK, INC, BOOK, CLASSES_EN, CONTENT_EN, SUP, EXIST, jload, jdump, B, lab, parts, read_draft, live,
                     validate, skeleton, weblate, Plan)

FULL = ['Studied Attacks', 'Two Extra Attacks', 'Three Extra Attacks', 'phbftrEpicBoon00']
KEEP = ['Tactical Shift', 'Indomitable', 'Tactical Master', 'Second Wind', 'Action Surge', 'phbftrWeaponMast']
DRAFT_NAME = {'phbftrEpicBoon00': 'Epic Boon', 'phbftrWeaponMast': 'Weapon Mastery'}
BATCHES = {'1': ['Tactical Shift', 'Indomitable', 'Tactical Master', 'Studied Attacks', 'Two Extra Attacks', 'Three Extra Attacks', 'phbftrEpicBoon00'],
           '2': ['Second Wind', 'Action Surge', 'phbftrWeaponMast', 'Fighter']}
P = os.path.join(INC, 'classes.fighter.1')
NL = chr(10)


def prep():
    import opencc
    conv = opencc.OpenCC('s2twp').convert(open(os.path.join(INC, 'fighter.txt'), encoding='utf-8').read())
    os.makedirs(os.path.join(INC, '_source'), exist_ok=True)
    open(os.path.join(INC, '_source', 'fighter.s2twp.txt'), 'w', encoding='utf-8', newline='').write(conv)
    L = conv.replace(chr(13), '').split(NL)
    def r(a, b): return [x for x in L[a - 1:b] if x.strip()]
    secs = [('戰術轉進 Tactical Shift', r(83, 83)), ('不屈 Indomitable', r(86, 87)), ('戰術主宰 Tactical Master', r(90, 90)),
            ('究明攻擊 Studied Attacks', r(96, 96)), ('額外攻擊（二） Two Extra Attacks', r(93, 93)), ('額外攻擊（三） Three Extra Attacks', r(102, 102)),
            ('傳奇恩惠 Epic Boon', r(99, 99)), ('回氣 Second Wind', r(58, 60)), ('動作如潮 Action Surge', r(67, 68)), ('武器精通 Weapon Mastery', r(63, 64)),
            ('戰士 Fighter', r(74, 74))]
    out = []
    for h, ls in secs: out += [h] + ls + ['']
    open(os.path.join(INC, '_source', 'fighter.prep.txt'), 'w', encoding='utf-8', newline=NL).write(NL.join(out))
    subprocess.call([sys.executable, os.path.join(SK, 'build_index.py'), '--skip-book', 'player-handbook', '--out', P + '.term_index.json'])


def classes():
    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'extract', '--book', BOOK, '--component', 'classes', '--keys']
                          + FULL + KEEP + ['--out', P + '.sheet.json'], stdout=subprocess.DEVNULL)
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
    def named_notes(k): return [l for l in D(k)['sup'] if not l.startswith(('【Foundry', '行動', '效果', '升級項目'))]

    for k in ('Studied Attacks', 'Two Extra Attacks', 'Three Extra Attacks'):
        nm(k); z(k, 0, D(k)['main'][0])
    k = 'Studied Attacks'; z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)
    k = 'phbftrEpicBoon00'; nm(k); body = D(k)['main'][0]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en[k]['description']); assert len(uu) == 2
    z(k, 0, body.replace('傳奇恩惠專長', '@UUID[%s]{傳奇恩惠專長}' % uu[0], 1).replace('戰鬥威能恩惠', '@UUID[%s]{戰鬥威能恩惠}' % uu[1], 1))

    def ex_blocks(k): return Plan(cur['entries.%s.description' % k]).blocks
    for k in KEEP:
        nm(k); ex = ex_blocks(k); bl = E[k]['blocks']; assert len(ex) == len(bl), (k, len(ex), len(bl))
        hi = next((i for i, b in enumerate(bl) if b['en'].startswith('<strong>Foundry')), len(bl))
        htmls = [b_.html for b_ in ex]
        if k == 'phbftrWeaponMast':   # user 2026-10-09: remove 「擁有熟練」 (EN has no proficiency requirement)
            assert htmls[0].count('且擁有熟練的武器精通屬性') == 1
            htmls[0] = htmls[0].replace('三種你所選擇且擁有熟練的武器精通屬性', '三種你所選擇的簡易或軍用武器的精通屬性')
            assert '擁有熟練' not in htmls[0]
        for i in range(hi): z(k, i, htmls[i], 'supplement', EXIST + ('；使用者裁定修正（刪「擁有熟練」）' if k == 'phbftrWeaponMast' and i == 0 else ''))
        if hi < len(bl):
            z(k, hi, H, 'supplement', SUP); z(k, hi + 1, named_notes(k)[0], 'supplement', SUP)
    E['Indomitable']['activities']['utility']['roll'] = sline('Indomitable', '行動擲骰：')
    E['Tactical Master']['effects']['Tactical Master']['name'] = sline('Tactical Master', '效果：')
    jdump(s, P + '.sheet.json')

    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'build', P + '.sheet.json', '--draft', P + '.draft.txt',
                           '--out', P + '.aligned.json'], stdout=subprocess.DEVNULL)
    rc = subprocess.call([sys.executable, os.path.join(SK, 'validate.py'), P + '.aligned.json', '--book', BOOK, '--component', 'classes',
                          '--allow', 'Foundry,Active,Effect,lookup,classes,fighter', '--out', P + '.upload.json'])
    assert rc == 0
    up = jload(P + '.upload.json')['entries']
    w = sec['Fighter']; adv_en = en['Fighter']['advancement']
    names = parts([l for l in w['sup'] if l.startswith('升級項目名稱：')][0].split('：', 1)[1])
    nkeys = [x for x in adv_en if 'name' in adv_en[x]]
    assert len(names) == len(nkeys), (len(names), nkeys)
    entry = {'advancement': {x: {'name': n} for x, n in zip(nkeys, names)}}
    assert not validate.check_subfields(entry, en['Fighter'])
    entry['description'] = fix_labeled(cur, en, 'Fighter', [('遊說', '說服'), ('[[/award 4GP]]', '4 GP')])   # user 2026-10-09: 遊說→說服
    up['Fighter'] = entry
    jdump({'entries': up}, P + '.all.json')
    for n_, ks in BATCHES.items():
        d_ = {k_: up[k_] for k_ in ks}
        f_ = os.path.join(INC, 'classes.fighter.%s.upload.json' % n_)
        jdump({'entries': d_}, f_)
        print('batch', n_, len(d_), 'entries', validate.count_strings(d_), 'strings', hashlib.sha256(open(f_, 'rb').read()).hexdigest())


def checks():
    s = jload(P + '.sheet.json')
    s['entries'] = {(DRAFT_NAME.get(k, k)): v for k, v in s['entries'].items() if k in FULL}
    jdump(s, P + '.terms-sheet.json')
    if not os.path.exists(P + '.ack.json'): jdump({}, P + '.ack.json')
    run = lambda *a: subprocess.call([sys.executable] + list(a))
    run(os.path.join(SK, 'spell_names.py'), '--out', os.path.join(INC, 'spell-names.json'))
    run(os.path.join(SK, 'terms_check.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt', '--index', P + '.term_index.json',
        '--names', os.path.join(INC, 'spell-names.json'), '--ack', P + '.ack.json', '--out', P + '.terms-report.md')
    run(os.path.join(SK, 'draft_diff.py'), '--source', os.path.join(INC, '_source', 'fighter.prep.txt'), '--draft', P + '.draft.txt',
        '--supplements', 'Tactical Shift,Indomitable,Tactical Master,Second Wind,Action Surge,Weapon Mastery,Fighter', '--out', P + '.draft-diff.md')
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
    print('forbidden:', [w for w in ['它', '如果', '施展', '發充能', '尺', '抗性', '等於', '亡靈', '成分', '妳', '倒地', '以下', '法術槽'] if w in raw])
    c = {'same': 0, 'new': 0, 'over': 0}
    for pth, v in walk(json.loads(raw)['entries'], 'entries.'):
        assert pth in cur, pth
        key = 'same' if cur[pth] == v else ('new' if cur[pth] == src[pth] else 'over')
        c[key] += 1
        if key == 'over': print('  OVER', pth, '|', cur[pth][:50].replace(NL, ' '))
    print(c)


def content():
    C = os.path.join(INC, 'content.fighter.3')
    en = jload(CONTENT_EN)['entries']['Fighter']['pages']
    cl = live('classes'); cu = live('content')
    ex = Plan(cl['entries.Fighter.description']).blocks
    assert len(ex) == 25, len(ex)
    strip = lambda h: re.sub(r'@UUID\[[^\]]+\]\{([^}]*)\}', lambda m: m.group(1), h)
    vis = lambda h: re.sub(r'<[^>]+>', '', strip(h)).strip()
    idx = list(range(16, 25))
    subs = ['Battle Master', 'Champion', 'Eldritch Knight', 'Psi Warrior']
    sub_names = [cl['entries.%s.name' % k_] for k_ in subs]
    subline = '戰士子職業是一種特化，在特定等級給予你對應的特性，具體內容見各子職業的說明。接下來的頁面介紹' + '、'.join(sub_names[:3]) + '和' + sub_names[3] + '這四種子職業。'
    lines = ['### Fighter.description'] + [vis(ex[i].html) for i in idx] + ['', '### Fighter.subclass', subline, '']
    open(C + '.draft.txt', 'w', encoding='utf-8', newline=NL).write(NL.join(lines))
    sec = {}; cur_ = None
    for l in open(C + '.draft.txt', encoding='utf-8'):
        l = l.rstrip(NL); m = re.match(r'### (.+)', l)
        if m: cur_ = m.group(1); sec[cur_] = []
        elif l.strip() and cur_: sec[cur_].append(l.strip())
    zh = [None] + [strip(ex[i].html) for i in idx]
    # the first paragraph of the EN page links the class name
    zh[1] = zh[1].replace('戰士', lab('classes.Item.phbftrFighter000', '戰士'), 1)
    def rows(html, zhs):
        b_ = Plan(html).blocks; assert len(b_) == len(zhs), (len(b_), len(zhs))
        return [{'id': b.id, 'en': b.html, 'zh': (b.html if z is None else z), 'source': 'draft', 'basis': ''} for b, z in zip(b_, zhs)]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en['Fighter']['subclass']); assert len(uu) == 4, uu
    z2 = subline
    for n_, u in zip(sub_names, uu): z2 = z2.replace(n_, '@UUID[%s]{%s}' % (u, n_), 1)
    nsub = len(Plan(en['Fighter']['subclass']).blocks)
    sheet = {'schema_version': 2, 'book': BOOK, 'component': 'content', 'entries': {
        'Fighter.description': {'name_en': 'Fighter', 'name': '戰士', 'blocks': rows(en['Fighter']['description'], zh)},
        'Fighter.subclass': {'name_en': 'Fighter', 'name': '戰士', 'blocks': rows(en['Fighter']['subclass'], [z2] + [None] * (nsub - 1))}}}
    adapter = {'Fighter.description': {'description': en['Fighter']['description']}, 'Fighter.subclass': {'description': en['Fighter']['subclass']}}
    draft = {k_: re.sub(r'\s+', '', ''.join(v)) for k_, v in sec.items()}
    out = skeleton.build_entries(sheet, adapter, draft)['entries']
    allow = validate.ALLOWED_ENGLISH | {'Embed', 'Compendium', 'caption', 'false', 'classes', 'three', 'right'}
    pages = {'Fighter': {'name': '戰士'}}
    for k_, v in out.items():
        probs = validate.check_description(adapter[k_]['description'], v['description'], allow)
        print(k_, probs); assert not probs
        pages['Fighter'][k_.split('.')[1]] = v['description']
    for pg, n_ in zip(subs, sub_names):
        assert pg in en; pages[pg] = {'name': n_}
    payload = {'entries': {'Fighter': {'pages': pages}}}
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
