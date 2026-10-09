"""Monk (player-handbook) batches. Paths resolve from this file; nothing here uploads.

  python monk.py prep      -> source conversion/headings, term index
  python monk.py classes   -> classes.monk.{1,2,3}.upload.json
  python monk.py checks    -> terms / draft_diff / lang_compare / payload path audit
  python monk.py content   -> content.monk.4.upload.json
"""
import hashlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from warlock import (ROOT, SK, INC, BOOK, CLASSES_EN, CONTENT_EN, SUP, EXIST, jload, jdump, B, lab, parts, read_draft, live,
                     validate, skeleton, weblate, Plan)

FULL = ['phbmnkUnarmoredD', 'phbmnkUnarmedStr', 'Evasion', 'Stunning Strike', 'Deflect Energy', 'Heightened Focus', 'Self-Restoration',
        'Perfect Focus', 'Superior Defense', 'Disciplined Survivor', 'Body and Mind', 'phbmnkEpicBoon00']
KEEP = ["Monk's Focus", 'Unarmored Movement', 'Martial Arts', 'Slow Fall', 'Empowered Strikes', 'Uncanny Metabolism', 'Deflect Attacks']
DRAFT_NAME = {'phbmnkUnarmoredD': 'Unarmored Defense', 'phbmnkUnarmedStr': 'Unarmed Strike', 'phbmnkEpicBoon00': 'Epic Boon'}
BATCHES = {'1': ['phbmnkUnarmoredD', 'phbmnkUnarmedStr', 'Evasion', 'Stunning Strike', 'Deflect Energy', 'Heightened Focus', 'Self-Restoration'],
           '2': ['Perfect Focus', 'Superior Defense', 'Disciplined Survivor', 'Body and Mind', 'phbmnkEpicBoon00', "Monk's Focus", 'Unarmored Movement'],
           '3': ['Martial Arts', 'Slow Fall', 'Empowered Strikes', 'Uncanny Metabolism', 'Deflect Attacks', 'Monk']}
P = os.path.join(INC, 'classes.monk.1')
NL = chr(10)


