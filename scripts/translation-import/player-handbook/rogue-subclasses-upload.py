"""Suggest-upload, audit, and archive the explicitly approved Rogue subclass v1."""
import hashlib, json, re, runpy, shutil, sys
from pathlib import Path
sys.dont_write_bytecode=True
B=runpy.run_path(str(Path(__file__).with_name('rogue-subclasses.py')))
ROOT,DATA,BASE,PREFIX,BOOK=(B[x] for x in ['ROOT','DATA','BASE','PREFIX','BOOK'])
load,save,write,leaves,w=(B[x] for x in ['load','save','write','leaves','w'])
AUTHORIZATION='好像也沒甚麼問題，可以上傳'
HASHES={'classes':'5329d83297e84068bf2f4cdb91b105373c3b65f6c07485b9071684c709a659a7','content':'99a08cda459d2358f478dc7a4b07706e33a9d3649725f593ec00790bfa83b19c'}
EXPECTED={'classes':92,'content':8}
def digest(name):return hashlib.sha256((DATA/(PREFIX+'.'+name)).read_bytes()).hexdigest()
def preflight():
    info=load('verification');assert info['version']=='v1' and info['payload_sha256']==HASHES
    assert all(v==0 for v in info['checks'].values()) and not info['uploaded']
    assert not list(DATA.glob(PREFIX+'.*upload-attempt.json'))
    records={}
    for c in ['classes','content']:
        assert digest(c+'.upload.json')==HASHES[c]
        full=dict(leaves(load(c+'.aligned')));payload=dict(leaves(load(c+'.upload')))
        assert len(payload)==EXPECTED[c] and all(full[p]==zh for p,zh in payload.items())
        status,tr=w.call('GET',f'/api/translations/{BOOK}/{BOOK}-{c}/zh_Hant/')
        filename=f'compendium/zh-tw/{BOOK}/{BOOK}.{c}.json';assert status==200 and tr['filename']==filename
        status,settings=w.call('GET',f'/api/components/{BOOK}/{BOOK}-{c}/');assert status==200 and settings.get('push')
        status,repo=w.call('GET',f'/api/components/{BOOK}/{BOOK}-{c}/repository/');assert status==200 and not repo.get('merge_failure')
        rows,pagination=B['read_all'](BOOK,BOOK+'-'+c);units={r['context']:r for r in rows};baseline=load(c+'.live')['units']
        local=dict(leaves(B['read'](ROOT/f'compendium/en/{BOOK}/{BOOK}.{c}.json')))
        identical=[]
        for p,zh in full.items():
            assert local[p]==baseline[p]['source'][0]==units[p]['source'][0],('EN changed',p)
            if units[p]['target']!=baseline[p]['target']:
                assert units[p]['target']==[zh],('Formal target differs from approved version',p)
                identical.append(p)
        save(c+'.component-before',units)
        records[c]={'filename':filename,'push_url_set':True,'repository':{k:repo.get(k) for k in ['needs_commit','needs_push','needs_merge','merge_failure']},'pagination':pagination,'strings':len(payload),'prior_suggestions':[p for p in payload if units[p]['has_suggestion']],'identical_accepted_since_preview':identical}
        print(c,len(payload),'matched; prior suggestions',len(records[c]['prior_suggestions']),'repository',records[c]['repository'])
    save('preflight',records)
    save('approval',{'date':'2026-10-09','authorization':AUTHORIZATION,'version':'v1','approved':True,'payload_sha256':HASHES,'method':'suggest','acknowledged_remaining':['原稿詭術師施法表缺EN/API單元；保留原稿，不放入payload。'],'unresolved':[],'preview_sha256':digest('preview.md')})
    shutil.copy2(DATA/(PREFIX+'.preview.md'),DATA/(PREFIX+'.confirmed.preview.md'))
    print('Approved payload unchanged: 100 strings')
def prepare_inspection():
    ids=[]
    for c in ['classes','content']:
        units=load(c+'.component-before');ids.extend(units[p]['id'] for p,v in leaves(load(c+'.upload')))
    script=Path(__file__).with_name('rogue-subclasses-suggestions.py')
    code='import json\nfrom weblate.trans.models import Suggestion\nids='+repr(ids)+'\nprint("ROGUE_SUGGESTIONS_JSON="+json.dumps({"suggestions":[{"id":s.id,"unit_id":s.unit_id,"target":[s.target] if isinstance(s.target,str) else list(s.target)} for s in Suggestion.objects.filter(unit_id__in=ids)]},ensure_ascii=False))\n'
    script.write_text(code,encoding='utf-8');print('Read-only suggestion inspection',len(ids),'units',script)
