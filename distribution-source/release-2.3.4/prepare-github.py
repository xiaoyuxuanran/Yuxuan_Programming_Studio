from pathlib import Path
import json,shutil,zipfile,hashlib,re,runpy,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];REPO=ROOT/'work/github-publish/Yuxuan_Programming_Studio';NATIVE=ROOT/'work/native';COURSE=ROOT/'work/course56'
def copy(a,b):b.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(a,b)
def stage():
 shutil.copytree(NATIVE/'resources/distribution-source',REPO/'distribution-source',dirs_exist_ok=True)
 copy(NATIVE/'mixly/UPSTREAM.json',REPO/'distribution-source/mixly-adaptation/UPSTREAM.json')
 # Draft authoring helper is superseded by final reviewed content.json files.
 p=REPO/'distribution-source/course56/blueprints/author_remaining.py'
 if p.exists():p.unlink()
 for source,target in [('使用说明.txt','docs/使用说明.txt'),('UPGRADE.md','docs/UPGRADE-2.3.4.md'),('CHANGELOG.txt','CHANGELOG.txt')]:copy(HERE/source,REPO/target)
 images=REPO/'docs/images'
 for source,target in [('teaching-root-1440.png','2.3.4-teaching.png'),('teaching-lesson-1440.png','2.3.4-lesson.png'),('personal-final-1440.png','2.3.4-projects.png')]:copy(COURSE/'ui'/source,images/target)
 for name in ['prepare-github.py','publish-release.py','course-bundles.py','build-check.py','Update-2.2.0.iss','Update-2.3.1.iss','Update-2.3.2.iss','Update-2.3.3.iss','target-files.json']:
  copy(HERE/name,REPO/'distribution-source/release-2.3.4'/name)
 for v in ['2.2.0','2.3.1','2.3.2','2.3.3']:copy(HERE/('update-manifest-'+v+'.json'),REPO/'distribution-source/release-2.3.4'/('update-manifest-'+v+'.json'))
 validation=REPO/'validation/release-2.3.4';validation.mkdir(exist_ok=True)
 for n in ['acceptance-final.ps1','finish-uninstall.ps1','restore-after-uninstall.ps1','verify-resume.py','installed-smoke.py','installed-teaching.cjs','studio-view-check.cjs','UpdateCompatibilityCheck.cs','UpdateNetworkCheck.cs']:copy(HERE/n,validation/n)
 for n in ['auxiliary-tests.json','firmware-final.json']:copy(COURSE/'validation'/n,validation/n)
 for n in ['teaching-ui.json','final-ui.json']:copy(COURSE/'ui'/n,validation/n)
 copy(COURSE/'storage-fix/result.json',validation/'storage-result.json')
 lessons=[]
 for n in range(1,57):
  if n==19:lessons.append({'lesson':19,'preservedOriginalCase':True,'slides':27});continue
  folder=COURSE/'validation'/f'lesson{n:02}'
  native=json.loads((folder/'native.json').read_text(encoding='utf8'));visual=json.loads((folder/'visual.json').read_text(encoding='utf8'))
  assert native['passed'] and visual['passed']
  lessons.append({'lesson':n,'nativeImportPassed':True,'projects':[{'name':p['name'],'blocks':p['blocks'],'bad':p['bad']} for p in native['projects']],'visualReview':visual,'slides':24})
 (validation/'course-summary.json').write_text(json.dumps({'lessons':lessons,'realAndroidDeviceTested':False,'totalSlides':1347},ensure_ascii=False,indent=2),encoding='utf8')
 prior=(REPO/'README.md').read_text(encoding='utf8')
 preserved=prior[prior.index('## 功能与文档'):]
 preserved=preserved.replace('2.3.3 的 `Source-and-Patches.zip`','2.3.4 的 `Source-and-Patches.zip`')
 rows='\n'.join(f'| {v} | [{v} → 2.3.4](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/download/v2.3.4/Yuxuan-Programming-Studio-Update-{v}-to-2.3.4.exe) |' for v in ['2.2.0','2.3.1','2.3.2','2.3.3'])
 readme='''# 羽轩编程工作台 · Yuxuan Programming Studio

Windows x64 本地编程平台，集成 App Inventor、Mixly 桌面编程、Python 和 C++。当前版本 **2.3.4**。

## 下载与升级

[Gitee分版本发布页](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/tag/v2.3.4) · [GitHub完整附件](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.4)

| 当前版本 | 使用的更新包 |
| --- | --- |
'''+rows+'''
| 2.3.0 | 先升级至2.3.1，再使用本版对应包 |
| 首次安装 | 安装[完整2.2.0](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.2.0)，再使用2.2.0直升包 |

本次更新包含全部56课本地资料，体积较大。保存工程并退出软件，运行匹配的更新包并选择原安装目录；保留项目、依赖和激活信息。已安装教学预览的2.3.3也可更新。[详细升级说明](docs/UPGRADE-2.3.4.md)。

更新清单优先从Gitee读取，只登记上传成功的镜像；超出Gitee附件限制的大文件使用GitHub完整附件。安装包校验大小和SHA256。

## 56课教学项目

- 8阶段、56课，每课90分钟，共84小时。创意表达、编程基础、动画游戏、声音传感器、数据工具、网络应用、ESP32物联网、毕业项目依次推进。
- 168个工程：每课含完整答案、课堂支架、纯界面起始版，可直接打开到个人工作区。
- 56份可编辑PPT及备注、教案、学生任务单、素材、真实积木参考图和答案APK。网络课程附Python课堂服务；硬件课程附串口、经典蓝牙、BLE及Wi-Fi TCP固件与接线说明。
- 教学首页右侧课程路线占半屏；个人项目表格、切换按钮、文件夹和资料入口统一蓝白布局，适配窄窗口。中文课程文件夹可用；内部工程标识采用英文数字以兼容编译链。
- 修复Windows本地项目存储长键名与NTFS流问题，兼容旧文件迁移、删除。

![教学项目与课程路线](docs/images/2.3.4-teaching.png)

[课次内的工程与资料入口](docs/images/2.3.4-lesson.png) · [个人项目布局](docs/images/2.3.4-projects.png)

课程资料已随更新安装，可在App Inventor“我的项目 → 教学项目”中使用；也可单独下载发布附件中的8个阶段资料包。下载后解压，先阅读各课“先读我”。

168个AIA通过平台导入与积木检查，56份答案APK编译完成；56份PPT共1347页经过逐页渲染检查。课堂API在Python3.8.9及3.13.16验证；六份ESP32固件在2.0.17核心编译。**未进行Android真机或实物开发板联调**，权限、传感器和通信功能请按教案在设备上验收。

'''+preserved
 (REPO/'README.md').write_text(readme,encoding='utf8')
 notes='''羽轩编程工作台 **2.3.4**，Windows x64。

### 56课教学项目与页面调整

新增完整8阶段56课，每课90分钟。每课含完整答案、课堂支架、纯界面起始版，共168个可直接打开的工程；软件内可下载PPT及完整资料，含教案、任务单、素材、积木参考图和答案APK。第19课保留原案例。

教学首页右侧显示课程路线；优化教学/个人项目切换、列表、文件夹和资料按钮的比例与窄窗口布局。中文课程目录和资料名可用，内部工程名沿用英文数字以兼容Android编译链。修复Windows本地项目存储中的长键名/NTFS流问题，支持旧数据迁移和删除。

网络课附标准库Python课堂服务，ESP32课附串口、经典蓝牙、BLE和Wi-Fi TCP固件与接线资料。56份PPT共1347页逐页渲染检查；168个AIA导入/坏块检查通过，56份完整答案APK编译。课堂API双Python版本验证，ESP32六种固件核心2.0.17编译通过。未做Android真机或实物硬件联调。

### 更新方式

提供 **2.2.0、2.3.1、2.3.2、2.3.3 → 2.3.4** 四种直升包，选择与当前版本匹配的包，退出软件后安装到原目录。含教学预览的2.3.3可升级。首次安装先装完整2.2.0，2.3.0先升到2.3.1。

本次包含全部课程本地资料，体积大于普通小补丁；保留个人项目、依赖及授权，支持重复覆盖与合并卸载。Mixly仍为桌面版，无仿真；保留前版Python/C++缩放与侧栏等功能。

附件包含四个更新包、8个阶段独立课程资料包、源码与补丁、使用/升级说明、更新日志、SHA256及更新清单。Gitee保留版本页面和可用镜像，完整大附件由GitHub提供；只把已验证的镜像写入自动更新清单。

[Gitee发布页](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/tag/v2.3.4) · [GitHub完整附件](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.4)
'''
 (HERE/'release-notes.md').write_text(notes,encoding='utf8')
 for a,b in [('使用说明.txt','User-Guide.txt'),('UPGRADE.md','UPGRADE.md'),('CHANGELOG.txt','CHANGELOG.txt')]:copy(HERE/a,HERE/'package'/b)
 for f in (ROOT/'outputs/课程案例/56课完整课程包').glob('Stage*.zip'):copy(f,HERE/'package'/f.name)
 copy(ROOT/'outputs/课程案例/56课完整课程包/课程索引.md',HERE/'package/Course-Index.md')
 print('Staged public source and course release assets',flush=True)
