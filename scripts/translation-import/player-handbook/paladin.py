"""Paladin (player-handbook) batches. Paths resolve from this file; nothing here uploads.

  python paladin.py prep      -> source conversion/headings, term index
  python paladin.py classes   -> classes.paladin.{1,2}.upload.json
  python paladin.py checks    -> terms / draft_diff / lang_compare / payload path audit
  python paladin.py content   -> content.paladin.3.upload.json
"""
import hashlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sorcerer import fix_labeled
from warlock import (ROOT, SK, INC, BOOK, CLASSES_EN, CONTENT_EN, SUP, EXIST, jload, jdump, B, lab, parts, read_draft, live,
                     validate, skeleton, weblate, Plan)

FULL = ['Abjure Foes', 'Aura of Courage', 'Aura of Protection', 'Faithful Steed', 'Radiant Strikes', 'Restoring Touch', 'Aura Expansion',
        'phbpdnEpicBoon00']
KEEP = ['Lay on Hands', "Paladin's Smite", 'phbpdnChannelDiv', 'phbpdnFightingSt']
DRAFT_NAME = {'phbpdnEpicBoon00': 'Epic Boon', 'phbpdnChannelDiv': 'Channel Divinity', 'phbpdnFightingSt': 'Fighting Style'}
FIX = {'Lay on Hands': [('能量池可恢復生命值的總數等於你聖騎士等級的五倍。', '')],
       'phbpdnChannelDiv': [('引導神兩次', '引導神力兩次'), ('無力狀態', '失能狀態')],
       'phbpdnFightingSt': [('以下選項', '下列選項')]}
BATCHES = {'1': FULL, '2': KEEP + ['phbpdnSpellcasti', 'Paladin']}
P = os.path.join(INC, 'classes.paladin.1')
NL = chr(10)


def prep():
    import opencc
    conv = opencc.OpenCC('s2twp').convert(open(os.path.join(INC, 'paladin.txt'), encoding='utf-8').read())
    os.makedirs(os.path.join(INC, '_source'), exist_ok=True)
    open(os.path.join(INC, '_source', 'paladin.s2twp.txt'), 'w', encoding='utf-8', newline='').write(conv)
    L = conv.replace(chr(13), '').split(NL)
    def r(a, b): return [x for x in L[a - 1:b] if x.strip()]
    secs = [('棄絕眾敵 Abjure Foes', r(111, 111)), ('勇氣靈光 Aura of Courage', r(114, 114)), ('守護靈光 Aura of Protection', r(106, 108)),
            ('信實坐騎 Faithful Steed', r(103, 103)), ('光耀打擊 Radiant Strikes', r(117, 117)), ('復原之觸 Restoring Touch', r(120, 120)),
            ('靈光增效 Aura Expansion', r(123, 123)), ('傳奇恩惠 Epic Boon', r(126, 126)), ('聖療 Lay on Hands', r(56, 58)),
            ('聖騎士斬技 Paladins Smite', r(79, 79)), ('引導神力 Channel Divinity', r(82, 86)), ('聖騎士 Paladin', r(2, 2))]
    out = []
    for h, ls in secs: out += [h] + ls + ['']
    open(os.path.join(INC, '_source', 'paladin.prep.txt'), 'w', encoding='utf-8', newline=NL).write(NL.join(out))
    subprocess.call([sys.executable, os.path.join(SK, 'build_index.py'), '--skip-book', 'player-handbook', '--out', P + '.term_index.json'])


