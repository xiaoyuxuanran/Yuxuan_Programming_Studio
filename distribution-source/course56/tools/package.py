from pathlib import Path
import json,sys,shutil,zipfile,hashlib,re
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parents[1];OUT=ROOT/'outputs/课程案例/56课课程'
progress=json.loads((HERE/'progress.json').read_text(encoding='utf8'))
def read(p):return json.loads(p.read_text(encoding='utf8'))
def package(n):
 key=f'lesson{n:02d}'
 if n==19:
  target=OUT/'No.19接物游戏：基本玩法'
  if not target.exists():shutil.copytree(ROOT/'outputs/课程案例/第19课-接物游戏',target)
  return target
 content=read(HERE/'content'/key/'content.json');spec=read(HERE/'aia'/key/'artifact-spec.json')
 native=read(HERE/'validation'/key/'native.json');deck=read(HERE/'decks'/key/'result.json');review=read(HERE/'validation'/key/'visual.json')
 assert native.get('passed') and review.get('passed'),f'L{n} native or visual review pending'
 target=Path(deck['path']).parent;target.mkdir(parents=True,exist_ok=True)
 versions=spec['versions'];answer=next(x for x in versions if x['kind']=='answer');aia=Path(answer['file'])
 for name in ['工程','素材','积木参考图']:(target/name).mkdir(exist_ok=True)
 for v in versions:shutil.copy2(v['file'],target/'工程'/Path(v['file']).name)
 apk=aia.with_suffix('.apk');assert apk.exists() and zipfile.is_zipfile(apk)
 with zipfile.ZipFile(apk) as z:assert 'AndroidManifest.xml' in z.namelist() and 'classes.dex' in z.namelist()
 shutil.copy2(apk,target/'工程'/apk.name)
 with zipfile.ZipFile(aia) as z:
  for name in z.namelist():
   if name.startswith('assets/') and not name.endswith('/'):
    rel=Path(name.removeprefix('assets/'));assert '..' not in rel.parts
    p=target/'素材'/rel;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(z.read(name))
 for file in (HERE/'screenshots'/key).glob('block-*.png'):shutil.copy2(file,target/'积木参考图'/file.name)
 for name in ['教师教案.md','学生任务单.md']:shutil.copy2(HERE/'content'/key/name,target/name)
 if 37<=n<=42:
  shutil.copytree(HERE/'teaching-api',target/'teaching-api',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 if 43<=n<=50:
  firmware=target/'firmware';firmware.mkdir(exist_ok=True)
  sketch=spec['firmwareFolder']
  shutil.copytree(HERE/'firmware'/sketch,firmware/sketch,dirs_exist_ok=True)
  for filename in ['接线与使用说明.md','协议与技术依据.md','tcp_lab_server.py']:
   shutil.copy2(HERE/'firmware'/filename,firmware/filename)
  (firmware/'tests').mkdir(exist_ok=True)
  for filename in ['protocol_test.cpp','test_tcp_lab.py']:
   shutil.copy2(HERE/'firmware/tests'/filename,firmware/'tests'/filename)
  shutil.copytree(HERE/'firmware/shared',firmware/'shared',dirs_exist_ok=True)
 renders=HERE/'decks'/key/'renders';shutil.copy2(renders/'slide-01.png',target/'课件封面.png')
 preview=HERE/'decks'/key/'preview.html'
 extra=''
 if preview.exists():
  shutil.copy2(preview,target/'交互预览.html');extra='\n- `交互预览.html`：浏览器读取AIA积木的教学演示，不能替代Android设备验收。'
 sources=content.get('sources',spec.get('sources',[]));links=[]
 for source in sources:
  if isinstance(source,str):links.append(source)
  elif source.get('url'):links.append(source.get('title',source['url'])+'：'+source['url'])
 text=f"# 第{n}课 {content['title']}\n\n每课90分钟。完整答案供教师参考；课堂建议导入Class支架；Starter只有界面及素材，适合独立重建。\n\n## 文件\n\n- PPTX：可编辑课件，含{deck['slides']}页及讲师备注。\n- 教师教案.md：教学节奏、讲解建议与参考答案。\n- 学生任务单.md：课堂练习、预测与互测记录。\n- 素材、积木参考图：与实际工程对应。{extra}\n\n## 工程版本\n\n|用途|文件|\n|---|---|\n"
 labels={'answer':'完整答案','class':'课堂支架','starter':'纯界面起始版'}
 for v in versions:text+=f"|{labels[v['kind']]}|{Path(v['file']).name}|\n"
 text+=f"\n导入方法：羽轩平台 → App Inventor → 项目 → 导入项目(.aia)。`{apk.name}`为已编译安装包。项目内部使用英文标识便于App Inventor编译；屏幕显示文字、课程目录及资料文件名可以使用中文。\n\n## 使用范围\n\n原平台已验证三版导入与完整答案APK编译。未做Android真机测试；语音、权限、传感器、蓝牙及TCP等功能应按教案在对应设备上验收。具体证据和限制见验证说明.md。\n"
 if 37<=n<=42:text+='\n配套标准库Python课堂服务在 `teaching-api/`，按其中使用说明启动。\n'
 if 43<=n<=50:text+='\n配套ESP32固件、接线表和TCP课堂测试服务在 `firmware/`；先阅读接线与使用说明。\n'
 (target/'先读我.md').write_text(text,encoding='utf8')
 facts=['# 验证说明','',f"PPT共{deck['slides']}页，已逐页渲染检查；文字和表格可编辑。",'', '|工程|积木数|坏块数|','|---|---:|---:|']
 for record in native['projects']:facts.append(f"|{record['name']}|{record['blocks']}|{len(record['bad'])}|")
 facts+=['',f'完整答案APK：{apk.stat().st_size:,}字节，ZIP/AndroidManifest.xml/classes.dex检查通过。','', '未做Android真机或硬件联调，不把编译成功等同于设备功能验收。']
 pre=HERE/'validation'/key/'preview.json'
 if pre.exists():facts+=['',f"网页交互演示通过{len(read(pre).get('checks',[]))}项实际AIA逻辑输出断言；网页的声音与布局由浏览器实现。"]
 (target/'验证说明.md').write_text('\n'.join(facts)+'\n',encoding='utf8')
 media=['# 素材与来源','','本课程由羽轩课程任务独立组织，不是MIT官方课件翻译。技术依据：','']+['- '+s for s in links]
 media+=['','品牌logo由用户提供；短提示音若存在，为程序合成的原创操作音，不是动物录音。积木图及设计器图来自实际导入的本机平台。']
 if any((target/'素材'/name).exists() for name in ['apple.png','basket.png']):
  original=ROOT/'outputs/课程案例/第19课-接物游戏/素材与来源.md'
  shutil.copy2(original,target/'素材'/'接物游戏素材来源.md')
  media+=['','苹果及篮子沿用第19课原创生成素材。完整说明与生成提示词见素材/接物游戏素材来源.md。']
 for sourcefile in ['assets-source.json','school-image-source.json']:
  f=HERE/sourcefile
  if f.exists():
   data=read(f);assets=data.get('assets',[data])
   for asset in assets:
    name=asset.get('name','scene_school')+'.png'
    if (target/'素材'/name).exists():media+=['',f"## {name}",'','使用内置 image_gen 生成。提示词：', '',asset['prompt']]
 (target/'素材与来源.md').write_text('\n'.join(media)+'\n',encoding='utf8')
 manifest=[]
 for file in sorted(target.rglob('*')):
  if file.is_file() and file.name!='文件校验.json':manifest.append({'file':file.relative_to(target).as_posix(),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
 (target/'文件校验.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
 progress['lessons'][n-1].update({k:'complete' for k in ['content','aia','nativeValidation','apk','ppt','visualReview','package']})
 return target
for n in map(int,sys.argv[1:]):print(package(n))
(HERE/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2),encoding='utf8')
