from pathlib import Path
import json, shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
catalog=json.loads((ROOT/'work/teaching-projects/catalog.json').read_text(encoding='utf8'))
for d in ['tools','content','blueprints','aia','validation','decks','screenshots']:(HERE/d).mkdir(exist_ok=True)
out=ROOT/'outputs/课程案例/56课课程';out.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'work/teaching-projects/课程大纲.md',out/'课程大纲.md')
p=HERE/'progress.json'
if not p.exists():
 lessons=[]
 for s in catalog['stages']:
  for l in s['lessons']:
   lessons.append({'id':l['id'],'title':l['title'],'stage':s['id'],'content':'pending','aia':'pending','nativeValidation':'pending','apk':'pending','ppt':'pending','visualReview':'pending','package':'pending','existing':str(ROOT/'outputs/课程案例/第19课-接物游戏') if l['id']==19 else None})
 lessons[18].update({k:'complete' for k in ['content','aia','nativeValidation','apk','ppt','visualReview','package']})
 p.write_text(json.dumps({'schemaVersion':1,'lessons':lessons},ensure_ascii=False,indent=2),encoding='utf8')
print('Initialized 56 lessons; lesson 19 already completed.')