def record_before():record_inspection('before')
def record_after():record_inspection('after')
def record_inspection(stage):
    log=(DATA/(PREFIX+'.suggestions-'+stage+'.txt')).read_text(encoding='utf-8-sig')
    m=re.search(r'ROGUE_SUGGESTIONS_JSON=(\{[^\r\n]+\})',log);assert m,stage
    data=json.loads(m[1]);save('suggestions-'+stage,data);print(stage,len(data['suggestions']),'suggestions inspected')
def upload(c):
    assert load('approval')['authorization']==AUTHORIZATION and load('approval')['payload_sha256']==HASHES
    assert digest(c+'.upload.json')==HASHES[c]
    for n in ['upload-attempt','upload-response']:assert not (DATA/(PREFIX+'.'+c+'.'+n+'.json')).exists(),'Inspect actual state before any retry'
    # Existing suggestions are retained, including alternatives; exact matches may be skipped.
    prior=load('suggestions-before')['suggestions'];known={s['unit_id'] for s in prior}
    before=load(c+'.component-before')
    for p,v in leaves(load(c+'.upload')):
        if before[p]['has_suggestion']:assert before[p]['id'] in known,('Missing prior suggestion inspection',p)
    save(c+'.upload-attempt',{'date':'2026-10-09','method':'suggest','sha256':HASHES[c]})
    status,body=w.upload(BOOK,BOOK+'-'+c,str(DATA/(PREFIX+'.'+c+'.upload.json')),method='suggest')
    save(c+'.upload-response',{'http_status':status,'response':body,'method':'suggest','sha256':HASHES[c]});print(c,status,body)
    assert status in [200,201] and isinstance(body,dict)
    assert body['not_found']==0 and body['accepted']+body['skipped']==EXPECTED[c]
def upload_classes():upload('classes')
def upload_content():upload('content')
def audit():
    prior=load('suggestions-before')['suggestions'];later=load('suggestions-after')['suggestions']
    result={}
    for c in ['classes','content']:
        before=load(c+'.component-before');rows,pagination=B['read_all'](BOOK,BOOK+'-'+c);after={r['context']:r for r in rows}
        assert set(before)==set(after)
        scope=dict(leaves(load(c+'.aligned')));unrelated_changes=[];identical_accepted=[]
        for p,u in before.items():
            assert after[p]['source']==u['source'],('Source changed during upload',p)
            if after[p]['target']!=u['target']:
                if p in scope:
                    assert after[p]['target']==[scope[p]],('Unexpected scoped formal write',p)
                    identical_accepted.append(p)
                else:unrelated_changes.append(p)
        accepted=[];skipped=[]
        for p,zh in leaves(load(c+'.upload')):
            uid=after[p]['id'];matches=[s for s in later if s['unit_id']==uid and s['target']==[zh]]
            pre_matches=[s for s in prior if s['unit_id']==uid and s['target']==[zh]]
            assert matches or after[p]['target']==[zh],('Approved suggestion/translation not found',p)
            if before[p]['target']==[zh]:skipped.append({'path':p,'reason':'Identical formal translation already present'})
            elif pre_matches:skipped.append({'path':p,'reason':'Identical existing suggestion retained'})
            else:accepted.append({'path':p,'unit_id':uid,'suggestion_ids':[s['id'] for s in matches],'identical_translation_accepted_since_upload':after[p]['target']==[zh]})
        response=load(c+'.upload-response')['response'];assert len(accepted)==response['accepted'] and len(skipped)==response['skipped'],(c,len(accepted),len(skipped),response)
        save(c+'.after',{p:after[p] for p in scope})
        result[c]={'accepted':accepted,'skipped':skipped,'response':response,'verified_units':len(after),'scoped_formal_targets_unchanged':not identical_accepted,'identical_accepted_during_upload':identical_accepted,'unrelated_formal_changes':unrelated_changes,'pagination':pagination,'approved_in_queue_or_formal':len(accepted)+len(skipped),'batch_formally_untranslated':sum(not any(after[p]['target']) or after[p]['target']==after[p]['source'] for p,zh in leaves(load(c+'.upload')))}
    summary={'complete':True,'accepted':sum(len(r['accepted']) for r in result.values()),'skipped':sum(len(r['skipped']) for r in result.values()),'not_found':0,'verified_units':sum(r['verified_units'] for r in result.values()),'components':result}
    save('upload-audit',summary)
    info=load('verification');info['approved']=True;info['uploaded']=True;info['remaining']=info.pop('pending');info['pending']=[];save('verification',info)
    print({k:v for k,v in summary.items() if k!='components'})
