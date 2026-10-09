"""Upload the explicitly confirmed Grave Domain v1 as suggestions, then audit."""
import hashlib, json, re, runpy, shutil, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
B=runpy.run_path(str(Path(__file__).with_name('grave-domain.py')))
ROOT,DATA,PROJECT,COMP=(B[k] for k in ['ROOT','DATA','PROJECT','COMP'])
load,save,write,leaves,w,paged=(B[k] for k in ['load','save','write','leaves','w','paged'])
AUTHORIZATION='bloodied用重傷\n其他沒什麼問題，可以上傳'
HASH='c5446cdbeb11f3c999196ba902d077b706890026520d1ba4058842ba973a3016'
DATE='2026-10-09'
def digest(name):return hashlib.sha256((DATA/name).read_bytes()).hexdigest()

def preflight():
    version=load('grave-domain.version');review=load('grave-domain.review')
    assert version['version']=='v1' and not version['uploaded']
    assert version['payload_sha256']==HASH==digest('grave-domain.upload.json')
    assert version['preview_sha256']==digest('grave-domain.preview.md')
    assert all(v==0 for v in review['checks'].values())
    assert not (DATA/'grave-domain.upload-attempt.json').exists(),'Audit existing upload before retrying'
    payload=dict(leaves(load('grave-domain.upload')));full=dict(leaves(load('grave-domain.aligned')))
    assert len(payload)==13 and all(full[p]==zh for p,zh in payload.items())
    status,tr=w.call('GET',f'/api/translations/{PROJECT}/{COMP}/zh_Hant/')
    filename=f'compendium/zh-tw/{PROJECT}/dnd-ravenloft-horrors-within.options.json'
    assert status==200 and tr['filename']==filename,(status,tr.get('filename'))
    status,settings=w.call('GET',f'/api/components/{PROJECT}/{COMP}/');assert status==200 and settings.get('push')
    status,repo=w.call('GET',f'/api/components/{PROJECT}/{COMP}/repository/');assert status==200 and not repo.get('merge_failure')
    rows,audit=paged(f'/api/translations/{PROJECT}/{COMP}/zh_Hant/units/')
    now={r['context']:r for r in rows};baseline={r['context']:r for r in load('options.live')['units']}
    scope=dict(leaves({'entries':load('scope')['options'],'folders':load('scope')['folders']}))
    accepted_since_preview=[]
    for p,en in scope.items():
        assert baseline[p]['source']==now[p]['source']==[en],('Source changed',p)
        if baseline[p]['target']!=now[p]['target']:
            assert p in full and now[p]['target']==[full[p]],('Formal target changed from approved version',p)
            accepted_since_preview.append(p)
    # The latest user ruling already matches both submitted Bloodied translations.
    for p in ["entries.Sentinel at Death's Door.description", "entries.Sentinel at Death's Door.activities.utility.condition"]:
        assert '重傷' in full[p] and '浴血' not in full[p]
    save('grave-domain.component-before',now)
    info={'date':DATE,'filename':filename,'push_url_set':True,'repository':{k:repo.get(k) for k in ['needs_commit','needs_push','needs_merge','merge_failure']},'pagination':audit,'payload_strings':13,'prior_suggestions':[p for p in payload if now[p].get('has_suggestion')],'identical_accepted_since_preview':accepted_since_preview}
    save('grave-domain.preflight',info)
    save('grave-domain.approval',{'date':DATE,'authorization':AUTHORIZATION,'version':'v1','approved':True,'method':'suggest','payload_sha256':HASH,'preview_sha256':version['preview_sha256'],'revision':'Bloodied兩處均已為重傷；無譯文修改，payload與預覽維持原確認版本。','remaining':version['remaining']})
    shutil.copy2(DATA/'grave-domain.preview.md',DATA/'grave-domain.confirmed.preview.md')
    ids=[now[p]['id'] for p in payload]
    script=Path(__file__).with_name('grave-domain-suggestions.py')
    script.write_text('import json\nfrom weblate.trans.models import Suggestion\nids='+repr(ids)+'\nprint("GRAVE_SUGGESTIONS_JSON="+json.dumps({"suggestions":[{"id":s.id,"unit_id":s.unit_id,"target":[s.target] if isinstance(s.target,str) else list(s.target)} for s in Suggestion.objects.filter(unit_id__in=ids)]},ensure_ascii=False))\n',encoding='utf-8')
    print(json.dumps(info,ensure_ascii=False,indent=1))

