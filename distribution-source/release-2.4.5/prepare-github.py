from pathlib import Path
import json,shutil,re,zipfile,runpy,hashlib,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];REPO=ROOT/'work/github-publish/Yuxuan_Programming_Studio';NATIVE=ROOT/'work/native'
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
def stage():
 shutil.copytree(NATIVE/'resources/distribution-source',REPO/'distribution-source',dirs_exist_ok=True)
 copy(NATIVE/'mixly/UPSTREAM.json',REPO/'distribution-source/mixly-adaptation/UPSTREAM.json')
 p=REPO/'distribution-source/course56/blueprints/author_remaining.py'
 if p.exists():p.unlink()
 for n in ['prepare.py','prepare-validation.py','prepare-release-tools.py','prepare-github.py','publish-release.py','verify-public.py','Setup-Full.iss','target-files.json','payload-audit.json','CHANGELOG.txt','UPGRADE.md','User-Guide.txt']:
  copy(HERE/n,REPO/'distribution-source/release-2.4.5'/n)
 for n in ['acceptance-full.ps1','installed-smoke.py','installed-teaching.cjs','studio-view-check.cjs','UpdateCompatibilityCheck.cs','UpdateNetworkCheck.cs']:
  copy(HERE/n,REPO/'validation/release-2.4.5'/n)
 copy(HERE/'CHANGELOG.txt',REPO/'CHANGELOG.txt');copy(HERE/'User-Guide.txt',REPO/'docs/使用说明.txt');copy(HERE/'UPGRADE.md',REPO/'docs/UPGRADE-2.4.5.md')
 current=(REPO/'README.md').read_text(encoding='utf8');tail=current[current.index('## 功能与文档'):]
 tail=tail.replace('2.3.4 的 `Source-and-Patches.zip`','2.4.5 的 `Source-and-Patches.zip`')
 text='''# 羽轩编程工作台 · Yuxuan Programming Studio

Windows x64 本地编程平台，集成 App Inventor、Mixly 桌面编程、Python 和 C++。当前版本 **2.4.5 完整安装版**。

## 直接下载与安装

**[下载2.4.5完整安装包](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/download/v2.4.5/AppInventor-Offline-Setup-x64.exe)** · [GitHub发布页](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.4.5) · [Gitee版本页](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/tag/v2.4.5)

本版可在新电脑直接安装，无需先装2.2.0或其他旧版。完整包包含四类编辑器、Java/Python/C++运行及编译环境、Mixly四类硬件支持、全部56课本地教学资料；不需要另装WSL。

已有版本请保存工程、退出工作台及代码窗口，再安装到原目录。覆盖安装保留个人项目、第三方依赖和授权信息；原有客户端的“检查更新”也能获取本版完整安装包。[安装与升级说明](docs/UPGRADE-2.4.5.md)。

首次使用仍需联网激活，之后可在授权有效期内离线使用；联网时校验授权。公开附件不包含激活码或已激活凭证。

本次为完整安装分发，功能沿用2.3.4。大安装包由GitHub提供；Gitee同步源码、版本说明、更新清单及可容纳的附件。软件优先读取Gitee清单，安装包校验大小与SHA256。

## 包含56课教学项目

8阶段、56课，每课90分钟，共84小时。每课含完整答案、课堂支架、纯界面起始版，共168个工程；本地资料含可编辑PPT及备注、教案、任务单、素材、积木参考图及答案APK。网络课附Python课堂服务，ESP32课附串口、经典蓝牙、BLE、Wi-Fi TCP固件和接线说明。

App Inventor → 我的项目 → 教学项目，即可按阶段与课次使用；中文课程目录可用。课程内容与2.3.4相同，[独立阶段课程包仍可从2.3.4下载](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.4)。

![教学项目与课程路线](docs/images/2.3.4-teaching.png)

168个AIA通过平台导入与积木检查，56份完整答案APK编译完成，56份PPT共1347页逐页渲染检查。未进行Android真机或实物开发板联调。

'''+tail
 (REPO/'README.md').write_text(text,encoding='utf8')
 notes='''羽轩编程工作台 **2.4.5 完整安装版**，Windows x64。

### 可直接安装

本版是全量安装包，**不需要先安装2.2.0或任何中间版本**。内含App Inventor、Mixly桌面版、Python3.8.9/3.13.16、C++及全部运行/编译环境；无需另装WSL、Java、Python或C++工具链。

完整保留2.3.4功能与8阶段56课教学资料：168个工程、PPT、教案、任务单、素材、参考图和答案APK；保留Python/C++双主题、字号与侧栏控制、图形库、Mixly四类硬件/云端库/串口调试和驱动入口。

### 下载与升级

**[下载完整安装包](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/download/v2.4.5/AppInventor-Offline-Setup-x64.exe)**

新用户直接安装。已有版本保存项目并退出软件，再安装到原目录；保留个人项目、依赖及授权信息。原有“检查更新”入口也可获取完整安装包。首次使用仍须联网激活，之后按授权有效期允许离线使用。

Gitee同步版本页面、源码与可用的小附件，完整安装包由GitHub提供；软件优先读取Gitee更新清单，下载校验大小和SHA256。

课程内容与2.3.4相同；如仅需独立课程资料，可继续下载[2.3.4的8阶段资料包](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.4)。未进行Android真机或实物开发板联调。
'''
 (HERE/'release-notes.md').write_text(notes,encoding='utf8')
 for n in ['CHANGELOG.txt','User-Guide.txt','UPGRADE.md']:copy(HERE/n,HERE/'package'/n)
 print('Prepared 2.4.5 public source, docs and release notes',flush=True)