def archive():
    result=load('upload-audit');assert result['complete'] and result['not_found']==0
    destination=BASE/'_done/subclasses/rogue';assert not destination.exists()
    base=BASE.resolve();src=DATA.resolve();dest=destination.resolve()
    assert src.is_relative_to(base) and dest.is_relative_to(base) and src!=base
    original=BASE/(PREFIX+'.txt');assert original.is_file()
    assert original.read_text(encoding='utf-8').rstrip('\r\n')==(DATA/(PREFIX+'.source.txt')).read_text(encoding='utf-8').rstrip('\r\n')
    remaining=BASE/(PREFIX+'.remaining.txt')
    assert not remaining.exists()
    remaining.write_text('### Arcane Trickster Spellcasting\n狀態：原稿有施法表，但目前EN／Weblate沒有對應單元；使用者已確認保留原稿，本批不新增EN欄位。\n原稿：'+str(original)+'（17–37行）\n'+(DATA/(PREFIX+'.source.unmapped-spellcasting-table.txt')).read_text(encoding='utf-8'),encoding='utf-8')
    links=lambda suffix:f'[{suffix}](<{str(destination/(PREFIX+"."+suffix)).replace(chr(92),"/")}>)'
    lines=['# 遊蕩者四子職業 v1 上傳報告','','2026-10-09。使用者確認：「'+AUTHORIZATION+'」。',
      '',f'已以method=suggest送出{result["accepted"]}個建議；跳過{result["skipped"]}、未匹配0。classes '+str(result['components']['classes']['response']['accepted'])+'＋content '+str(result['components']['content']['response']['accepted'])+'。',
      '', '涵蓋25個classes條目（四個子職業、相關特性、附屬心靈之刃武器）與8個content頁面；靈能骰表、行動、效果、升級提示及插圖標題一併處理；没有相關RollTable。21個既有欄位及36個正文區塊照舊。全部差異、原稿行號、補翻與條件對照見'+links('preview.md')+'。',
      '', '必要修正：施法UUID與殘留字元、現行法術名及國字環階、Vex＝侵擾、法術竊賊在偷得法術後才觸發使用限制、靈能面紗對生物造成傷害後結束、撕裂心智必須每回合重複豁免、mile＝哩、模仿大師的研究對象等。',
      '', '四項驗收完成：底稿99段的差異全部登記；術語48項命中、15項語境說明、未處理0；validate通過25條109個完整字串，content另驗8頁12字串；所有HTML、UUID、Reference、Embed、巨集及佔位符保留。獨立通讀與嵌套欄位核對完成。',
      '',f'上傳後重新讀取{result["verified_units"]}個單元，核對全部100個核准字串在建議佇列或相同正式譯文中，並核對實際建議內容。正式譯文變動及其他批次變動詳見'+links('upload-audit.json')+'。本次只新增建議，未以translate／replace覆寫正式譯文。',
      '', '## 尚餘範圍','', '詭術師施法表（原稿17–37行）無EN/API可對應單元。原稿與remaining保留在_incoming/player-handbook；没有可匹配但尚未送出的字串，來源表格的後續匯入需先有EN對應結構。',
      '',f'[原稿](<{str(original).replace(chr(92),"/")}>)；[remaining](<{str(remaining).replace(chr(92),"/")}>)。',
      '', '## 確認版本與最終雜湊','', '核准版為v1，payload與確認預覽一致，未改譯文。']
    for c,h in HASHES.items():lines.append(c+'：`'+h+'`。')
    lines+=['','## 上傳回應','','```json',json.dumps({c:r['response'] for c,r in result['components'].items()},ensure_ascii=False,indent=1),'```','',links('approval.json')+'；'+links('preflight.json')+'；'+links('upload-audit.json')+'。']
    write('2026-10-09.report.md','\n'.join(lines).replace('没有','沒有'))
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(src),str(dest))
    # Keep the original manuscript in place because it contains the remaining table.
    for path in dest.rglob('*'):
        if path.suffix not in ['.md','.html']:continue
        if path.name==PREFIX+'.confirmed.preview.md':continue
        t=path.read_text(encoding='utf-8').replace(str(DATA).replace('\\','/'),str(dest).replace('\\','/'))
        if path.name in [PREFIX+'.preview.md',PREFIX+'.reading.html']:
            t=t.replace('尚未上傳','已於2026-10-09上傳為建議')
            t=t.replace('## 10. 待確認','## 10. 已確認事項').replace('請確認整批必要修正、原稿補翻及既有譯文保留項。確認後才以method=suggest上傳。','使用者已確認整批必要修正、原稿補翻及既有譯文保留項；已以method=suggest上傳。')
        path.write_text(t,encoding='utf-8')
    preview=dest/(PREFIX+'.preview.md')
    with preview.open('a',encoding='utf-8') as h:
        h.write('\n\n## 使用者確認及上傳結果\n\n使用者：「'+AUTHORIZATION+'」。本版已確認，表格保留原稿。\n\n'+f'新增{result["accepted"]}個建議、跳過{result["skipped"]}、未匹配0；實際建議內容及全部核准字串均已核對。\n')
    print(dest/(PREFIX+'.2026-10-09.report.md'))
if __name__=='__main__':globals()[sys.argv[1]]()
