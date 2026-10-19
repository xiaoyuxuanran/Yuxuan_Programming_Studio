from pathlib import Path
import re,json,shutil,hashlib,sys,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WAR=ROOT/'work/native/server/war'
lines=(HERE/'课程大纲.md').read_text(encoding='utf8').splitlines();stages=[]
focus=['事件 · 角色 · 创意表达','变量 · 判断 · 循环 · 过程','坐标 · 动画 · 碰撞 · 规则','声音 · 影像 · 手机传感器','列表 · 字典 · 本地保存','Web · JSON · 数据共享','蓝牙 · BLE · Wi-Fi TCP','选题 · 开发 · 测试 · 展示']
for line in lines:
 m=re.match(r'\*\*(第[一二三四五六七八]阶段)：(.+?)｜第\s*(\d+)～(\d+)\s*节',line)
 if m:
  stages.append({'id':str(len(stages)+1).zfill(2),'name':m[1]+'：'+m[2].strip(),'title':m[2].strip(),'start':int(m[3]),'end':int(m[4]),'focus':focus[len(stages)],'lessons':[]});continue
 m=re.match(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|',line)
 if m and stages:
  n=int(m[1]);assert stages[-1]['start']<=n<=stages[-1]['end']
  stages[-1]['lessons'].append({'id':n,'title':m[2].strip(),'name':f'No.{n}'+m[2].strip(),'summary':m[3].strip(),'projects':[]})
lessons=[c for s in stages for c in s['lessons']]
assert len(stages)==8 and [c['id'] for c in lessons]==list(range(1,57))
samples=ROOT/'outputs/课程案例/第19课-接物游戏/工程'
if not samples.is_dir():samples=HERE/'projects'
target=WAR/'static/teaching/projects';target.mkdir(parents=True,exist_ok=True)
course=next(c for c in lessons if c['id']==19)
for id,name,filename,project,detail in [
 ('answer','完整答案','CatchApple19.aia','YXTeach19Answer','完整基本玩法：随机出现、接取计分、暂停和重置。'),
 ('class','课堂支架','CatchApple19Class.aia','YXTeach19Class','界面与辅助过程已准备好，动手完成四个核心任务。'),
 ('starter','纯界面起始版','CatchApple19Starter.aia','YXTeach19Starter','只含界面和素材，适合独立重建完整游戏。')]:
 shutil.copy2(samples/filename,target/filename)
 course['projects'].append({'id':id,'name':name,'description':detail,'file':filename,'url':'static/teaching/projects/'+filename,'projectName':project,'sha256':hashlib.sha256((samples/filename).read_bytes()).hexdigest()})
production=ROOT/'work/course56';complete='--require-complete' in sys.argv
materials=WAR/'static/teaching/materials';materials.mkdir(parents=True,exist_ok=True)
for lesson in lessons:
 n=lesson['id'];key=f'lesson{n:02}'
 if n!=19:
  spec=json.loads((production/'aia'/key/'artifact-spec.json').read_text(encoding='utf8'))
  proof=json.loads((production/'validation'/key/'native.json').read_text(encoding='utf8'))
  assert proof.get('passed') and all(not p['bad'] for p in proof['projects']),key
  names={'answer':('完整答案','完整界面和积木，供教师参考与对照。'),'class':('课堂支架','保留界面和辅助逻辑，按任务单补全核心任务。'),'starter':('纯界面起始版','保留界面和素材，适合独立搭建积木。')}
  for kind in ['answer','class','starter']:
   v=next(v for v in spec['versions'] if v['kind']==kind);source=Path(v['file']);filename=source.name
   digest=hashlib.sha256(source.read_bytes()).hexdigest();assert digest==v['sha256']
   shutil.copy2(source,target/filename)
   name,detail=names[kind]
   lesson['projects'].append({'id':kind,'name':name,'description':detail,'file':filename,'url':'static/teaching/projects/'+filename,'projectName':v['name'],'sha256':digest})
  deck=json.loads((production/'decks'/key/'result.json').read_text(encoding='utf8'));ppt=Path(deck['path']);folder=ppt.parent
  visual=production/'validation'/key/'visual.json'
  ready=visual.exists() and json.loads(visual.read_text(encoding='utf8')).get('passed') and (folder/'文件校验.json').exists()
 else:
  folder=ROOT/'outputs/课程案例/第19课-接物游戏';ppt=folder/'第19课-接物游戏.pptx';ready=True
 if complete:assert ready,f'Lesson {n} final package still pending'
 lesson['materials']=[]
 if not ready:continue
 pptfile=f'Lesson{n:02}-Slides.pptx';bundlefile=f'Lesson{n:02}-Materials.zip'
 shutil.copy2(ppt,materials/pptfile)
 with zipfile.ZipFile(materials/bundlefile,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for f in sorted(folder.rglob('*')):
   if f.is_file():z.write(f,f.relative_to(folder).as_posix())
 for name,filename in [('下载课件 PPT',pptfile),('下载本课完整资料',bundlefile)]:
  lesson['materials'].append({'name':name,'file':filename,'url':'static/teaching/materials/'+filename,'sha256':hashlib.sha256((materials/filename).read_bytes()).hexdigest()})
catalog={'schemaVersion':1,'id':'appinventor56-v2','name':'App Inventor 创意编程课程','lessonCount':56,'stageCount':8,'lessonMinutes':90,'hours':84,'stages':stages}
(HERE/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf8')
shutil.copy2(HERE/'catalog.json',WAR/'static/teaching/catalog.json')
for name,folder in [('teaching-projects.js','js'),('teaching-projects.css','css')]:shutil.copy2(HERE/name,WAR/'static'/folder/name)
index=WAR/'index.jsp';s=index.read_text(encoding='utf8')
if 'teaching-projects.js' not in s:s=s.replace('</head>','<link rel="stylesheet" href="static/css/teaching-projects.css?v=teaching1">\n<script defer src="static/js/teaching-projects.js?v=teaching1"></script>\n</head>')
token=hashlib.sha256(b''.join((HERE/f).read_bytes() for f in ['teaching-projects.js','teaching-projects.css','catalog.json'])+(WAR/'ode/ode.nocache.js').read_bytes()).hexdigest()[:12]
s=re.sub(r'(teaching-projects\.(?:js|css)\?v=)[a-zA-Z0-9]+',lambda m:m[1]+'tp'+token,s)
index.write_text(s,encoding='utf8')
(ROOT/'work/native/resources/build-version.txt').write_text('2026.10.19-teaching-projects-'+token+'\n',encoding='utf8')
print(f'Staged 8 stages, 56 Chinese lesson folders, {sum(len(l["projects"]) for l in lessons)} templates, and {sum(bool(l["materials"]) for l in lessons)} course packs.')
