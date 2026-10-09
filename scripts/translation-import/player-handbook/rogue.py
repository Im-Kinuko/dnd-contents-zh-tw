"""Rogue (player-handbook) batches. Paths resolve from this file; nothing here uploads.

  python rogue.py classes   -> classes.rogue.1.upload.json (batch 1) and classes.rogue.2.upload.json (batch 2)
  python rogue.py checks    -> terms / draft_diff / lang_compare / payload path audit
  python rogue.py content   -> content.rogue.3.upload.json
"""
import hashlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from warlock import (ROOT, SK, INC, BOOK, CLASSES_EN, CONTENT_EN, SUP, EXIST, jload, jdump, B, lab, parts, read_draft, live,
                     validate, skeleton, weblate, Plan)

NEW_KEYS = ['Cunning Strike', 'Improved Cunning Strike', 'Devious Strikes', 'Uncanny Dodge', 'phbrgeEvasion000', 'Reliable Talent',
            'Slippery Mind', 'Elusive', 'phbrgeEpicBoon00', 'Stroke of Luck']
KEEP_KEYS = ['phbrgeExpertise0', 'Sneak Attack', "Thieves' Cant", 'Cunning Action']
BATCH1 = ['Cunning Strike', 'Improved Cunning Strike', 'Devious Strikes', 'Uncanny Dodge', 'phbrgeEvasion000', 'Reliable Talent']
DRAFT_NAME = {'phbrgeEvasion000': 'Evasion', 'phbrgeEpicBoon00': 'Epic Boon', 'phbrgeExpertise0': 'Expertise'}
SPAN1 = '<span class="reference"><em class="fas fa-user-shield"> </em>應用半傷</span>'
SPAN2 = '<span class="reference"><em class="fa-solid fa-reply-all"> </em>應用</span>'
TOK = SUP + '；指示物＝lang Token、應用半傷＝lang ChatContextHalfDamage'
MAC = '[[/item Cunning Strike activity=Cunning Sneak Attack]]{詭詐偷襲}'
P = os.path.join(INC, 'classes.rogue.1')


def spans(line):
    assert '選擇應用半傷，' in line and '再點擊應用按鈕' in line
    return line.replace('選擇應用半傷，', '選擇' + SPAN1 + '，', 1).replace('再點擊應用按鈕', '再點擊' + SPAN2 + '按鈕', 1)


