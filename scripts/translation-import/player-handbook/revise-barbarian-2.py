import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / '_incoming/player-handbook'
PREFIX = 'classes.barbarian.2'
paragraph = '若你使用魯莽攻擊，則可以放棄本回合中你所選擇的一次基於力量攻擊檢定所具有的任何優勢。所選的攻擊檢定不能具有劣勢。若所選的攻擊檢定命中，則目標將承受額外[[lookup @scale.barbarian.brutal-strike]]傷害，傷害類型與武器或徒手打擊造成的傷害類型相同，並且你可以造成一種你所選擇的殘暴打擊效應。你具有下列效應選項。'
for suffix in ['upload.json', 'draft.txt', 'verification.json']:
    source = HERE/(PREFIX+'.'+suffix)
    backup = HERE/(PREFIX+'.v1.'+suffix)
    assert source.is_file() and not backup.exists()
    backup.write_bytes(source.read_bytes())
draft = HERE/(PREFIX+'.draft.txt')
lines = draft.read_text(encoding='utf-8').splitlines()
index = lines.index('### Brutal Strike')
assert lines[index+2].startswith('若你使用魯莽攻擊，')
old = lines[index+2]
assert old != paragraph
lines[index+2] = paragraph
draft.write_text('\n'.join(lines)+'\n',encoding='utf-8')
review = HERE/'review-barbarian-2.py'
text = review.read_text(encoding='utf-8')
text = text.replace('v1','v2').replace('放棄其所有優勢','放棄其任何優勢（使用者指定完整句）').replace('any Advantage→所選一次檢定的所有優勢','any Advantage→所選一次檢定的任何優勢（使用者指定）')
text = text.replace('待本批v2確認。','使用者已於2026-10-08確認本批v2。').replace('待本批確認','使用者已確認').replace('待確認，未上傳','已確認，待上傳')
text = text.replace("'approved':False", "'approved':True")
text = text.replace('第2批v2已預覽，未上傳','第2批v2已確認，待上傳')
text = text.replace(".replace('第2批待順稿','第2批v2已確認，待上傳')", ".replace('第2批v1已預覽，未上傳','第2批v2已確認，待上傳')")
text = text.replace('待確認：本批v2、','本批v2已由使用者確認，包括').replace('本批名稱「殘暴打擊」','本批名稱「殘暴打擊」')
text = text.replace('依技能第5步「每批版本得到使用者明確確認後才上傳」，本批停於預覽。','使用者提供Brutal Strike首段完整修訂，並明確表示「其他應該沒問題，可以上傳」。v2只採用該段修訂，其餘譯文保留，依此次確認送出建議。')
review.write_text(text,encoding='utf-8')
approval = {'version':'v2','date':'2026-10-08','entry':'Brutal Strike','field':'description/b0001','before':old,'approved_paragraph':paragraph,'authorization':'其他應該沒問題，可以上傳','scope':'只變更使用者指定首段；其餘v1譯文不變；本批9條29字串以suggest上傳。','approved':True}
(HERE/(PREFIX+'.approval.json')).write_text(json.dumps(approval,ensure_ascii=False,indent=1),encoding='utf-8')
print(json.dumps(approval,ensure_ascii=False))
