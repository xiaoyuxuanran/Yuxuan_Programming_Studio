from pathlib import Path
import zipfile,json,hashlib,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];COURSE=ROOT/'work/course56';OUT=ROOT/'outputs/课程案例/56课完整课程包';OUT.mkdir(exist_ok=True)
catalog=json.loads((ROOT/'work/teaching-projects/catalog.json').read_text(encoding='utf8'))
progress=json.loads((COURSE/'progress.json').read_text(encoding='utf8'))
assert len(progress['lessons'])==56
for l in progress['lessons']:
 for k in ['content','aia','nativeValidation','apk','ppt','visualReview','package']:assert l[k]=='complete',(l['id'],k)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
records=[];index=['# App Inventor 创意编程56课','', '8个阶段，每课90分钟，共84小时。课程由创意与事件入门逐步推进到数据、网络、ESP32通信和毕业项目。第19课保留原案例。','', '每课含可编辑PPT、教案、任务单、完整答案/课堂支架/纯界面起始版AIA、答案APK、素材及真实积木参考图。PPT与工程可独立使用，也已集成进羽轩编程工作台2.3.4教学项目。','', '168个AIA已通过平台导入与坏块检查；56个答案APK编译完成；PPT共1347页逐页渲染检查。没有进行Android真机或实物ESP32联调，需按教案完成设备权限与硬件验收。','']
for stage in catalog['stages']:
 filename=f'Stage{stage["id"]}-Lessons{stage["start"]:02}-{stage["end"]:02}.zip';bundle=OUT/filename
 with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for l in stage['lessons']:
   folder=next(p for p in (ROOT/'outputs/课程案例/56课课程').iterdir() if p.is_dir() and p.name.startswith(f'No.{l["id"]:02}'))
   assert len(list((folder/'工程').glob('*.aia')))==3,folder
   assert len(list(folder.glob('*.pptx')))==1,folder
   for f in sorted(folder.rglob('*')):
    if f.is_file():z.write(f,folder.name+'/'+f.relative_to(folder).as_posix())
  z.writestr('阶段说明.md',f'# {stage["name"]}\n\n第{stage["start"]}–{stage["end"]}课，每课90分钟。\n\n'+stage['focus']+'\n')
 with zipfile.ZipFile(bundle) as z:assert z.testzip() is None
 records.append({'stage':stage['id'],'lessons':[stage['start'],stage['end']],'name':filename,'bytes':bundle.stat().st_size,'sha256':sha(bundle)})
 index+=['## '+stage['name'],'',f'下载阶段资料：[{filename}]({filename})','']+[f'- No.{l["id"]:02} {l["title"]}：{l["summary"]}' for l in stage['lessons']]+['']
 print(filename+' '+str(round(bundle.stat().st_size/1048576,1))+' MiB',flush=True)
(OUT/'课程索引.md').write_text('\n'.join(index)+'\n',encoding='utf8')
shutil.copy2(ROOT/'work/teaching-projects/课程大纲.md',OUT/'课程大纲.md')
(OUT/'SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['name']+'\n' for r in records),encoding='utf8')
master=OUT/'AppInventor-56-Lessons.zip'
with zipfile.ZipFile(master,'w',zipfile.ZIP_STORED) as z:
 for r in records:z.write(OUT/r['name'],r['name'])
 for n in ['课程索引.md','课程大纲.md','SHA256SUMS.txt']:z.write(OUT/n,n)
with zipfile.ZipFile(master) as z:assert z.testzip() is None
(HERE/'course-bundles.json').write_text(json.dumps({'complete':True,'lessons':56,'aia':168,'ppt':56,'slides':1347,'stages':records,'master':{'path':str(master),'bytes':master.stat().st_size,'sha256':sha(master)}},ensure_ascii=False,indent=2),encoding='utf8')
print('Complete master bundle '+str(round(master.stat().st_size/1048576,1))+' MiB',flush=True)