def fix_rogue_class(cur, en):
    """Existing Rogue description with user-approved fixes (遊說→說服, 成為遊蕩者…, 通常) and {labels} for the equipment links."""
    t = cur['entries.Rogue.description']
    def sub1(a, b):
        nonlocal t
        assert t.count(a) == 1, (a, t.count(a)); t = t.replace(a, b)
    sub1('遊說、巧手', '說服、巧手'); sub1('<h2>作為遊蕩者…</h2>', '<h2>成為遊蕩者…</h2>'); sub1('通常都無法匹敵', '都無法匹敵')
    eq = {}
    for r in weblate.paged('/api/translations/%s/%s-equipment/zh_Hant/units/' % (BOOK, BOOK)):
        if r['context'].endswith('.name'): eq[r['context'][len('entries.'):-len('.name')]] = r['target'][0]
    en_labels = re.findall(r'@UUID\[([^\]]+)\]\{([^}]*)\}', en['Rogue']['description'])
    for uid, label in en_labels:
        label = label.replace(chr(173), '')
        if 'equipment.Item' not in uid: continue
        key = label if label in eq else (label[:-1] if label.endswith('s') and label[:-1] in eq else None)
        key = key or {'Thieves’ Tools': "Thieves' Tools", 'Burglar’s Pack': "Burglar's Pack"}.get(label)
        assert key in eq, (label, key)
        old = '@UUID[%s]' % uid
        assert t.count(old) == 1, old
        t = t.replace(old, old + '{%s}' % eq[key])
    probs = validate.check_description(en['Rogue']['description'], t, validate.ALLOWED_ENGLISH | {'Foundry'})
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
    def sup_line(k, prefix):
        h = [l for l in D(k)['sup'] if l.startswith(prefix)]; assert len(h) == 1, (k, prefix, h); return h[0]
    def sline(k, prefix): return sup_line(k, prefix).split('：', 1)[1]
    def nm(k): E[k]['name'] = D(k)['name']
    def run_in(line):
        m = re.match(r'(【[^】]+】)(.*)', line, re.S); return B(m.group(1)) + m.group(2)
    def bold(line, phrase):
        assert phrase in line, (line, phrase); return line.replace(phrase, B(phrase), 1)
    def note(k, bi, prefix, boldp=None, mac=False, tok=False):
        line = sup_line(k, prefix)
        if boldp: line = bold(line, boldp)
        if mac: line = line.replace('詭詐偷襲行動', MAC + '行動', 1)
        if tok: line = spans(line)
        z(k, bi, line, 'supplement', TOK if tok else SUP)
    def head(k, bi):
        assert D(k)['sup'][0] == '【Foundry註記】'; z(k, bi, H, 'supplement', SUP)

    def ref(line, plain, name, label):
        assert line.count(plain) == 1, (line, plain)
        return line.replace(plain, plain.replace(label, '&amp;Reference[%s]{%s}' % (name, label)))
    # --- Cunning Strike
    k = 'Cunning Strike'; nm(k); M = D(k)['main']
    z(k, 0, M[0]); z(k, 1, M[1]); z(k, 2, run_in(ref(M[2], '陷入中毒狀態', 'Poisoned', '中毒'))); z(k, 3, M[3]); z(k, 4, run_in(ref(M[4], '陷入伏地狀態', 'Prone', '伏地'))); z(k, 5, run_in(M[5]))
    head(k, 6)
    note(k, 7, '使用詭詐打擊效果後', '詭詐偷襲'); z(k, 8, sup_line(k, '你可以在傷害擲骰對話框中選擇'), 'supplement', SUP)
    note(k, 9, '淬毒行動', '淬毒'); note(k, 10, '摔絆行動', '摔絆')
    a = E[k]['activities']; assert list(a) == ['Poison', 'Trip', 'Cunning Sneak Attack', 'Withdraw']
    for key, n in zip(a, parts(sline(k, '行動：'))): a[key]['name'] = n; a[key]['condition'] = sline(k, '行動條件：')
    a['Trip']['target'] = sline(k, '行動目標：')
    ef = E[k]['effects']; assert list(ef) == ['Cunning Strike: Poisoned', 'Cunning Strike: Tripped']
    for key, n in zip(ef, parts(sline(k, '效果：'))): ef[key]['name'] = n
    ef['Cunning Strike: Poisoned']['description'] = '<p>%s</p>' % sline(k, '效果敘述：')

    # --- Improved Cunning Strike
    k = 'Improved Cunning Strike'; nm(k); z(k, 0, D(k)['main'][0]); head(k, 1)
    note(k, 2, '使用詭詐打擊效果後', mac=True); z(k, 3, sup_line(k, '你可以在傷害擲骰對話框中控制'), 'supplement', SUP)

    # --- Devious Strikes
    k = 'Devious Strikes'; nm(k); M = D(k)['main']
    z(k, 0, M[0]); z(k, 1, run_in(M[1])); z(k, 2, run_in(ref(M[2], '陷入昏迷狀態', 'Unconscious', '昏迷'))); z(k, 3, run_in(ref(M[3], '陷入目盲狀態', 'Blinded', '目盲'))); head(k, 4)
    note(k, 5, '使用詭詐打擊效果後', mac=True); z(k, 6, sup_line(k, '你可以在傷害擲骰對話框中控制'), 'supplement', SUP)
    note(k, 7, '恍惚行動', '恍惚'); note(k, 8, '擊昏行動', '擊昏'); note(k, 9, '眩目行動', '眩目')
    a = E[k]['activities']; assert list(a) == ['Daze', 'Knock Out', 'Obscure']
    for key, n in zip(a, parts(sline(k, '行動：'))): a[key]['name'] = n; a[key]['condition'] = sline(k, '行動條件：')
    ef = E[k]['effects']; assert list(ef) == ['Devious Strikes: Dazed', 'Devious Strikes: Knocked Out', 'Devious Strikes: Blinded']
    for key, n, d in zip(ef, parts(sline(k, '效果：')), parts(sline(k, '效果敘述：'))): ef[key]['name'] = n; ef[key]['description'] = '<p>%s</p>' % d

    # --- Uncanny Dodge / Evasion
    k = 'Uncanny Dodge'; nm(k); z(k, 0, D(k)['main'][0]); head(k, 1); note(k, 2, '選取你的指示物', tok=True)
    a = E[k]['activities']['Uncanny Dodge']; a['name'] = sline(k, '行動：'); a['condition'] = sline(k, '行動條件：')
    k = 'phbrgeEvasion000'; nm(k); z(k, 0, D(k)['main'][0]); head(k, 1); note(k, 2, '選取你的指示物', tok=True)

    # --- Reliable Talent
    k = 'Reliable Talent'; nm(k); z(k, 0, D(k)['main'][0]); head(k, 1); note(k, 2, '此特性包含')
    E[k]['effects']['Reliable Talent']['name'] = sline(k, '效果：')

    # --- Slippery Mind / Elusive / Stroke of Luck
    k = 'Slippery Mind'; nm(k); z(k, 0, D(k)['main'][0]); head(k, 1); note(k, 2, '這些熟練會')
    k = 'Elusive'; nm(k); z(k, 0, D(k)['main'][0])
    k = 'Stroke of Luck'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, D(k)['main'][1])
    a = E[k]['activities']['Stroke of Luck']; a['name'] = sline(k, '行動：'); a['condition'] = sline(k, '行動條件：')

    # --- Epic Boon
    k = 'phbrgeEpicBoon00'; nm(k); body = D(k)['main'][0]
    uuids = re.findall(r'@UUID\[([^\]]+)\]', en[k]['description']); assert len(uuids) == 2
    assert '傳奇恩惠專長' in body and '夜之精魂恩惠' in body
    zh = body.replace('傳奇恩惠專長', '@UUID[%s]{傳奇恩惠專長}' % uuids[0], 1).replace('夜之精魂恩惠', '@UUID[%s]{夜之精魂恩惠}' % uuids[1], 1)
    z(k, 0, zh); head(k, 1); note(k, 2, '升級時，系統會提示你進行選擇')

    # --- existing translations kept; Foundry notes translated / defects fixed
    def existing(k, key):
        return Plan(cur['entries.%s.description' % key]).blocks
    for k_ in KEEP_KEYS: nm(k_)
    k = 'phbrgeExpertise0'; ex = existing(k, k)
    z(k, 0, ex[0].html, 'supplement', EXIST); z(k, 1, ex[1].html, 'supplement', EXIST); head(k, 2); note(k, 3, '升級時，系統會提示你選擇專精')
    k = 'Sneak Attack'; ex = existing(k, k)
    for i in range(4):
        h = ex[i].html
        if i == 1:
            for a_, b_ in (('目標的5呎內至少有一名同伴，且其未陷入無力狀態', '你的盟友中至少有一人與目標相距不超過5呎，且其未陷入失能狀態'),):
                assert h.count(a_) == 1, h; h = h.replace(a_, b_)
        z(k, i, h, 'supplement', EXIST + ('；使用者 2026-10-09 裁定修正（同伴→盟友、無力→失能、5呎句式）' if i == 1 else ''))
    head(k, 4); note(k, 5, '你的偷襲傷害會')
    k = "Thieves' Cant"; ex = existing(k, k)
    z(k, 0, ex[0].html, 'supplement', EXIST); head(k, 1); note(k, 2, '盜賊黑話會自動')
    k = 'Cunning Action'; ex = existing(k, k)
    t = ex[0].html; cut = '疾走、撤離或躲藏。'
    assert cut in t
    z(k, 0, t.split(cut)[0] + '&amp;Reference[Dash]{疾走}、&amp;Reference[Disengage]{撤離}或&amp;Reference[Hide]{躲藏}。', 'supplement',
      EXIST + '；移除尾端殘留的原始 Reference 標記，補回 {中文} 標籤')
    for key in E[k]['activities']: E[k]['activities'][key]['name'] = cur['entries.Cunning Action.activities.%s.name' % key]
    for key in E[k]['effects']: E[k]['effects'][key]['name'] = cur['entries.Cunning Action.effects.%s.name' % key]
    jdump(s, P + '.sheet.json')

    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'build', P + '.sheet.json', '--draft', P + '.draft.txt',
                           '--out', P + '.aligned.json'], stdout=subprocess.DEVNULL)
    rc = subprocess.call([sys.executable, os.path.join(SK, 'validate.py'), P + '.aligned.json', '--book', BOOK, '--component', 'classes',
                          '--allow', 'Foundry,Active,Effect,lookup,scale,rogue,item,activity,Cunning,Sneak,Attack', '--out', P + '.upload.json'])
    assert rc == 0
    up = jload(P + '.upload.json')['entries']

    # names already translated in Weblate must not be re-sent as changes: keep them (identical values are skipped by Weblate)
    # Rogue: advancement names only
    w = sec['Rogue']; adv_en = en['Rogue']['advancement']
    nl = [l for l in w['sup'] if l.startswith('升級項目名稱：')][0].split('：', 1)[1]
    names = parts(nl); nkeys = [x for x in adv_en if 'name' in adv_en[x]]
    assert len(names) == len(nkeys), (len(names), nkeys)
    entry = {'advancement': {x: {'name': n} for x, n in zip(nkeys, names)}}
    assert not validate.check_subfields(entry, en['Rogue'])
    sl = cur['entries.Rogue.advancement.FiaNLovfP6tnY4tD.hint']
    entry['advancement']['FiaNLovfP6tnY4tD'] = {'hint': sec['Slippery Mind']['sup'][[x.startswith('升級項目提示：') for x in sec['Slippery Mind']['sup']].index(True)].split('：', 1)[1]}
    entry['description'] = fix_rogue_class(cur, en)
    up['Rogue'] = entry
    up['Steady Aim'] = {'name': '手穩就準'}

    b1 = {k: up[k] for k in BATCH1}
    b2 = {k: v for k, v in up.items() if k not in BATCH1}
    for n, d in (('1', b1), ('2', b2)):
        f = os.path.join(INC, 'classes.rogue.%s.upload.json' % n)
        jdump({'entries': d}, f)
        print('batch', n, len(d), 'entries', validate.count_strings(d), 'strings', hashlib.sha256(open(f, 'rb').read()).hexdigest())