def classes():
    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'extract', '--book', BOOK, '--component', 'classes', '--keys']
                          + FULL + KEEP + ['--out', P + '.sheet.json'], stdout=subprocess.DEVNULL)
    s = jload(P + '.sheet.json'); E = s['entries']
    sec = read_draft(P + '.draft.txt')
    en = jload(CLASSES_EN)['entries']
    cur = live('classes')
    sn = jload(os.path.join(INC, 'spell-names.json'))
    H = B('【Foundry註記】')
    def D(k): return sec.get(k) or sec[DRAFT_NAME[k]]
    def z(k, i, zh, src='draft', basis=''):
        b = E[k]['blocks'][i]; b['zh'] = zh; b['source'] = src; b['basis'] = basis
    def sline(k, prefix):
        h = [l for l in D(k)['sup'] if l.startswith(prefix)]; assert len(h) == 1, (k, prefix); return h[0].split('：', 1)[1]
    def nm(k): E[k]['name'] = D(k)['name']
    def named_notes(k): return [l for l in D(k)['sup'] if not l.startswith(('【Foundry', '行動', '效果', '升級項目'))]
    def bold(t_, phrase):
        assert phrase in t_, (t_, phrase); return t_.replace(phrase, B(phrase), 1)
    def ref(t_, plain, token, label):
        assert t_.count(plain) == 1, (t_, plain)
        return t_.replace(plain, plain.replace(label, '&amp;Reference[%s]{%s}' % (token, label)))
    def spell(k, t_, zhname):
        uid = re.findall(r'@UUID\[([^\]]+spells[^\]]+)\]', en[k]['description']); assert len(uid) == 1, (k, uid)
        assert t_.count(zhname) == 1, (t_, zhname)
        return t_.replace(zhname, '@UUID[%s]{%s}' % (uid[0], zhname), 1)

    # ---------- FULL entries ----------
    k = 'Abjure Foes'; nm(k); body = D(k)['main'][0]
    z(k, 0, ref(body, '陷入恐慌狀態', 'Frightened', '恐慌')); z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)
    E[k]['activities']['save']['target'] = sline(k, '行動目標：')
    E[k]['effects']['Abjured']['name'] = cur['entries.Abjure Foes.effects.Abjured.name']

    k = 'Aura of Courage'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)
    E[k]['activities']['Aura of Courage']['name'] = cur['entries.Aura of Courage.activities.Aura of Courage.name']
    E[k]['effects']['Courageous']['name'] = cur['entries.Aura of Courage.effects.Courageous.name']

    k = 'Aura of Protection'; nm(k); M = D(k)['main']
    z(k, 0, ref(M[0], '陷入失能狀態', 'Incapacitated apply=false', '失能')); z(k, 1, M[1], 'supplement', '含 [[lookup]] 巨集的區塊；句子取自底稿，巨集原樣保留'); z(k, 2, M[2])
    z(k, 3, H, 'supplement', SUP); z(k, 4, named_notes(k)[0], 'supplement', SUP)
    E[k]['effects']['Protected']['name'] = sline(k, '效果：')

    k = 'Faithful Steed'; nm(k); M = D(k)['main']
    z(k, 0, spell(k, M[0], '尋獲坐騎')); z(k, 1, M[1]); z(k, 2, H, 'supplement', SUP); z(k, 3, named_notes(k)[0], 'supplement', SUP)

    k = 'Radiant Strikes'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)
    E[k]['effects']['Radiant Strikes']['name'] = sline(k, '效果：')

    k = 'Restoring Touch'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)

    k = 'Aura Expansion'; nm(k); z(k, 0, D(k)['main'][0]); z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)

    k = 'phbpdnEpicBoon00'; nm(k); body = D(k)['main'][0]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en[k]['description']); assert len(uu) == 2
    z(k, 0, body.replace('傳奇恩惠專長', '@UUID[%s]{傳奇恩惠專長}' % uu[0], 1).replace('真視恩惠', '@UUID[%s]{真視恩惠}' % uu[1], 1))
    z(k, 1, H, 'supplement', SUP); z(k, 2, named_notes(k)[0], 'supplement', SUP)

    # ---------- KEEP entries: existing body (with listed fixes + labels), translated notes / nested names ----------
    def ex_blocks(k): return Plan(cur['entries.%s.description' % k]).blocks
    for k in KEEP:
        nm(k) if k in sec or k in DRAFT_NAME else E[k].__setitem__('name', cur['entries.%s.name' % k])
        ex = ex_blocks(k); bl = E[k]['blocks']; assert len(ex) == len(bl), (k, len(ex), len(bl))
        hi = next((i for i, b in enumerate(bl) if b['en'].startswith('<strong>Foundry')), len(bl))
        htmls = [b_.html for b_ in ex]
        for a_, b_ in FIX.get(k, []):
            assert sum(h.count(a_) for h in htmls) == 1, (k, a_)
            htmls = [h.replace(a_, b_) for h in htmls]
        for uid, label in re.findall(r'@UUID\[([^\]]+spells\.Item[^\]]+)\]\{([^}]*)\}', en[k]['description']):
            old = '@UUID[%s]' % uid
            htmls = [re.sub(re.escape(old) + r'(?!\{)', lambda m_: old + '{%s}' % sn[label], h) for h in htmls]
        for i in range(hi): z(k, i, htmls[i], 'supplement', EXIST + ('；修正既有譯文錯誤' if k in FIX and k != 'phbpdnFightingSt' else '；使用者慣例（以下→下列）' if k in FIX else ''))
        if hi < len(bl):
            z(k, hi, H, 'supplement', SUP)
            nn = named_notes(k); assert len(nn) == len(bl) - hi - 1, (k, nn)
            for j, t_ in enumerate(nn):
                if k == 'Lay on Hands': t_ = bold(t_, ['治療', '移除毒素'][j])
                if k == 'phbpdnChannelDiv' and j == 1: t_ = bold(t_, '神聖感知')
                z(k, hi + 1 + j, t_, 'supplement', SUP)
    k = 'phbpdnChannelDiv'
    E[k]['activities']['Divine Sense']['name'] = sline(k, '行動：'); E[k]['effects']['Divine Sense']['name'] = sline(k, '效果：')
    E['Lay on Hands']['activities']['Remove Poison']['name'] = cur['entries.Lay on Hands.activities.Remove Poison.name']
    jdump(s, P + '.sheet.json')

    subprocess.check_call([sys.executable, os.path.join(SK, 'skeleton.py'), 'build', P + '.sheet.json', '--draft', P + '.draft.txt',
                           '--out', P + '.aligned.json'], stdout=subprocess.DEVNULL)
    rc = subprocess.call([sys.executable, os.path.join(SK, 'validate.py'), P + '.aligned.json', '--book', BOOK, '--component', 'classes',
                          '--allow', 'Foundry,Active,Effect,lookup,scale,Scale,classes,paladin', '--out', P + '.upload.json'])
    assert rc == 0
    up = jload(P + '.upload.json')['entries']
    w = sec['Paladin']; adv_en = en['Paladin']['advancement']
    names = parts([l for l in w['sup'] if l.startswith('升級項目名稱：')][0].split('：', 1)[1])
    nkeys = [x for x in adv_en if 'name' in adv_en[x]]
    assert len(names) == len(nkeys), (len(names), nkeys)
    entry = {'advancement': {x: {'name': n} for x, n in zip(nkeys, names)}}
    assert not validate.check_subfields(entry, en['Paladin'])
    entry['description'] = fix_labeled(cur, en, 'Paladin', PALADIN_FIX)
    assert entry['description'].count('phbarmShield0000]{護盾術}') == 1   # equipment name in Weblate is the spell name; armor Shield = 盾牌 (conventions)
    entry['description'] = entry['description'].replace('phbarmShield0000]{護盾術}', 'phbarmShield0000]{盾牌}')
    up['Paladin'] = entry
    up['phbpdnSpellcasti'] = {'description': fix_labeled(cur, en, 'phbpdnSpellcasti', SPELL_FIX)}
    jdump({'entries': up}, P + '.all.json')
    for n_, ks in BATCHES.items():
        d_ = {k_: up[k_] for k_ in ks}
        f_ = os.path.join(INC, 'classes.paladin.%s.upload.json' % n_)
        jdump({'entries': d_}, f_)
        print('batch', n_, len(d_), 'entries', validate.count_strings(d_), 'strings', hashlib.sha256(open(f_, 'rb').read()).hexdigest())


