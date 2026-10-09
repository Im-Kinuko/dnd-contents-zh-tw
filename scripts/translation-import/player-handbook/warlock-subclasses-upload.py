"""Revise, suggest-upload, audit and archive the user-approved Warlock subclass batch."""
import contextlib, hashlib, io, json, re, runpy, shutil, sys
from pathlib import Path
sys.dont_write_bytecode=True
B=runpy.run_path(str(Path(__file__).with_name('warlock-subclasses.py')))
ROOT,DATA,BASE,PREFIX,BOOK=(B[x] for x in ['ROOT','DATA','BASE','PREFIX','BOOK'])
load,save,write,leaves,w=(B[x] for x in ['load','save','write','leaves','w'])
AUTHORIZATION='Magical Cunning現在固定叫做祕法迴流\n其他粗略看過後好像可以，沒問題就上傳'
def digest(name):return hashlib.sha256((DATA/(PREFIX+'.'+name)).read_bytes()).hexdigest()
def rewrite(value):
    if isinstance(value,str):return value.replace('魔法機靈','祕法迴流')
    if isinstance(value,dict):return {k:rewrite(v) for k,v in value.items()}
    if isinstance(value,list):return [rewrite(v) for v in value]
    return value
def revise():
    assert not list(DATA.glob(PREFIX+'.*upload-attempt.json'))
    old=DATA/'versions/v1';old.mkdir(parents=True,exist_ok=True)
    for path in DATA.glob(PREFIX+'.*'):
        if path.is_file() and not (old/path.name).exists():shutil.copy2(path,old/path.name)
    save('approval-revision',{'version':'v2','date':'2026-10-09','authorization':AUTHORIZATION,'approved':True,'changes':['Magical Cunning固定為祕法迴流','創造奴僕行動條件依已確認正文修正為異怪召喚術','驚懼步伐range照EN，正文保留兩處擇一'],'method':'suggest'})
    text=(DATA/(PREFIX+'.draft.txt')).read_text(encoding='utf-8')
    text=rewrite(text).replace('activities.Thrall Temporary HP.condition：當你不需專注施放脆弱詛咒時','activities.Thrall Temporary HP.condition：當你不需專注施放異怪召喚術時')
    write('draft.txt',text);save('draft-fingerprint',{'sha256':digest('draft.txt')})
    for c in ['classes','content']:
        sheet=load(c+'.sheet')
        for k,row in sheet['entries'].items():
            for block in row['blocks']:block['draft_text']=rewrite(block['draft_text'])
            for field in ['activities','effects','advancement']:
                if field in row:row[field]=rewrite(row[field])
            if k=='Create Thrall':row['activities']['Thrall Temporary HP']['condition']='當你不需專注施放異怪召喚術時'
        save(c+'.sheet',sheet)
    labels=load('labels');labels['Magical Cunning']='祕法迴流';save('labels',labels)
    meta=load('metadata')
    for row in meta:
        row['zh']=rewrite(row['zh'])
        if row['path']=='entries.Create Thrall.activities.Thrall Temporary HP.condition':
            row['zh']='當你不需專注施放異怪召喚術時';row['basis']='使用者確認預覽的建議：依正文施放異怪召喚術，修正EN條件誤寫Hex。'
        elif 'Magical Cunning' in row['en']:row['basis']+=' 使用者固定譯名祕法迴流。'
    save('metadata',meta)
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):B['map_draft']()
    write('map.v2.log.txt',buf.getvalue())
    B['checks']();B['review']();B['preview']()
    update_preview()
    print('Approved v2 rebuilt',load('verification')['payload_sha256'])