def inspect(stage):
    assert stage in ['before','after']
    script=Path(__file__).with_name('grave-domain-suggestions.py')
    result=subprocess.run(['docker','exec','-i','weblate-docker-weblate-1','weblate','shell'],input=script.read_bytes(),capture_output=True)
    out=result.stdout.decode('utf-8','replace');err=result.stderr.decode('utf-8','replace')
    write('grave-domain.suggestions-'+stage+'.txt',out+'\n'+err)
    assert result.returncode==0,('Read-only inspection failed',result.returncode)
    match=re.search(r'GRAVE_SUGGESTIONS_JSON=(\{[^\r\n]+\})',out);assert match,'No inspection JSON'
    data=json.loads(match[1]);save('grave-domain.suggestions-'+stage,data)
    print(stage,len(data['suggestions']),'actual suggestions inspected')
def inspect_before():inspect('before')
def inspect_after():inspect('after')

def upload():
    approval=load('grave-domain.approval');assert approval['authorization']==AUTHORIZATION and approval['payload_sha256']==HASH
    assert digest('grave-domain.upload.json')==HASH
    assert digest('grave-domain.confirmed.preview.md')==approval['preview_sha256']
    for name in ['upload-attempt','upload-response']:assert not (DATA/('grave-domain.'+name+'.json')).exists(),'Inspect state before any retry'
    prior=load('grave-domain.suggestions-before')['suggestions'];known={s['unit_id'] for s in prior}
    before=load('grave-domain.component-before')
    for p,v in leaves(load('grave-domain.upload')):
        if before[p].get('has_suggestion'):assert before[p]['id'] in known,('Prior suggestions uninspected',p)
    save('grave-domain.upload-attempt',{'date':DATE,'method':'suggest','sha256':HASH,'strings':13})
    status,body=w.upload(PROJECT,COMP,str(DATA/'grave-domain.upload.json'),method='suggest')
    save('grave-domain.upload-response',{'http_status':status,'response':body,'method':'suggest','sha256':HASH})
    print(status,json.dumps(body,ensure_ascii=False))
    assert status in [200,201] and isinstance(body,dict)
    assert body['not_found']==0 and body['accepted']+body['skipped']==13

def audit():
    before=load('grave-domain.component-before');rows,pagination=paged(f'/api/translations/{PROJECT}/{COMP}/zh_Hant/units/');after={r['context']:r for r in rows}
    prior=load('grave-domain.suggestions-before')['suggestions'];later=load('grave-domain.suggestions-after')['suggestions']
    assert set(before)==set(after)
    scoped=dict(leaves(load('grave-domain.aligned')));unrelated=[];identical=[]
    for p,u in before.items():
        assert after[p]['source']==u['source'],('Source changed',p)
        if after[p]['target']!=u['target']:
            if p in scoped:
                assert after[p]['target']==[scoped[p]],('Unexpected formal target change',p)
                identical.append(p)
            else:unrelated.append(p)
    accepted=[];skipped=[]
    for p,zh in leaves(load('grave-domain.upload')):
        uid=after[p]['id'];matches=[s for s in later if s['unit_id']==uid and s['target']==[zh]]
        pre_matches=[s for s in prior if s['unit_id']==uid and s['target']==[zh]]
        assert matches or after[p]['target']==[zh],('Exact approved target absent',p)
        if before[p]['target']==[zh]:skipped.append({'path':p,'reason':'Identical formal target'})
        elif pre_matches:skipped.append({'path':p,'reason':'Identical existing suggestion'})
        else:accepted.append({'path':p,'unit_id':uid,'suggestion_ids':[s['id'] for s in matches],'accepted_into_formal_since_upload':after[p]['target']==[zh]})
    response=load('grave-domain.upload-response')['response']
    assert len(accepted)==response['accepted'] and len(skipped)==response['skipped'],(len(accepted),len(skipped),response)
    result={'complete':True,'accepted':len(accepted),'skipped':len(skipped),'not_found':0,'verified_units':len(rows),'accepted_details':accepted,'skipped_details':skipped,'identical_formal_acceptance_during_upload':identical,'unrelated_formal_changes':unrelated,'pagination':pagination,'remaining_eligible_strings':0,'remaining_missing_structure':['book日誌頁GraveDomainCleri缺少EN/API元件；字串數無法計算'],'formal_untranslated_in_submitted_scope':sum(not any(after[p]['target']) or after[p]['target']==after[p]['source'] for p,v in leaves(load('grave-domain.upload')))}
    save('grave-domain.upload-audit',result);save('grave-domain.component-after',after)
    version=load('grave-domain.version');version['approved']=True;version['uploaded']=True;save('grave-domain.version',version)
    print({k:result[k] for k in ['complete','accepted','skipped','not_found','verified_units','remaining_eligible_strings']})