def bundle():
 report=json.loads((ROOT/'work/r245/install-acceptance.json').read_text(encoding='utf-8-sig'));assert report['ok'] and report['userStateRestored']
 summary={k:report[k] for k in ['ok','installerSHA256','freshExit','reinstallExit','uninstallExit','preservedFiles','userStateRestored','mergedUninstallVerified','fullInstallerVerified']}
 summary.update(payload=report['payload'],smokeTests=report['smoke']['tests'],preservationTests=report['preservationSmoke']['tests'])
 v=REPO/'validation/release-2.4.5';v.mkdir(exist_ok=True)
 (v/'acceptance-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
 copy(HERE/'updater-compatibility.json',v/'updater-compatibility.json')
 secret=runpy.run_path(str(ROOT/'work/release-2.3.1/gitee-publish.py'))['token']().encode();count=0;size=0
 bundle=HERE/'package/Source-and-Patches.zip'
 with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(REPO.rglob('*')):
   if not p.is_file() or '.git' in p.relative_to(REPO).parts:continue
   rel=p.relative_to(REPO).as_posix()
   if rel=='update.json':continue
   raw=p.read_bytes();assert secret not in raw,rel
   assert not re.search(rb'YX-[0-9A-F]{8}(?:-[0-9A-F]{8}){3}',raw),rel
   assert not re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]+[A-Za-z0-9+/\r\n]{64,}',raw),rel
   assert not re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})',raw),rel
   assert not any(n in rel.lower() for n in ['device-license.bin','.dpapi','cookies.json','license-state.json']),rel
   z.writestr(rel,raw);count+=1;size+=len(raw)
 with zipfile.ZipFile(bundle) as z:assert z.testzip() is None
 (HERE/'source-audit.json').write_text(json.dumps({'passed':True,'files':count,'sourceBytes':size,'zipBytes':bundle.stat().st_size,'sha256':hashlib.file_digest(bundle.open('rb'),'sha256').hexdigest()},indent=2),encoding='utf8')
 print('Passed public source audit: '+str(count)+' files',flush=True)
if __name__=='__main__':{'stage':stage,'bundle':bundle}[sys.argv[1]]()