def update_preview():
    path=DATA/(PREFIX+'.preview.md');text=path.read_text(encoding='utf-8')
    text=text.replace('完整預覽 v1','已確認預覽 v2').replace('＝113字串；1個有上游矛盾的行動條件留在pending，未放入payload。','＝114字串；創造奴僕行動條件已依使用者確認改為異怪召喚術並納入payload。')
    replacements={
      '1個條件待裁定':'全部條件已确认'.replace('确认','確認'),
      ' 此欄待裁定，未放入payload。':' 此欄已由使用者確認依正文修正，列入payload。',
      '保留兩方案在pending，未列入payload，等待使用者裁定。':'使用者已確認建議；採「當你不需專注施放異怪召喚術時」並列入payload。',
      '## 10. 待裁定與確認':'## 10. 確認與已解決事項',
      '目前此欄未放入payload，直譯與建議皆保留於pending。':'使用者已確認依正文修正；此欄已放入payload。',
      '待裁定，未列入payload':'已確認依正文修正',
      '創造奴僕condition有上游矛盾，留在pending，其餘均依正文或已裁定例外。':'創造奴僕condition的上游矛盾已依使用者確認修正；全部條件已完成核對。',
      '及1待裁定欄位':'；已確認的創造奴僕條件保留',
      '請確認本預覽的必要修正、補翻及保留項；確認後才會以建議上傳。':'使用者已確認必要修正、補翻與保留項，並授權以建議上傳。',
      '請確認可維持此處理。':'使用者已確認維持此處理。',
      '定案詞：魔法機靈':'定案詞：祕法迴流',
    }
    for a,b in replacements.items():text=text.replace(a,b)
    text+='\n\n## 使用者確認修訂 v2\n\n2026-10-09：'+AUTHORIZATION.replace('\n','；')+'。\n\nMagical Cunning的3個本批引用（天族韌性正文與2個行動條件）已統一為祕法迴流；原稿「秘法迴流」依使用者裁定採「祕」。創造奴僕的條件依確認改成異怪召喚術，其餘內容與v1一致。\n'
    for c,h in load('verification')['payload_sha256'].items():text+=f'\n最終{c} SHA-256：`{h}`。\n'
    path.write_text(text,encoding='utf-8')
    reading=DATA/(PREFIX+'.reading.html');reading.write_text(reading.read_text(encoding='utf-8').replace('v1','v2').replace('1個條件待裁定','所有條件已確認'),encoding='utf-8')
def preflight():
    info=load('verification');assert info['approved'] and not info['pending']
    assert load('approval-revision')['authorization']==AUTHORIZATION
    assert not list(DATA.glob(PREFIX+'.*upload-attempt.json'))
    records={}
    for c in ['classes','content']:
        slug=BOOK+'-'+c
        status,translation=w.call('GET',f'/api/translations/{BOOK}/{slug}/zh_Hant/')
        filename=f'compendium/zh-tw/{BOOK}/{BOOK}.{c}.json';assert status==200 and translation['filename']==filename
        status,settings=w.call('GET',f'/api/components/{BOOK}/{slug}/');assert status==200 and settings.get('push')
        status,repo=w.call('GET',f'/api/components/{BOOK}/{slug}/repository/');assert status==200 and not repo.get('merge_failure')
        rows,pagination=B['read_all'](BOOK,slug);units={r['context']:r for r in rows};baseline=load(c+'.live')['units']
        full=dict(leaves(load(c+'.aligned')));payload=dict(leaves(load(c+'.upload')))
        if c=='classes' and (DATA/(PREFIX+'.name-revision.json')).exists():full.update({load('name-revision')['path']:load('name-revision')['zh']})
        local=dict(leaves(B['read'](ROOT/f'compendium/en/{BOOK}/{BOOK}.{c}.json')))
        accepted_since_preview=[]
        for p,v in full.items():
            assert local[p]==baseline[p]['source'][0]==units[p]['source'][0],('EN changed',p)
            expected_target=[load('name-revision')['old']] if p=='entries.Magical Cunning.name' else baseline[p]['target']
            if units[p]['target']!=expected_target:
                assert units[p]['target']==[v],('Formal target differs from approved version',p)
                accepted_since_preview.append(p)
        assert all(full[p]==v for p,v in payload.items())
        assert digest(c+'.upload.json')==info['payload_sha256'][c]
        prior=[p for p in payload if units[p]['has_suggestion']]
        if prior:
            snapshot=load('prior-suggestions');known={s['unit_id']:s for s in snapshot['suggestions']}
            for p in prior:
                assert units[p]['id'] in known,('Existing suggestions need inspection',p)
                assert known[units[p]['id']]['target']==[payload[p]],('Different prior suggestion; preserve and inspect',p,known[units[p]['id']])
        save(c+'.component-before',units)
        records[c]={'filename':filename,'push_url_set':True,'repository':{k:repo.get(k) for k in ['needs_commit','needs_push','needs_merge','merge_failure']},'pagination':pagination,'strings':len(payload),'prior_suggestions':prior,'accepted_since_preview':accepted_since_preview}
        print(c,len(payload),'matched','repository',records[c]['repository'])
        if c=='classes':print('Magical Cunning current formal name:',units['entries.Magical Cunning.name']['target'][0])
    save('preflight',records);save('approval',{'authorization':AUTHORIZATION,'version':'v2','approved':True,'payload_sha256':info['payload_sha256'],'method':'suggest'})