def prep():
    import opencc
    conv = opencc.OpenCC('s2twp').convert(open(os.path.join(INC, 'monk.txt'), encoding='utf-8').read())
    open(os.path.join(INC, '_source', 'monk.s2twp.txt'), 'w', encoding='utf-8', newline='').write(conv)
    L = conv.replace(chr(13), '').split(NL)
    def r(a, b): return [x for x in L[a - 1:b] if x.strip()]
    secs = [('無甲防禦 Unarmored Defense', r(66, 66)), ('反射閃避 Evasion', r(106, 107)), ('震懾拳 Stunning Strike', r(100, 100)),
            ('撥擋能量 Deflect Energy', r(123, 123)), ('出神入化 Heightened Focus', r(113, 116)), ('返本還元 Self-Restoration', r(119, 120)),
            ('明鏡止水 Perfect Focus', r(130, 130)), ('無懈可擊 Superior Defense', r(133, 134)), ('圓融自在 Disciplined Survivor', r(126, 127)),
            ('天人合一 Body and Mind', r(140, 140)), ('傳奇恩惠 Epic Boon', r(137, 137)), ('武僧 Monk', r(88, 88))]
    out = []
    for h, ls in secs: out += [h] + ls + ['']
    open(os.path.join(INC, '_source', 'monk.prep.txt'), 'w', encoding='utf-8', newline=NL).write(NL.join(out))
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
    def line(k, prefix):
        h = [l for l in D(k)['sup'] if l.startswith(prefix)]; assert len(h) == 1, (k, prefix, h); return h[0]
    def sline(k, prefix): return line(k, prefix).split('：', 1)[1]
    def nm(k): E[k]['name'] = D(k)['name']
    def run_in(t_):
        m = re.match(r'(【[^】]+】)(.*)', t_, re.S); return B(m.group(1)) + m.group(2)
    def bold(t_, phrase):
        assert phrase in t_, (t_, phrase); return t_.replace(phrase, B(phrase), 1)
    def ref(t_, plain, token, label):
        assert t_.count(plain) == 1, (t_, plain)
        return t_.replace(plain, plain.replace(label, '&amp;Reference[%s]{%s}' % (token, label)))
    def notes(k):
        return [l for l in D(k)['sup'][1:] if not l.startswith(('行動', '效果', '升級項目', '參見'))]
    def named_notes(k):   # sup lines excluding the heading and the field lines
        return [l for l in D(k)['sup'] if not l.startswith(('【Foundry', '行動', '效果', '升級項目', '參見'))]
    def acts(k, zhnames):
        a = E[k]['activities']; assert len(a) == len(zhnames), (k, list(a))
        for key, n in zip(a, zhnames): a[key]['name'] = n
        return a
    def fixed(k, repl):
        return repl

    # ---------- FULL entries ----------
    k = 'phbmnkUnarmoredD'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)
    E[k]['effects']['Unarmored Defense']['name'] = cur['entries.phbmnkUnarmoredD.effects.Unarmored Defense.name']

    k = 'phbmnkUnarmedStr'; nm(k)
    uid = re.findall(r'@UUID\[([^\]]+)\]', en[k]['description'])[0]
    z(k, 0, '<em>參見：@UUID[%s]{武藝（武僧）}</em>' % uid, 'supplement', SUP + '；EN: See: Martial Arts (Monk)')
    a = acts(k, [sline(k, '行動：')]); a['Grapple/Shove']['chatFlavor'] = sline(k, '行動聊天提示：')
    for key, n in zip(E[k]['effects'], parts(sline(k, '效果：'))): E[k]['effects'][key]['name'] = n

    k = 'Evasion'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, D(k)['main'][1])

    k = 'Stunning Strike'; nm(k)
    z(k, 0, ref(D(k)['main'][0], '陷入震懾狀態', 'Stunned apply=false', '震懾'))
    z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)
    E[k]['activities']['save']['condition'] = sline(k, '行動條件：')
    for key, n in zip(E[k]['effects'], parts(sline(k, '效果：'))): E[k]['effects'][key]['name'] = n

    k = 'Deflect Energy'; nm(k); M = D(k)['main']
    z(k, 0, M[0]); n_ = named_notes(k)
    z(k, 1, bold(n_[0], '撥擋'), 'supplement', SUP); z(k, 2, bold(n_[1], '借力打力'), 'supplement', SUP)
    a = acts(k, parts(sline(k, '行動：'))); conds = parts(sline(k, '行動條件：'))
    a['Reduce']['condition'] = conds[0]; a['Redirect']['condition'] = conds[1]
    a['Redirect']['range'] = sline(k, '行動範圍：'); a['Redirect']['target'] = sline(k, '行動目標：')

    k = 'Heightened Focus'; nm(k); M = D(k)['main']
    z(k, 0, M[0]); z(k, 1, run_in(M[1])); z(k, 2, run_in(M[2])); z(k, 3, run_in(M[3])); z(k, 4, H, 'supplement', SUP)
    n_ = named_notes(k); z(k, 5, bold(n_[0], '疾風連擊'), 'supplement', SUP); z(k, 6, bold(n_[1], '閃轉騰挪'), 'supplement', SUP)
    a = acts(k, parts(sline(k, '行動：'))); a['Patient Defense']['condition'] = sline(k, '行動條件：')

    k = 'Self-Restoration'; nm(k); M = D(k)['main']
    t1 = M[0]
    for tok, lb in (('Charmed apply=false', '魅惑'), ('Frightened apply=false', '恐慌'), ('Poisoned apply=false', '中毒')):
        assert t1.count(lb) == 1, (t1, lb); t1 = t1.replace(lb, '&amp;Reference[%s]{%s}' % (tok, lb))
    t2 = M[1]; assert t2.count('力竭') == 1
    t2 = t2.replace('力竭', '&amp;Reference[Exhaustion apply=false]{力竭}')
    z(k, 0, t1); z(k, 1, t2)

    k = 'Perfect Focus'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)

    k = 'Superior Defense'; nm(k); M = D(k)['main']
    z(k, 0, M[0] + M[1]); z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)
    E[k]['activities']['utility']['condition'] = sline(k, '行動條件：'); E[k]['effects']['Superior Defense']['name'] = sline(k, '效果：')

    k = 'Disciplined Survivor'; nm(k); M = D(k)['main']
    z(k, 0, M[0]); z(k, 1, M[1]); z(k, 2, H, 'supplement', SUP); z(k, 3, named_notes(k)[0], 'supplement', SUP)
    acts(k, [sline(k, '行動：')]); E[k]['effects']['Disciplined Survivor']['name'] = sline(k, '效果：')

    k = 'Body and Mind'; nm(k); z(k, 0, D(k)['main'][0])

    k = 'phbmnkEpicBoon00'; nm(k); body = D(k)['main'][0]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en[k]['description']); assert len(uu) == 2
    assert '傳奇恩惠專長' in body and '無敵攻勢恩惠' in body
    z(k, 0, body.replace('傳奇恩惠專長', '@UUID[%s]{傳奇恩惠專長}' % uu[0], 1).replace('無敵攻勢恩惠', '@UUID[%s]{無敵攻勢恩惠}' % uu[1], 1))
    z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)

    # ---------- KEEP entries: existing body, translated notes / nested names, user-approved style fixes ----------
    def ex_blocks(k): return Plan(cur['entries.%s.description' % k]).blocks
    k = "Monk's Focus"; nm(k); ex = ex_blocks(k); bl = E[k]['blocks']; assert len(ex) == len(bl)
    hi = 7
    htmls = [b.html for b in ex[:hi]]
    for a_, b_ in (('行步如風', '疾步如風'), ('豁免DC = 8+你的感知調整值+你的熟練加值', '豁免DC為8 + 你的感知調整值 + 你的熟練加值')):
        assert sum(h.count(a_) for h in htmls) == 1, a_
        htmls = [h.replace(a_, b_) for h in htmls]
    for i in range(hi): z(k, i, htmls[i], 'supplement', EXIST + ('；使用者規則修正' if i in (3, 6) else ''))
    z(k, 7, H, 'supplement', SUP)
    n_ = named_notes(k)
    z(k, 8, bold(bold(n_[0], '疾風連擊'), '消耗內力點'), 'supplement', SUP)
    z(k, 9, bold(bold(n_[1], '閃轉騰挪'), '閃轉騰挪（內力點）'), 'supplement', SUP)
    z(k, 10, bold(n_[2], '疾步如風'), 'supplement', SUP)
    a = E[k]['activities']
    for key in a: a[key]['name'] = cur["entries.Monk's Focus.activities.%s.name" % key]
    a['Flurry of Blows']['chatFlavor'] = '進行兩次[[/item Unarmed Strike]]{%s}' % '徒手打擊'
    ef = E[k]['effects']; ef['Patient Defense (Focus Point)']['name'] = sline(k, '效果：'); ef['Disengaged']['name'] = cur["entries.Monk's Focus.effects.Disengaged.name"]

    k = 'Unarmored Movement'; nm(k); ex = ex_blocks(k)
    z(k, 0, ex[0].html, 'supplement', EXIST); z(k, 1, ex[1].html, 'supplement', EXIST + '；EN 已無尾端 Foundry 註記，不採既有 fuzzy 註記')
    E[k]['effects']['Unarmored Movement']['name'] = cur['entries.Unarmored Movement.effects.Unarmored Movement.name']

    k = 'Martial Arts'; nm(k); ex = ex_blocks(k); bl = E[k]['blocks']; assert len(ex) == len(bl)
    for i in range(8):
        h = ex[i].html
        if i == 3: assert '未著裝護甲或持盾' in h; h = h.replace('未著裝護甲或持盾', '未穿戴護甲或握持盾牌')
        z(k, i, h, 'supplement', EXIST + ('；轉換修正 著裝→穿戴' if i == 3 else ''))
    z(k, 8, H, 'supplement', SUP)
    z(k, 9, '此特性包含用於為武器附魔的行動，會為該武器加入整合上述變化的<strong>武僧攻擊</strong>行動。', 'supplement', SUP)
    a = E[k]['activities']
    for key in a: a[key]['name'] = cur['entries.Martial Arts.activities.%s.name' % key]
    ef = E[k]['effects']['Dexterous Attacks & Martial Arts Damage']
    ef['name'] = sline(k, '效果：')
    e5 = ex[5].html.replace('1d6', '[[lookup @scale.monk.die]]'); e7 = ex[7].html
    assert '[[lookup' in e5
    ef['description'] = '<p>%s</p><p>%s</p><p></p>' % (e5, e7)
    ef['changes']['3'] = sline(k, '效果修改：')

    for k, bolds in (('Slow Fall', ['減少傷害']), ('Empowered Strikes', ['真力注拳', None]), ('Uncanny Metabolism', [None])):
        nm(k); ex = ex_blocks(k); bl = E[k]['blocks']; assert len(ex) == len(bl), (k, len(ex), len(bl))
        hi = next(i for i, b_ in enumerate(bl) if b_['en'].startswith('<strong>Foundry'))
        for i in range(hi): z(k, i, ex[i].html, 'supplement', EXIST)
        z(k, hi, H, 'supplement', SUP)
        for j, (n_, bd) in enumerate(zip(named_notes(k), bolds)): z(k, hi + 1 + j, bold(n_, bd) if bd else n_, 'supplement', SUP)
        assert hi + 1 + len(bolds) == len(bl), k
    acts('Slow Fall', [sline('Slow Fall', '行動：')]); acts('Empowered Strikes', [sline('Empowered Strikes', '行動：')])
    for key in E['Uncanny Metabolism']['activities']:
        E['Uncanny Metabolism']['activities'][key]['name'] = cur['entries.Uncanny Metabolism.activities.%s.name' % key]
        E['Uncanny Metabolism']['activities'][key]['condition'] = cur['entries.Uncanny Metabolism.activities.%s.condition' % key]

    k = 'Deflect Attacks'; nm(k); ex = ex_blocks(k); bl = E[k]['blocks']; assert len(ex) == len(bl)
    for i in range(2):
        h = ex[i].html
        if i == 1: assert '全掩護' in h; h = h.replace('全掩護', '全掩蔽')
        z(k, i, h, 'supplement', EXIST + ('；使用者裁定 全掩蔽' if i == 1 else ''))
    z(k, 2, H, 'supplement', SUP)
    n_ = named_notes(k); z(k, 3, bold(n_[0], '撥擋'), 'supplement', SUP); z(k, 4, bold(n_[1], '借力打力'), 'supplement', SUP)
    a = E[k]['activities']
    for key in a:
        a[key]['name'] = cur['entries.Deflect Attacks.activities.%s.name' % key]; a[key]['condition'] = cur['entries.Deflect Attacks.activities.%s.condition' % key]
    a['Redirect']['range'] = sline(k, '行動範圍：'); a['Redirect']['target'] = sline(k, '行動目標：')
    jdump(s, P + '.sheet.json')

    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'build', P + '.sheet.json', '--draft', P + '.draft.txt',
                           '--out', P + '.aligned.json'], stdout=subprocess.DEVNULL)
    rc = subprocess.call([sys.executable, os.path.join(SK, 'validate.py'), P + '.aligned.json', '--book', BOOK, '--component', 'classes',
                          '--allow', 'Foundry,Active,Effect,lookup,scale,monk,item,Unarmed,Strike,die', '--out', P + '.upload.json'])
    assert rc == 0
    up = jload(P + '.upload.json')['entries']
    w = sec['Monk']; adv_en = en['Monk']['advancement']
    names = parts([l for l in w['sup'] if l.startswith('升級項目名稱：')][0].split('：', 1)[1])
    nkeys = [x for x in adv_en if 'name' in adv_en[x]]
    assert len(names) == len(nkeys), (len(names), nkeys)
    entry = {'advancement': {x: {'name': n} for x, n in zip(nkeys, names)}}
    assert not validate.check_subfields(entry, en['Monk'])
    up['Monk'] = entry
    # user rulings 2026-10-09: focus point cost reads 「消耗N點內力」; Uncanny Metabolism＝周天運轉; Disciplined Survivor＝堅忍不拔
    def fx(x):
        if isinstance(x, str):
            x = re.sub(r'消耗(\d+)內力點', lambda m: '消耗%s點內力' % m.group(1), x)
            return x.replace('運氣入化', '周天運轉').replace('隨遇而安', '堅忍不拔')
        if isinstance(x, dict): return {k_: fx(v_) for k_, v_ in x.items()}
        return x
    up = fx(up)
    jdump({'entries': up}, P + '.all.json')
    for n_, ks in BATCHES.items():
        d_ = {k_: up[k_] for k_ in ks}
        f_ = os.path.join(INC, 'classes.monk.%s.upload.json' % n_)
        jdump({'entries': d_}, f_)
        print('batch', n_, len(d_), 'entries', validate.count_strings(d_), 'strings', hashlib.sha256(open(f_, 'rb').read()).hexdigest())