def bundle():
 validation=REPO/'validation/release-2.3.4'
 report=json.loads((ROOT/'work/r234/install-acceptance.json').read_text(encoding='utf-8-sig'));assert report['ok'] and report['userStateRestored']
 summary={k:report[k] for k in ['ok','installerSHA256','freshExit','patchExit','reinstallExit','uninstallExit','preservedFiles','userStateRestored','mergedUninstallVerified','emptyDirectoryRejected']}
 summary['payloadVerifiedFiles']=report['payload']['verifiedFiles'];summary['smokeTests']=report['smoke']['tests'];summary['preservationTests']=report['preservationSmoke']['tests']
 (validation/'acceptance-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
 copy(HERE/'updater-compatibility.json',validation/'updater-compatibility.json')
 copy(HERE/'build-check.json',validation/'build-check.json')
 secret=runpy.run_path(str(ROOT/'work/release-2.3.1/gitee-publish.py'))['token']().encode();count=0;total=0
 out=HERE/'package/Source-and-Patches.zip'
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(REPO.rglob('*')):
   if not p.is_file() or '.git' in p.relative_to(REPO).parts:continue
   rel=p.relative_to(REPO).as_posix()
   if rel=='update.json':continue
   raw=p.read_bytes();assert secret not in raw,rel
   assert not re.search(rb'YX-[0-9A-F]{8}(?:-[0-9A-F]{8}){3}',raw),rel
   assert not re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]+[A-Za-z0-9+/\r\n]{64,}',raw),rel
   assert not re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})',raw),rel
   assert not any(x in rel.lower() for x in ['device-license.bin','license-state.json','.dpapi','cookies.json']),rel
   z.writestr(rel,raw);count+=1;total+=len(raw)
 with zipfile.ZipFile(out) as z:assert z.testzip() is None
 (HERE/'source-audit.json').write_text(json.dumps({'passed':True,'files':count,'uncompressedBytes':total,'bytes':out.stat().st_size,'sha256':hashlib.file_digest(out.open('rb'),'sha256').hexdigest()},indent=2),encoding='utf8')
 print('Source audit passed: '+str(count)+' files',flush=True)
if __name__=='__main__':{'stage':stage,'bundle':bundle}[sys.argv[1]]()