PALADIN_FIX = [('遊說', '說服')]
SPELL_FIX = [('以下資訊', '下列資訊')]


def checks():
    s = jload(P + '.sheet.json')
    s['entries'] = {(DRAFT_NAME.get(k, k)): v for k, v in s['entries'].items() if k in FULL}
    jdump(s, P + '.terms-sheet.json')
    if not os.path.exists(P + '.ack.json'): jdump({}, P + '.ack.json')
    run = lambda *a: subprocess.call([sys.executable] + list(a))
    run(os.path.join(SK, 'spell_names.py'), '--out', os.path.join(INC, 'spell-names.json'))
    run(os.path.join(SK, 'terms_check.py'), P + '.terms-sheet.json', '--draft', P + '.draft.txt', '--index', P + '.term_index.json',
        '--names', os.path.join(INC, 'spell-names.json'), '--ack', P + '.ack.json', '--out', P + '.terms-report.md')
    run(os.path.join(SK, 'draft_diff.py'), '--source', os.path.join(INC, '_source', 'paladin.prep.txt'), '--draft', P + '.draft.txt',
        '--supplements', 'Lay on Hands,Paladins Smite,Channel Divinity,Fighting Style,Paladin', '--out', P + '.draft-diff.md')
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
    print('forbidden:', [w for w in ['它', '如果', '施展', '發充能', '尺', '抗性', '等於', '亡靈', '成分', '妳', '倒地', '以下', '法術槽', '無力'] if w in raw])
    c = {'same': 0, 'new': 0, 'over': 0}
    for pth, v in walk(json.loads(raw)['entries'], 'entries.'):
        assert pth in cur, pth
        key = 'same' if cur[pth] == v else ('new' if cur[pth] == src[pth] else 'over')
        c[key] += 1
        if key == 'over': print('  OVER', pth, '|', cur[pth][:50].replace(NL, ' '))
    print(c)