def checks():
    s = jload(P + '.sheet.json')
    s['entries'] = {(DRAFT_NAME.get(k, k)): v for k, v in s['entries'].items() if k not in KEEP}
    jdump(s, P + '.terms-sheet.json')
    if not os.path.exists(P + '.ack.json'): jdump({}, P + '.ack.json')
    run = lambda *a: subprocess.call([sys.executable] + list(a))
    run(os.path.join(SK, 'spell_names.py'), '--out', os.path.join(INC, 'spell-names.json'))
    run(os.path.join(SK, 'terms_check.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt', '--index', P + '.term_index.json',
        '--names', os.path.join(INC, 'spell-names.json'), '--ack', P + '.ack.json', '--out', P + '.terms-report.md')
    run(os.path.join(SK, 'draft_diff.py'), '--source', os.path.join(INC, '_source', 'monk.prep.txt'), '--draft', P + '.draft.txt',
        '--supplements', "Unarmed Strike,Monk's Focus,Unarmored Movement,Martial Arts,Slow Fall,Empowered Strikes,Uncanny Metabolism,Deflect Attacks,Monk", '--out', P + '.draft-diff.md')
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
    print('forbidden:', [w for w in ['它', '如果', '施展', '發充能', '尺', '抗性', '等於', '亡靈', '成分', '妳', '倒地', '無需', '以下', '法術槽', '功力', '全掩護', '著裝'] if w in raw])
    c = {'same': 0, 'new': 0, 'over': 0}
    for pth, v in walk(json.loads(raw)['entries'], 'entries.'):
        assert pth in cur, pth
        key = 'same' if cur[pth] == v else ('new' if cur[pth] == src[pth] else 'over')
        c[key] += 1
        if key == 'over': print('  OVER', pth, '|', cur[pth][:50].replace(NL, ' '))
    print(c)


def content():
    C = os.path.join(INC, 'content.monk.4')
    en = jload(CONTENT_EN)['entries']['Monk']['pages']
    cl = live('classes'); cu = live('content')
    ex = Plan(cl['entries.Monk.description']).blocks
    assert len(ex) == 29, len(ex)
    strip = lambda h: re.sub(r'@UUID\[[^\]]+\]\{([^}]*)\}', lambda m: m.group(1), h)
    vis = lambda h: re.sub(r'<[^>]+>', '', strip(h)).strip()
    idx = list(range(18, 29))
    subs = ['Warrior of Mercy', 'Warrior of Shadow', 'Warrior of the Elements', 'Warrior of the Open Hand']
    sub_names = [cl['entries.%s.name' % k_] for k_ in subs]
    subline = '武僧子職業是一種特化，在特定等級給予你對應的特性，具體內容見各子職業的說明。接下來的頁面介紹' + '、'.join(sub_names[:3]) + '和' + sub_names[3] + '這四種子職業。'
    lines = ['### Monk.description'] + [vis(ex[i].html) for i in idx] + ['', '### Monk.subclass', subline, '']
    open(C + '.draft.txt', 'w', encoding='utf-8', newline=NL).write(NL.join(lines))
    sec = {}; cur_ = None
    for l in open(C + '.draft.txt', encoding='utf-8'):
        l = l.rstrip(NL); m = re.match(r'### (.+)', l)
        if m: cur_ = m.group(1); sec[cur_] = []
        elif l.strip() and cur_: sec[cur_].append(l.strip())
    zh = [None] + [strip(ex[i].html) for i in idx]
    assert zh[1].startswith('武僧')
    zh[1] = zh[1].replace('武僧', lab('classes.Item.phbmnkMonk000000', '武僧'), 1)
    def rows(html, zhs):
        b_ = Plan(html).blocks; assert len(b_) == len(zhs), (len(b_), len(zhs))
        return [{'id': b.id, 'en': b.html, 'zh': (b.html if z is None else z), 'source': 'draft', 'basis': ''} for b, z in zip(b_, zhs)]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en['Monk']['subclass']); assert len(uu) == 4, uu
    z2 = subline
    for n_, u in zip(sub_names, uu): z2 = z2.replace(n_, '@UUID[%s]{%s}' % (u, n_), 1)
    nsub = len(Plan(en['Monk']['subclass']).blocks)
    sheet = {'schema_version': 2, 'book': BOOK, 'component': 'content', 'entries': {
        'Monk.description': {'name_en': 'Monk', 'name': '武僧', 'blocks': rows(en['Monk']['description'], zh)},
        'Monk.subclass': {'name_en': 'Monk', 'name': '武僧', 'blocks': rows(en['Monk']['subclass'], [z2] + [None] * (nsub - 1))}}}
    adapter = {'Monk.description': {'description': en['Monk']['description']}, 'Monk.subclass': {'description': en['Monk']['subclass']}}
    draft = {k_: re.sub(r'\s+', '', ''.join(v)) for k_, v in sec.items()}
    out = skeleton.build_entries(sheet, adapter, draft)['entries']
    allow = validate.ALLOWED_ENGLISH | {'Embed', 'Compendium', 'caption', 'false', 'classes', 'three', 'right'}
    pages = {'Monk': {'name': '武僧'}}
    for k_, v in out.items():
        probs = validate.check_description(adapter[k_]['description'], v['description'], allow)
        print(k_, probs); assert not probs
        pages['Monk'][k_.split('.')[1]] = v['description']
    for pg, n_ in zip(subs, sub_names):
        assert pg in en; pages[pg] = {'name': n_}
    payload = {'entries': {'Monk': {'pages': pages}}}
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
