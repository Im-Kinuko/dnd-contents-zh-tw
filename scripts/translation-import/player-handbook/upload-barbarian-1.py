"""Upload only the human-approved v1, as suggestions, and verify individual units."""
import concurrent.futures, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
sys.path.insert(0, str(ROOT/'.claude/skills/translation-import/scripts'))
import weblate as w

PROJECT = 'dnd-players-handbook'
COMPONENT = 'dnd-players-handbook-classes'
BASE = '/api/translations/'+PROJECT+'/'+COMPONENT+'/zh_Hant/'
EXPECTED_HASH = '237a0b3963021a275474197d8c8b35e6f5beccf650e221786567f5a6e1aeb10e'
PAYLOAD = HERE/'classes.barbarian.1.upload.json'
PREFIX = 'classes.barbarian.1'

def save(name,value):
    (HERE/(PREFIX+'.'+name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')

def leaves(value,prefix=''):
    if isinstance(value,dict):
        for key,child in value.items():
            yield from leaves(child,prefix+'.'+key if prefix else key)
    elif isinstance(value,str):
        yield prefix,value

assert hashlib.sha256(PAYLOAD.read_bytes()).hexdigest() == EXPECTED_HASH
expected = dict(leaves(json.loads(PAYLOAD.read_text(encoding='utf-8'))))
assert len(expected) == 43

def get_units():
    result, page, count = {}, 1, 0
    untranslated = 0
    remaining_keys = ['Instinctive Pounce','Brutal Strike','Relentless Rage','Improved Brutal Strike','Persistent Rage','Improved Brutal Strike (2)','Indomitable Might','Epic Boon','Primal Champion']
    remaining_units = []
    while True:
        status,body = w.call('GET',BASE+'units/?page_size=1000&page='+str(page))
        assert status == 200, ('units',status)
        count += len(body['results'])
        for unit in body['results']:
            is_untranslated = not any(unit['target']) or unit['target'] == unit['source']
            untranslated += int(is_untranslated)
            if any(unit['context'].startswith('entries.'+key+'.') for key in remaining_keys):
                remaining_units.append({'context':unit['context'],'untranslated':is_untranslated,'has_suggestion':unit['has_suggestion']})
            if unit['context'] in expected:
                result[unit['context']] = unit
        if not body.get('next'):
            assert count == body['count']
            break
        page += 1
    assert set(result) == set(expected), sorted(set(expected)-set(result))
    save('statistics-latest',{'component_total':count,'component_empty_or_source':untranslated,'next_batch_strings':len(remaining_units),'next_batch_empty_or_source':sum(row['untranslated'] for row in remaining_units),'next_batch_units':remaining_units})
    return result

mode = sys.argv[1]
if mode == 'preflight':
    status,translation = w.call('GET',BASE)
    assert status == 200
    assert translation['filename'] == 'compendium/zh-tw/dnd-players-handbook/dnd-players-handbook.classes.json'
    status,component = w.call('GET','/api/components/'+PROJECT+'/'+COMPONENT+'/')
    assert status == 200 and component.get('push')
    status,repo = w.call('GET','/api/components/'+PROJECT+'/'+COMPONENT+'/repository/')
    # Pending remote updates do not block database-only suggestions. Record the
    # state; do not pull, merge, commit or push during this upload.
    assert status == 200 and not repo.get('merge_failure')
    units = get_units()
    approved_en = json.loads((HERE/'barbarian.weblate_units.json').read_text(encoding='utf-8'))['units']
    for context,unit in units.items():
        assert unit['source'] == approved_en[context]['source'], 'EN changed: '+context
    save('before',units)
    save('preflight',{'sha256':EXPECTED_HASH,'filename':translation['filename'],'push_url_set':bool(component.get('push')),'repository':{key:repo.get(key) for key in ['needs_commit','needs_push','needs_merge','merge_failure']},'matched_strings':len(units),'approved_by':'Human user message: 上傳','approval_date':'2026-10-08'})
    first = next(iter(units.values()))
    print(json.dumps({'matched_strings':len(units),'unit_fields':list(first),'sample_id':first['id'],'suggestions':first.get('suggestions')},ensure_ascii=False))
elif mode == 'upload':
    assert (HERE/(PREFIX+'.preflight.json')).is_file()
    status,body = w.upload(PROJECT,COMPONENT,str(PAYLOAD),method='suggest')
    save('upload-response',{'http_status':status,'response':body,'sha256':EXPECTED_HASH,'method':'suggest'})
    print(json.dumps({'http_status':status,'response':body},ensure_ascii=False))
    assert status in [200,201], 'Upload response requires investigation; do not blindly retry.'
elif mode == 'inspect':
    units = get_units()
    save('after',units)
    first = next(iter(units.values()))
    status,body = w.call('GET','/api/units/'+str(first['id'])+'/')
    print(json.dumps({'http_status':status,'unit_fields':list(body) if isinstance(body,dict) else None,'suggestions':body.get('suggestions') if isinstance(body,dict) else None},ensure_ascii=False))
elif mode == 'audit':
    after = get_units()
    save('after',after)
    before = json.loads((HERE/(PREFIX+'.before.json')).read_text(encoding='utf-8'))
    accepted, skipped = [], []
    for context,target in expected.items():
        assert after[context]['target'] == before[context]['target'], 'Existing translation changed: '+context
        assert after[context]['source'] == before[context]['source'], 'Source changed: '+context
        if after[context]['target'] == [target]:
            skipped.append({'context':context,'reason':'現行譯文與本批payload完全相同。'})
        else:
            assert not before[context]['has_suggestion'] and after[context]['has_suggestion'], 'Suggestion not confirmed: '+context
            accepted.append({'context':context,'unit_id':after[context]['id'],'reason':'現行譯文保持不變，上傳後新增has_suggestion。'})
    response = json.loads((HERE/(PREFIX+'.upload-response.json')).read_text(encoding='utf-8'))
    assert len(accepted) == response['response']['accepted'] == 18
    assert len(skipped) == response['response']['skipped'] == 25
    assert response['response']['not_found'] == 0
    save('upload-audit',{'accepted':accepted,'skipped':skipped,'not_found':[],'all_targets_unchanged':True,'verified_strings':43,'complete':True})
    print(json.dumps({'accepted':len(accepted),'skipped_same_translation':len(skipped),'not_found':0,'all_targets_unchanged':True},ensure_ascii=False))
else:
    raise ValueError(mode)