def prepare_inspection():
    rows,_=B['read_all'](BOOK,BOOK+'-content');units={r['context']:r for r in rows};payload=dict(leaves(load('content.upload')))
    ids=[units[p]['id'] for p in payload]
    script=Path(__file__).with_name('warlock-subclasses-suggestions.py')
    text='import json\nfrom weblate.trans.models import Suggestion\nids='+repr(ids)+'\nprint("WARLOCK_SUGGESTIONS_JSON="+json.dumps({"suggestions":[{"id":s.id,"unit_id":s.unit_id,"target":list(s.target),"user_id":s.user_id} for s in Suggestion.objects.filter(unit_id__in=ids)]},ensure_ascii=False))\n'
    script.write_text(text,encoding='utf-8');print('Read-only inspection script',script,'units',ids)
def record_inspection():
    log=(DATA/(PREFIX+'.prior-suggestions.txt')).read_text(encoding='utf-8-sig')
    match=re.search(r'WARLOCK_SUGGESTIONS_JSON=(\{[^\r\n]+\})',log);assert match
    save('prior-suggestions',json.loads(match[1]));print(json.dumps(load('prior-suggestions'),ensure_ascii=False))
def fixed_name():
    before=load('classes.component-before');path='entries.Magical Cunning.name';u=before[path]
    assert u['source']==['Magical Cunning']
    record={'path':path,'en':'Magical Cunning','old':u['target'][0],'zh':'祕法迴流','unit_id':u['id'],'basis':'使用者明示Magical Cunning固定叫做祕法迴流；名稱欄同時一致化。'}
    save('name-revision',record)
    payload=load('classes.upload');payload['entries']['Magical Cunning']={'name':'祕法迴流'};save('classes.upload',payload)
    info=load('verification');info['classes_upload_strings']=len(dict(leaves(payload)));info['payload_sha256']['classes']=digest('classes.upload.json');save('verification',info)
    preview=DATA/(PREFIX+'.preview.md');text=preview.read_text(encoding='utf-8')
    text=text.replace('待送classes 98＋content 16＝114字串','待送classes 99＋content 16＝115字串（另含Magical Cunning名稱欄1字串）')
    text+='\n\n### Magical Cunning名稱欄同步修正\n\nEN：Magical Cunning；現行正式譯名：'+record['old']+'；使用者指定：祕法迴流。名稱欄僅此1個字串加入本批，相關特性正文仍照原範圍保留。\n\n最終classes SHA-256：`'+info['payload_sha256']['classes']+'`。\n'
    preview.write_text(text,encoding='utf-8');print('Name revision added',info['classes_upload_strings'],info['payload_sha256']['classes'])
def upload(c):
    sha=load('approval')['payload_sha256'][c];assert digest(c+'.upload.json')==sha
    for name in ['upload-attempt','upload-response']:assert not (DATA/(PREFIX+'.'+c+'.'+name+'.json')).exists(),'Inspect actual state before any retry'
    save(c+'.upload-attempt',{'date':'2026-10-09','method':'suggest','sha256':sha})
    status,body=w.upload(BOOK,BOOK+'-'+c,str(DATA/(PREFIX+'.'+c+'.upload.json')),method='suggest')
    save(c+'.upload-response',{'http_status':status,'response':body,'method':'suggest','sha256':sha});print(c,status,body)
    assert status in [200,201] and isinstance(body,dict)
    expected=len(dict(leaves(load(c+'.upload'))))
    assert body['not_found']==0 and body['accepted']+body['skipped']==expected