def archive():
    audit=load('grave-domain.upload-audit');assert audit['complete'] and audit['not_found']==0
    base=ROOT/'_incoming/horror-within';src=DATA.resolve();dest=(base/'_done/grave-domain').resolve()
    assert src.is_relative_to(base.resolve()) and dest.is_relative_to(base.resolve()) and src!=base.resolve()
    assert not dest.exists()
    original=base/'grave-domain.txt';assert original.is_file()
    assert original.read_text(encoding='utf-8').rstrip('\r\n')==(DATA/'grave-domain.source.txt').read_text(encoding='utf-8').rstrip('\r\n')
    remaining=base/'grave-domain.remaining.txt';assert not remaining.exists()
    remaining.write_text('### Grave Domain\n尚餘：子職業細節日誌頁 GraveDomainCleri。\nUUID：Compendium.dnd-ravenloft-horrors-within.book.JournalEntry.rhwSubclasses000.JournalEntryPage.GraveDomainCleri\n目前本書只有options／glossary的API元件與options.json本地EN，沒有book／content。不能新增或推測EN結構，待上游提供再做。\n原稿grave-domain.txt保留，行號1–35；法術表已處理，並無剩餘可匹配字串。缺少結構的日誌頁字串數無法計算。\n',encoding='utf-8')
    def link(name):return '['+name+'](<'+str(dest/name).replace(chr(92),'/')+'>)'
    report=['# 墳墓領域整批 v1 上傳報告','',DATE+'。使用者确认：「bloodied用重傷；其他沒什麼問題，可以上傳」。'.replace('确认','確認'),'','以method=suggest完成'+str(audit['accepted'])+'個翻譯建議；跳過'+str(audit['skipped'])+'，未匹配0。核准Bloodied兩處原本皆為重傷，payload不變。','',
    '範圍：6個options條目、完整31字串；本批只送13個差異字串。司命神使7個英文欄位依原稿補翻，其餘6個為必要規則、定案詞或標記修正；18個既有欄位、1個資料夾名稱與11個正文區塊照舊。內嵌法術表與全部相關行動、效果及advancement欄位已涵蓋，無獨立RollTable。','',
    '差異包含法術表生命領域誤名、死亡牽引的施放／命中條件與傷害巨集、0生命值治療骰必取最大值、現行法術名標籤、歸墓之途持續時間、黯蝕／不死生物／重傷／暴擊／材料構材用詞。完整原稿行號、逐塊EN／原稿／既有譯文／底稿、修改理由、名稱保留、補翻與condition對照見'+link('grave-domain.preview.md')+'。','',
    '四項驗收：規則逐句核對與中文通讀通過；terms_check回傳0，27项命中、3項明列語境ack、未處理0；draft_diff回傳0，26段、5段改動大均有理由；lang_compare回傳0，各項缺詞均已解釋；validate回傳0，6條31字串。HTML、表格、br、UUID目標及巨集保留，禁用詞0。'.replace('27项','27項'),'',
    '上傳前確認正式zh_Hant路徑、push URL、repository與核准雜湊；上傳後重新核對全部'+str(audit['verified_units'])+'單元來源，並從Django讀取實際13個建議，逐字核對payload。正式譯文接受與其他批次變動详见'.replace('详见','詳見')+link('grave-domain.upload-audit.json')+'。','',
    '## 尚餘範圍','','book／content的子職業細節日誌頁GraveDomainCleri仍缺local EN與API元件。此頁無法計算尚餘字串數，不能宣稱content已完成；原稿及grave-domain.remaining.txt保留在_incoming/horror-within/。本次已存在的可匹配範圍剩餘待送字串為0。','',
    '## 版本與上傳證據','','核准v1 SHA-256：`'+HASH+'`。','','```json',json.dumps(load('grave-domain.upload-response'),ensure_ascii=False,indent=1),'```','',link('grave-domain.approval.json')+'；'+link('grave-domain.preflight.json')+'；'+link('grave-domain.upload-audit.json')+'。']
    write('grave-domain.'+DATE+'.report.md','\n'.join(report))
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(src),str(dest))
    # Freeze the confirmed preview bytes; only presentation copies gain upload status.
    for name in ['grave-domain.preview.md','grave-domain.reading.html']:
        path=dest/name;t=path.read_text(encoding='utf-8').replace('尚未上傳','已於'+DATE+'上傳為建議')
        if name.endswith('.md'):
            t=t.replace('原稿：../grave-domain.txt','原稿：../../grave-domain.txt').replace('本批v1共13個建議字串待使用者確認後才能上傳','本批v1共13個建議字串已依使用者確認上傳')
            t+='\n\n## 使用者確認與上傳結果\n\nBloodied＝重傷，兩處原已符合，payload不變。使用者確認其餘內容可上傳。完成13個建議，跳過0、未匹配0，實際文字逐一核對。\n'
        path.write_text(t,encoding='utf-8')
    print(dest/('grave-domain.'+DATE+'.report.md'))

if __name__=='__main__':globals()[sys.argv[1]]()
