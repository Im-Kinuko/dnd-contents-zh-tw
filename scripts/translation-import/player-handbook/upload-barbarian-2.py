"""Upload user-approved batch 2 v2 as suggestions, preserving existing targets."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
import weblate as w
from html_blocks import Plan, visible_text

PREFIX = 'classes.barbarian.2'
PROJECT = 'dnd-players-handbook'
COMPONENT = 'dnd-players-handbook-classes'
BASE = '/api/translations/'+PROJECT+'/'+COMPONENT+'/zh_Hant/'
EXPECTED_HASH = '1aa13347ff47f6aa0d0cf1548f382fff232209bf1144d25e9d022ffd1be80577'
PAYLOAD = HERE/(PREFIX+'.upload.json')
def load(suffix):
    return json.loads((HERE/(PREFIX+'.'+suffix+'.json')).read_text(encoding='utf-8'))
def save(suffix,value):
    (HERE/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def leaves(node,prefix=''):
    if isinstance(node,dict):
        for key,value in node.items():
            yield from leaves(value,prefix+'.'+key if prefix else key)
    elif isinstance(node,str):
        yield prefix,node

assert hashlib.sha256(PAYLOAD.read_bytes()).hexdigest() == EXPECTED_HASH
expected = dict(leaves(load('upload')))
previous = dict(leaves(load('v1.upload')))
assert len(expected)==29 and set(expected)==set(previous)
changed = [key for key in expected if expected[key] != previous[key]]
assert changed==['entries.Brutal Strike.description'],changed
before_blocks = Plan(previous[changed[0]]).blocks
after_blocks = Plan(expected[changed[0]]).blocks
assert len(before_blocks)==len(after_blocks)
assert before_blocks[1:]==after_blocks[1:],'Other Brutal Strike blocks changed'
approval = load('approval')
mapped = next(row for row in load('mapping-audit') if row['path']=='Brutal Strike.description/b0001')
assert visible_text(mapped['zh'])==visible_text(approval['approved_paragraph'])
assert approval['approved'] and approval['version']=='v2'
save('revision-audit',{'changed_fields':changed,'only_first_block_changed':True,'other_28_strings_unchanged':True,'exact_user_paragraph':True,'sha256':EXPECTED_HASH})

def get_units():
    result, all_units, page = {}, {}, 1
    while True:
        status,body = w.call('GET',BASE+'units/?page_size=1000&page='+str(page))
        assert status==200,('units',status)
        for unit in body['results']:
            all_units[unit['context']] = unit
            if unit['context'] in expected:
                result[unit['context']] = unit
        if not body.get('next'):
            assert len(all_units)==body['count']
            break
        page+=1
    assert set(result)==set(expected),sorted(set(expected)-set(result))
    stats = {'component_total':len(all_units),'component_empty_or_source':sum(not any(u['target']) or u['target']==u['source'] for u in all_units.values()),'batch_strings':len(result),'batch_empty_or_source':sum(not any(u['target']) or u['target']==u['source'] for u in result.values()),'batch_has_suggestion':sum(u['has_suggestion'] for u in result.values())}
    save('statistics-latest',stats)
    return result,all_units

mode = sys.argv[1]
if mode=='preflight':
    status,translation = w.call('GET',BASE)
    assert status==200 and translation['filename']=='compendium/zh-tw/dnd-players-handbook/dnd-players-handbook.classes.json'
    status,component = w.call('GET','/api/components/'+PROJECT+'/'+COMPONENT+'/')
    assert status==200 and component.get('push')
    status,repo = w.call('GET','/api/components/'+PROJECT+'/'+COMPONENT+'/repository/')
    assert status==200 and not repo.get('merge_failure')
    units,all_units = get_units()
    approved_en = load('weblate')['units']
    for context,unit in units.items():
        assert unit['source']==approved_en[context]['source'],'EN changed: '+context
    save('before',units)
    save('component-before',all_units)
    record = {'version':'v2','sha256':EXPECTED_HASH,'filename':translation['filename'],'push_url_set':bool(component.get('push')),'repository':{key:repo.get(key) for key in ['needs_commit','needs_push','needs_merge','merge_failure']},'matched_strings':len(units),'approved_by':approval,'same_target':[k for k,u in units.items() if u['target']==[expected[k]]],'prior_suggestions':[k for k,u in units.items() if u['has_suggestion']]}
    save('preflight',record)
    print(json.dumps({k:v for k,v in record.items() if k!='approved_by'},ensure_ascii=False))
elif mode=='upload':
    assert load('preflight')['sha256']==EXPECTED_HASH
    assert not (HERE/(PREFIX+'.upload-response.json')).exists(),'Already attempted; investigate before retry.'
    status,body = w.upload(PROJECT,COMPONENT,str(PAYLOAD),method='suggest')
    save('upload-response',{'http_status':status,'response':body,'sha256':EXPECTED_HASH,'method':'suggest'})
    print(json.dumps({'http_status':status,'response':body},ensure_ascii=False))
    assert status in [200,201],'Investigate response; do not blindly retry.'
elif mode=='audit':
    after,component_after = get_units()
    save('after',after)
    before = load('before')
    component_before = load('component-before')
    assert set(component_before)==set(component_after)
    for context,unit in component_after.items():
        assert unit['source']==component_before[context]['source'],'Component source changed: '+context
        assert unit['target']==component_before[context]['target'],'Existing translation changed: '+context
    accepted,skipped = [],[]
    for context,target in expected.items():
        if after[context]['target']==[target]:
            skipped.append({'context':context,'reason':'現行譯文與payload完全相同。'})
        else:
            assert not before[context]['has_suggestion'] and after[context]['has_suggestion'],'Suggestion requires inspection: '+context
            accepted.append({'context':context,'unit_id':after[context]['id'],'reason':'上傳前無建議，上傳後has_suggestion；現行source及target不變。'})
    response = load('upload-response')['response']
    assert len(accepted)==response['accepted']
    assert len(skipped)==response['skipped']
    assert response['not_found']==0 and len(accepted)+len(skipped)==29
    record = {'accepted':accepted,'skipped':skipped,'not_found':[],'verified_strings':29,'component_verified_strings':len(component_after),'all_targets_unchanged':True,'complete':True}
    save('upload-audit',record)
    print(json.dumps({'accepted':len(accepted),'skipped_same_translation':len(skipped),'not_found':0,'component_verified_strings':len(component_after),'all_targets_unchanged':True},ensure_ascii=False))
else:
    raise ValueError(mode)