def content():
    C = os.path.join(INC, 'content.paladin.3')
    en = jload(CONTENT_EN)['entries']['Paladin']['pages']
    cl = live('classes'); cu = live('content')
    ex = Plan(cl['entries.Paladin.description']).blocks
    assert len(ex) == 30, len(ex)
    strip = lambda h: re.sub(r'@UUID\[[^\]]+\]\{([^}]*)\}', lambda m: m.group(1), h)
    vis = lambda h: re.sub(r'<[^>]+>', '', strip(h)).strip()
    idx = list(range(16, 26))
    subs = ['Oath of Devotion', 'Oath of Glory', 'Oath of the Ancients', 'Oath of Vengeance']
    sub_names = [cl['entries.%s.name' % k_] for k_ in subs]
    subline = '聖騎士子職業是一種特化，在特定等級給予你對應的特性，具體內容見各子職業的說明。接下來的頁面介紹' + '、'.join(sub_names[:3]) + '和' + sub_names[3] + '這四種子職業。'
    lines = ['### Paladin.description'] + [vis(ex[i].html) for i in idx] + ['', '### Paladin.subclass', subline, '']
    open(C + '.draft.txt', 'w', encoding='utf-8', newline=NL).write(NL.join(lines))
    sec = {}; cur_ = None
    for l in open(C + '.draft.txt', encoding='utf-8'):
        l = l.rstrip(NL); m = re.match(r'### (.+)', l)
        if m: cur_ = m.group(1); sec[cur_] = []
        elif l.strip() and cur_: sec[cur_].append(l.strip())
    zh = [None, None] + [strip(ex[i].html) for i in idx]
    # the first paragraph of the EN page links the class actor
    uid = re.findall(r'@UUID\[([^\]]+)\]', en['Paladin']['description']); assert len(uid) == 1
    zh[2] = zh[2].replace('聖騎士', '@UUID[%s]{聖騎士}' % uid[0], 1)
    def rows(html, zhs):
        b_ = Plan(html).blocks; assert len(b_) == len(zhs), (len(b_), len(zhs))
        return [{'id': b.id, 'en': b.html, 'zh': (b.html if z is None else z), 'source': 'draft', 'basis': ''} for b, z in zip(b_, zhs)]
    uu = re.findall(r'@UUID\[([^\]]+)\]', en['Paladin']['subclass']); assert len(uu) == 4, uu
    z2 = subline
    for n_, u in zip(sub_names, uu): z2 = z2.replace(n_, '@UUID[%s]{%s}' % (u, n_), 1)
    nsub = len(Plan(en['Paladin']['subclass']).blocks)
    sheet = {'schema_version': 2, 'book': BOOK, 'component': 'content', 'entries': {
        'Paladin.description': {'name_en': 'Paladin', 'name': '聖騎士', 'blocks': rows(en['Paladin']['description'], zh)},
        'Paladin.subclass': {'name_en': 'Paladin', 'name': '聖騎士', 'blocks': rows(en['Paladin']['subclass'], [z2] + [None] * (nsub - 1))}}}
    adapter = {'Paladin.description': {'description': en['Paladin']['description']}, 'Paladin.subclass': {'description': en['Paladin']['subclass']}}
    draft = {k_: re.sub(r'\s+', '', ''.join(v)) for k_, v in sec.items()}
    out = skeleton.build_entries(sheet, adapter, draft)['entries']
    allow = validate.ALLOWED_ENGLISH | {'Embed', 'Compendium', 'caption', 'false', 'classes', 'three', 'right'}
    pages = {'Paladin': {'name': '聖騎士'}}
    for k_, v in out.items():
        probs = validate.check_description(adapter[k_]['description'], v['description'], allow)
        print(k_, probs); assert not probs
        pages['Paladin'][k_.split('.')[1]] = v['description']
    for pg, n_ in zip(subs, sub_names):
        assert pg in en; pages[pg] = {'name': n_}
    payload = {'entries': {'Paladin': {'pages': pages}}}
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
