"""Upload the approved journal-page v1 as suggestions and verify existing targets."""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
PREFIX='content.barbarian.3'
PROJECT='dnd-players-handbook'
COMPONENT='dnd-players-handbook-content'
BASE='/api/translations/'+PROJECT+'/'+COMPONENT+'/zh_Hant/'
EXPECTED_HASH='4777737763fbbd100386e822660192126a1c1486a4420362cee9c4a4dc3080cd'
PAYLOAD=HERE/(PREFIX+'.upload.json')
sys.path.insert(0,str(ROOT/'.claude/skills/translation-import/scripts'))
import weblate as w
from validate import check_description
from html_blocks import visible_text
def load(suffix):
    return json.loads((HERE/(PREFIX+'.'+suffix+'.json')).read_text(encoding='utf-8'))
def save(suffix,value):
    (HERE/(PREFIX+'.'+suffix+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
def leaves(node,prefix=''):
    if isinstance(node,dict):
        for key,value in node.items():yield from leaves(value,prefix+'.'+key if prefix else key)
    elif isinstance(node,str):yield prefix,node
assert hashlib.sha256(PAYLOAD.read_bytes()).hexdigest()==EXPECTED_HASH
info=load('verification')
assert info['sha256']==EXPECTED_HASH and info['version']=='v1'
assert hashlib.sha256((HERE/(PREFIX+'.draft.txt')).read_bytes()).hexdigest()==info['draft_sha256']
assert all(info[key] for key in ['mechanical_pass','all_exact_draft_matches','rule_review_complete','terminology_review_complete','chinese_readthrough_complete'])
expected=dict(leaves(load('upload')))
en=dict(leaves(load('en-scope')))
assert len(expected)==5 and set(expected)==set(en)
for path,zh in expected.items():assert not check_description(en[path],zh),path
for row in load('mapping-audit'):assert visible_text(row['zh'])==row['draft']
approval={'version':'v1','date':'2026-10-08','authorization':'上傳','scope':'使用者已看過第3批v1預覽後指示上傳；1個Barbarian日誌條目、1個頁面、5個字串；method=suggest。','sha256':EXPECTED_HASH,'approved':True}

def get_units():
    result,all_units,page={}, {},1
    while True:
        status,body=w.call('GET',BASE+'units/?page_size=1000&page='+str(page))
        assert status==200,('units',status)
        for unit in body['results']:
            all_units[unit['context']]=unit
            if unit['context'] in expected:result[unit['context']]=unit
        if not body.get('next'):
            assert len(all_units)==body['count']
            break
        page+=1
    assert set(result)==set(expected),sorted(set(expected)-set(result))
    save('statistics-latest',{'component_total':len(all_units),'component_empty_or_source':sum(not any(u['target']) or u['target']==u['source'] for u in all_units.values()),'batch_strings':len(result),'batch_empty_or_source':sum(not any(u['target']) or u['target']==u['source'] for u in result.values()),'batch_has_suggestion':sum(u['has_suggestion'] for u in result.values())})
    return result,all_units

mode=sys.argv[1]
if mode=='preflight':
    status,translation=w.call('GET',BASE)
    assert status==200 and translation['filename']=='compendium/zh-tw/dnd-players-handbook/dnd-players-handbook.content.json'
    status,component=w.call('GET','/api/components/'+PROJECT+'/'+COMPONENT+'/')
    assert status==200 and component.get('push')
    status,repo=w.call('GET','/api/components/'+PROJECT+'/'+COMPONENT+'/repository/')
    assert status==200 and not repo.get('merge_failure')
    units,all_units=get_units()
    preview_live=load('content.live')['units']
    for path,unit in units.items():assert unit['source']==preview_live[path]['source']==[en[path]],'EN changed: '+path
    save('before',units)
    save('component-before',all_units)
    save('approval',approval)
    record={'version':'v1','sha256':EXPECTED_HASH,'filename':translation['filename'],'push_url_set':bool(component.get('push')),'repository':{key:repo.get(key) for key in ['needs_commit','needs_push','needs_merge','merge_failure']},'matched_strings':len(units),'approval':approval,'same_target':[k for k,u in units.items() if u['target']==[expected[k]]],'prior_suggestions':[k for k,u in units.items() if u['has_suggestion']]}
    save('preflight',record)
    print(json.dumps({k:v for k,v in record.items() if k!='approval'},ensure_ascii=False))
elif mode=='upload':
    assert load('preflight')['sha256']==EXPECTED_HASH and load('approval')['approved']
    assert not (HERE/(PREFIX+'.upload-response.json')).exists(),'Already attempted; inspect before retry.'
    status,body=w.upload(PROJECT,COMPONENT,str(PAYLOAD),method='suggest')
    save('upload-response',{'http_status':status,'response':body,'sha256':EXPECTED_HASH,'method':'suggest'})
    print(json.dumps({'http_status':status,'response':body},ensure_ascii=False))
    assert status in [200,201],'Investigate response; do not blindly retry.'
elif mode=='audit':
    after,all_after=get_units()
    save('after',after)
    before,all_before=load('before'),load('component-before')
    assert set(all_before)==set(all_after)
    for path,unit in all_after.items():
        assert unit['source']==all_before[path]['source'],'Source changed: '+path
        assert unit['target']==all_before[path]['target'],'Existing target changed: '+path
    accepted,skipped=[],[]
    for path,target in expected.items():
        if after[path]['target']==[target]:
            skipped.append({'context':path,'reason':'現行譯文與確認版本完全相同。'})
        else:
            assert not before[path]['has_suggestion'] and after[path]['has_suggestion'],'Suggestion requires inspection: '+path
            accepted.append({'context':path,'unit_id':after[path]['id'],'reason':'上傳前無建議，上傳後有建議；現行source及target保持不變。'})
    response=load('upload-response')['response']
    assert len(accepted)==response['accepted'] and len(skipped)==response['skipped']
    assert response['not_found']==0 and len(accepted)+len(skipped)==5
    save('upload-audit',{'accepted':accepted,'skipped':skipped,'not_found':[],'verified_strings':5,'component_verified_strings':len(all_after),'all_targets_unchanged':True,'complete':True})
    print(json.dumps({'accepted':len(accepted),'skipped_same_translation':len(skipped),'not_found':0,'component_verified_strings':len(all_after),'all_targets_unchanged':True},ensure_ascii=False))
else:raise ValueError(mode)