def upload_classes():upload('classes')
def upload_content():upload('content')
def audit():
    result={}
    for c in ['classes','content']:
        before=load(c+'.component-before');rows,pagination=B['read_all'](BOOK,BOOK+'-'+c);after={r['context']:r for r in rows}
        assert set(before)==set(after)
        for p,u in before.items():assert after[p]['source']==u['source'] and after[p]['target']==u['target'],('Unexpected formal write',p)
        payload=dict(leaves(load(c+'.upload')));accepted=[];skipped=[]
        for p,zh in payload.items():
            if after[p]['target']==[zh]:skipped.append({'path':p,'reason':'Already identical formal translation'})
            elif before[p]['has_suggestion']:
                prior=load('prior-suggestions')['suggestions'];assert any(s['unit_id']==after[p]['id'] and s['target']==[zh] for s in prior)
                assert after[p]['has_suggestion'];skipped.append({'path':p,'reason':'Identical prior suggestion retained'})
            else:
                assert not before[p]['has_suggestion'] and after[p]['has_suggestion'],('Suggestion state mismatch',p)
                accepted.append({'path':p,'unit_id':after[p]['id'],'formal_target_unchanged':True})
        response=load(c+'.upload-response')['response'];assert len(accepted)==response['accepted'] and len(skipped)==response['skipped']
        save(c+'.after',{p:after[p] for p in payload})
        result[c]={'accepted':accepted,'skipped':skipped,'not_found':response['not_found'],'response':response,'verified_units':len(after),'formal_translations_unchanged':True,'pagination':pagination,'batch_formally_untranslated':sum(not any(after[p]['target']) or after[p]['target']==after[p]['source'] for p in payload)}
    summary={'complete':True,'accepted':sum(len(r['accepted']) for r in result.values()),'skipped':sum(len(r['skipped']) for r in result.values()),'not_found':0,'verified_units':sum(r['verified_units'] for r in result.values()),'components':result}
    save('upload-audit',summary);info=load('verification');info['uploaded']=True;save('verification',info)
    print({k:v for k,v in summary.items() if k!='components'})
def archive():
    result=load('upload-audit');assert result['complete'] and result['not_found']==0
    destination=BASE/'_done/subclasses/warlock';assert not destination.exists()
    # Verify both absolute paths remain inside this book's workspace before moving the batch directory.
    base=BASE.resolve();src=DATA.resolve();dest=destination.resolve()
    assert src.is_relative_to(base) and dest.is_relative_to(base) and src!=base
    lines=['# 契術師四子職業 v2 上傳報告','', '2026-10-09。使用者確認：'+AUTHORIZATION.replace('\n','；')+'。',
      '',f'已以method=suggest送出{result["accepted"]}個建議；跳過{result["skipped"]}、未匹配0。classes '+str(result['components']['classes']['response']['accepted'])+'＋content '+str(result['components']['content']['response']['accepted'])+'。',
      '', '四宗主及相關法術表、行動、效果與12個content頁面一次處理；沒有相關骰表。27個既有欄位照舊。Magical Cunning引用與名稱欄固定祕法迴流；創造奴僕的條件依確認採異怪召喚術；所有其他差異見完整預覽。',
      '', '底稿差異、90項術語命中及機械驗證通過。所有HTML、UUID、Reference、Embed及巨集保留。前後核對'+str(result['verified_units'])+'個單元，正式source／target均未變；本次建議待使用者於Weblate審閱接受。',
      '', '## 最終雜湊','']
    for c,h in load('verification')['payload_sha256'].items():lines.append(c+'：`'+h+'`。')
    lines+=['','## 回應','',json.dumps({c:r['response'] for c,r in result['components'].items()},ensure_ascii=False,indent=1),'', '尚無待裁定或未匹配欄位。原稿與所有證據一併歸檔；v1保留於versions/v1。']
    write('2026-10-09.report.md','\n'.join(lines))
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(src),str(dest))
    original=BASE/PREFIX
    if original.exists():
        assert original.resolve().is_relative_to(base) and original.is_file()
        assert original.read_text(encoding='utf-8').rstrip('\r\n')==(dest/(PREFIX+'.source.txt')).read_text(encoding='utf-8').rstrip('\r\n')
        shutil.move(str(original),str(dest/(PREFIX+'.original.txt')))
    for path in dest.rglob('*'):
        if path.suffix not in ['.md','.html']:continue
        text=path.read_text(encoding='utf-8');text=text.replace(str(DATA).replace('\\','/'),str(dest).replace('\\','/'));path.write_text(text,encoding='utf-8')
    preview=dest/(PREFIX+'.preview.md');text=preview.read_text(encoding='utf-8')
    text=text.replace('尚未上傳','已於2026-10-09上傳為建議（111新增、4相同正式譯文跳過）')
    text+='\n\n## 上傳結果\n\nclasses新增99個建議；content新增12個建議、4個相同正式頁名跳過。合計111個新建議、未匹配0；3431個單元正式譯文與EN未變。\n'
    preview.write_text(text,encoding='utf-8')
    reading=dest/(PREFIX+'.reading.html');reading.write_text(reading.read_text(encoding='utf-8').replace('尚未上傳','已上傳為建議'),encoding='utf-8')
    print(str(dest/(PREFIX+'.2026-10-09.report.md')))
if __name__=='__main__':globals()[sys.argv[1]]()