def checks():
    s = jload(P + '.sheet.json')
    s['entries'] = {(DRAFT_NAME.get(k, k)): v for k, v in s['entries'].items() if k not in KEEP_KEYS}
    jdump(s, P + '.terms-sheet.json')
    if not os.path.exists(P + '.ack.json'): jdump({}, P + '.ack.json')
    run = lambda *a: subprocess.call([sys.executable] + list(a))
    run(os.path.join(SK, 'spell_names.py'), '--out', os.path.join(INC, 'spell-names.json'))
    run(os.path.join(SK, 'terms_check.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt', '--index', P + '.term_index.json',
        '--names', os.path.join(INC, 'spell-names.json'), '--ack', P + '.ack.json', '--out', P + '.terms-report.md')
    run(os.path.join(SK, 'draft_diff.py'), '--source', os.path.join(INC, '_source', 'rogue.prep.txt'), '--draft', P + '.draft.txt',
        '--supplements', 'Rogue,Expertise,Sneak Attack,Thieves\' Cant,Cunning Action', '--out', P + '.draft-diff.md')
    out = subprocess.run([sys.executable, os.path.join(SK, 'lang_compare.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt'],
                         capture_output=True, text=True, encoding='utf-8').stdout
    open(P + '.lang-compare.md', 'w', encoding='utf-8').write(out)
    cur = live('classes')
    src = {r['context']: r['source'][0] for r in weblate.paged('/api/translations/%s/%s-classes/zh_Hant/units/' % (BOOK, BOOK))}
    def walk(x, p):
        for k, v in x.items():
            if isinstance(v, dict): yield from walk(v, p + k + '.')
            else: yield p + k, v
    for n in ('1', '2'):
        raw = open(os.path.join(INC, 'classes.rogue.%s.upload.json' % n), encoding='utf-8').read()
        print('batch', n, 'forbidden:', [w for w in ['它', '如果', '施展', '發充能', '尺', '抗性', '等於', '亡靈', '成分', '妳', '倒地', '無需'] if w in raw])
        c = {'same': 0, 'new': 0, 'over': 0}
        for pth, v in walk(json.loads(raw)['entries'], 'entries.'):
            assert pth in cur, pth
            key = 'same' if cur[pth] == v else ('new' if cur[pth] == src[pth] else 'over')
            c[key] += 1
            if key == 'over': print('  OVER', pth, '|', cur[pth][:50].replace(chr(10), ' '))
        print('  ', c)


def prep():
    """Rogue source: s2twp conversion + headings 'zh English' for draft_diff."""
    import opencc
    src = os.path.join(INC, 'rogue.txt')
    conv = opencc.OpenCC('s2twp').convert(open(src, encoding='utf-8').read())
    open(os.path.join(INC, '_source', 'rogue.s2twp.txt'), 'w', encoding='utf-8', newline='').write(conv)
    L = conv.replace(chr(13), '').split(chr(10))
    def r(a, b): return [x for x in L[a - 1:b] if x.strip()]
    secs = [('詭詐打擊 Cunning Strike', r(84, 88)), ('強化詭詐打擊 Improved Cunning Strike', r(100, 100)), ('兇狡打擊 Devious Strikes', r(103, 106)),
            ('直覺閃避 Uncanny Dodge', r(91, 91)), ('反射閃避 Evasion', r(94, 94)), ('可靠才能 Reliable Talent', r(97, 97)),
            ('圓滑心智 Slippery Mind', r(109, 109)), ('飄忽不定 Elusive', r(112, 112)), ('傳奇恩惠 Epic Boon', r(115, 115)),
            ('幸運一擊 Stroke of Luck', r(118, 119)), ('專精 Expertise', r(55, 57)), ('偷襲 Sneak Attack', r(60, 62)),
            ("盜賊黑話 Thieves' Cant", r(65, 65)), ('靈巧動作 Cunning Action', r(72, 72)), ('遊蕩者 Rogue', r(75, 75))]
    out = []
    for h, ls in secs: out += [h] + ls + ['']
    open(os.path.join(INC, '_source', 'rogue.prep.txt'), 'w', encoding='utf-8', newline=chr(10)).write(chr(10).join(out))
    subprocess.call([sys.executable, os.path.join(SK, 'build_index.py'), '--skip-book', 'player-handbook', '--out', P + '.term_index.json'])


def content():
    """Rogue journal page (name/description/subclass) from the reviewed classes translation + subclass page names."""
    C = os.path.join(INC, 'content.rogue.3')
    en = jload(CONTENT_EN)['entries']['Rogue']['pages']
    cl = live('classes'); cu = live('content')
    ex = Plan(cl['entries.Rogue.description']).blocks
    assert len(ex) == 28
    strip = lambda h: re.sub(r'@UUID\[[^\]]+\]\{([^}]*)\}', lambda m: m.group(1), h)
    vis = lambda h: re.sub(r'<[^>]+>', '', strip(h)).strip()
    idx = list(range(18, 28))
    subs = {'Arcane Trickster': 'x', 'Assassin': 'x', 'Soulknife': 'x', 'Thief': 'x'}
    sub_names = [cl['entries.%s.name' % k_] for k_ in subs]
    subline = '遊蕩者子職業是一種特化，在特定等級給予你對應的特性，具體內容見各子職業的說明。接下來的頁面介紹' + '、'.join(sub_names[:3]) + '和' + sub_names[3] + '這四種子職業。'
    NL = chr(10)
    open(C + '.draft.txt', 'w', encoding='utf-8', newline=NL).write(NL.join(['### Rogue.description'] + [vis(ex[i].html) for i in idx] + ['', '### Rogue.subclass', subline, '']))
    sec = {}; cur_ = None
    for l in open(C + '.draft.txt', encoding='utf-8'):
        l = l.rstrip(NL); m = re.match(r'### (.+)', l)
        if m: cur_ = m.group(1); sec[cur_] = []
        elif l.strip() and cur_: sec[cur_].append(l.strip())
    zh = [None] + [strip(ex[i].html) for i in idx] + [None]
    assert zh[1].startswith('遊蕩者們')
    fx = {'作為遊蕩者…': '成為遊蕩者…', '通常都無法匹敵': '都無法匹敵'}
    for j in range(len(zh)):
        if zh[j]:
            for a_, b_ in fx.items(): zh[j] = zh[j].replace(a_, b_)
    sec['Rogue.description'] = [x.replace('作為遊蕩者…', '成為遊蕩者…').replace('通常都無法匹敵', '都無法匹敵') for x in sec['Rogue.description']]
    zh[1] = zh[1].replace('遊蕩者', lab('classes.Item.phbrgeRogue00000', '遊蕩者'), 1)
    bl = Plan(en['Rogue']['description']).blocks; assert len(bl) == 12
    def rows(html, zhs):
        b_ = Plan(html).blocks; assert len(b_) == len(zhs), (len(b_), len(zhs))
        return [{'id': b.id, 'en': b.html, 'zh': (b.html if z is None else z), 'source': 'draft', 'basis': ''} for b, z in zip(b_, zhs)]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en['Rogue']['subclass']); assert len(uu) == 4
    z2 = subline
    for n_, u in zip(sub_names, uu): z2 = z2.replace(n_, '@UUID[%s]{%s}' % (u, n_), 1)
    sheet = {'schema_version': 2, 'book': BOOK, 'component': 'content', 'entries': {
        'Rogue.description': {'name_en': 'Rogue', 'name': '遊蕩者', 'blocks': rows(en['Rogue']['description'], zh)},
        'Rogue.subclass': {'name_en': 'Rogue', 'name': '遊蕩者', 'blocks': rows(en['Rogue']['subclass'], [z2, None])}}}
    adapter = {'Rogue.description': {'description': en['Rogue']['description']}, 'Rogue.subclass': {'description': en['Rogue']['subclass']}}
    draft = {k_: re.sub(r'\s+', '', ''.join(v)) for k_, v in sec.items()}
    out = skeleton.build_entries(sheet, adapter, draft)['entries']
    allow = validate.ALLOWED_ENGLISH | {'Embed', 'Compendium', 'caption', 'false', 'classes', 'three', 'right'}
    pages = {'Rogue': {'name': '遊蕩者'}}
    for k_, v in out.items():
        probs = validate.check_description(adapter[k_]['description'], v['description'], allow)
        print(k_, probs); assert not probs
        pages['Rogue'][k_.split('.')[1]] = v['description']
    for pg in subs:
        assert pg in en; pages[pg] = {'name': cl['entries.%s.name' % pg]}
    payload = {'entries': {'Rogue': {'pages': pages}}}
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
    {'classes': classes, 'checks': checks, 'prep': prep, 'content': content}[sys.argv[1]]()
