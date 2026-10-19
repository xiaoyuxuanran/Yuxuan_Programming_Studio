"""Build a self-contained 2.4.5 installer from an explicit audited payload."""
from pathlib import Path
import os,json,hashlib,shutil,re,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];NATIVE=ROOT/'work/native';OLD=ROOT/'work/release-2.3.4';VERSION='2.4.5'
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def longpath(p):
 s=str(p.absolute());return '\\\\?\\'+s if os.name=='nt' and not s.startswith('\\\\?\\') else s
def included(rel):
 return not any(x=='__pycache__' for x in Path(rel).parts) and not rel.startswith(('mixly/web/','server/war/WEB-INF/authkey/','server/war/WEB-INF/keystore/','server/war/WEB-INF/appengine-generated/')) and rel not in ['LayoutCheck.exe','mixly/arduino-cli/Arduino15/inventory.yaml'] and not (rel.startswith('AppInventor-2.') and rel.endswith('.exe')) and not rel.endswith('.pyc')
def sha(p):
 with open(longpath(p),'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def prepare():
 (HERE/'package').mkdir(exist_ok=True)
 old=ROOT/'work/SuiteUpdates.cs';s=old.read_text(encoding='utf8')
 if 'ProductVersion="2.3.4"' in s:
  copy(NATIVE/'AppInventor.exe',HERE/'client-2.3.4-original.exe')
  old.write_text(s.replace('2.3.4','2.4.5'),encoding='utf8')
 assert 'ProductVersion="2.4.5"' in old.read_text(encoding='utf8')
 p=ROOT/'work/Setup.iss';s=p.read_text(encoding='utf-8-sig').replace('AppVersion=2.3.4','AppVersion=2.4.5')
 if 'UninstallLogMode=' not in s:s=s.replace('AppVersion=2.4.5','AppVersion=2.4.5\nUninstallLogMode=append')
 s=re.sub(r'^Compression=.*$','Compression=lzma2/ultra64',s,flags=re.M)
 s=re.sub(r'^SolidCompression=.*$','SolidCompression=yes',s,flags=re.M)
 s=re.sub(r'^LZMANumBlockThreads=.*$','LZMANumBlockThreads=4',s,flags=re.M)
 # Normalize exactly one dictionary directive, even after an interrupted preparation.
 s=re.sub(r'^LZMADictionarySize=.*\n?','',s,flags=re.M)
 s=s.replace('\nCompression=lzma2/ultra64','\nCompression=lzma2/ultra64\nLZMADictionarySize=131072')
 p.write_text(s,encoding='utf-8-sig')
 changelog='''羽轩编程工作台 2.4.5 · 2026-10-19

• 提供完整Windows x64安装包，新电脑无需先安装2.2.0或其他旧版。
• 内含App Inventor、Mixly桌面版、Python、C++及全部运行/编译环境。
• 内含8阶段56课教学项目、168个AIA工程和全部本地课件资料。
• 保留2.3.4的项目页面布局、中文课程目录和Windows存储修复。
• 保留Python双版本、图形库、明暗主题、字号缩放与侧栏开关，及Mixly云端库、串口调试和驱动入口。
• 支持在原目录覆盖更新，保留个人项目、依赖与授权信息。
• 首次使用仍需联网激活；安装包不包含激活码或已激活凭证。

'''+(OLD/'CHANGELOG.txt').read_text(encoding='utf8')
 (HERE/'CHANGELOG.txt').write_text(changelog,encoding='utf8')
 guide='''羽轩编程工作台 2.4.5 完整安装版

适用于Windows 10/11 x64。直接运行AppInventor-Offline-Setup-x64.exe安装，无需先安装任何旧版本，也无需另装WSL、Java、Python或C++编译器。

内含App Inventor、Mixly桌面版、Python3.8.9/3.13.16、Clang++及运行/编译依赖；教学项目含8阶段56课、168个工程、PPT、教案、任务单、素材和配套程序。

新电脑可选择安装目录；已有版本请保存工程、退出工作台和运行中的代码窗口，再安装到原目录。覆盖安装保留个人项目、第三方依赖和授权数据。首次使用必须联网激活，之后可在凭证有效期内离线使用；联网时校验授权。

App Inventor → 我的项目 → 教学项目，按阶段与课次选择完整答案、课堂支架或纯界面起始版。课次页可以下载PPT与完整资料。内部工程标识使用英文数字；中文课程目录和界面文字受支持。

Mixly仍为桌面版，保留Arduino AVR、Arduino ESP8266、Python ESP32、Arduino ESP32、云端库、串口调试和驱动入口，无仿真。

已验证的课程资料来自2.3.4：168个AIA通过导入与积木检查，56份答案APK编译完成，56份PPT共1347页逐页渲染检查。未做Android真机或实物开发板联调。

SHA256SUMS.txt提供附件校验值。正式版与下载地址见GitHub的v2.4.5发布页。
'''
 (HERE/'User-Guide.txt').write_text(guide,encoding='utf8')
 (HERE/'UPGRADE.md').write_text('''# 安装或升级到2.4.5

本版是完整安装包，首次安装直接运行 `AppInventor-Offline-Setup-x64.exe`，不需要2.2.0基础版。

已有版本：保存项目，退出工作台、Mixly和Python/C++程序，运行安装包并选择原安装目录。保留个人项目、依赖及激活信息；升级前建议备份 `%LOCALAPPDATA%\\AppInventorOffline` 和外部工程。

安装包包含四类编辑器、运行环境和全部56课本地资料，压缩文件较大，需留足安装与临时解压空间。激活规则与前版相同。

[GitHub正式版](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.4.5)。软件内“检查更新”也可以获取本版完整安装包。
''',encoding='utf8')
 (HERE/'before-install.txt').write_text('羽轩编程工作台2.4.5完整安装版\n\n内含四类编程环境与全部56课资料，可直接全新安装。\n已有版本请退出软件并选择原安装目录；个人项目、依赖和授权保留。\n\n首次使用仍需联网激活。',encoding='utf8')
 copy(HERE/'CHANGELOG.txt',NATIVE/'resources/CHANGELOG.txt');copy(HERE/'User-Guide.txt',NATIVE/'resources/使用说明.txt');copy(HERE/'User-Guide.txt',NATIVE/'使用说明.txt')
 (NATIVE/'resources/build-version.txt').write_text('2026.10.19-full-2.4.5\n',encoding='utf8')
 source=NATIVE/'resources/distribution-source'
 for n in ['SuiteLauncher.cs','SuiteLicense.cs','SuiteUpdates.cs','Setup.iss']:copy(ROOT/'work'/n,source/n)
 for n in ['prepare.py','CHANGELOG.txt','UPGRADE.md','User-Guide.txt']:copy(HERE/n,source/'release-2.4.5'/n)
 csc='C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'
 subprocess.run([csc,'/nologo','/target:winexe','/platform:x64','/win32icon:'+str(NATIVE/'resources/brand.ico'),'/out:'+str(NATIVE/'AppInventor.exe'),'/r:System.Windows.Forms.dll','/r:System.Drawing.dll','/r:System.Core.dll','/r:System.Web.Extensions.dll',str(ROOT/'work/SuiteLauncher.cs'),str(ROOT/'work/SuiteLicense.cs'),str(ROOT/'work/SuiteUpdates.cs')],check=True)
 files={};prefix=Path(longpath(NATIVE))
 for root,dirs,names in os.walk(prefix,followlinks=False):
  dirs[:]=[d for d in dirs if not (Path(root)/d).is_junction() and included((Path(root)/d).relative_to(prefix).as_posix()+'/')]
  for n in names:
   rel=(Path(root)/n).relative_to(prefix).as_posix()
   if not included(rel):continue
   assert not any(x in rel.lower() for x in ['device-license.bin','.dpapi','cookies.json','running.ini','license-state.json']),rel
   p=NATIVE/rel;files[rel]={'sha256':sha(p),'bytes':os.stat(longpath(p)).st_size}
 (HERE/'target-files.json').write_text(json.dumps({'version':VERSION,'files':files},indent=2),encoding='utf8')
 base=json.loads((OLD/'target-files.json').read_text(encoding='utf8'))['files']
 for rel,d in base.items():
  assert rel in files,rel
  if rel.startswith(('mixly/','studio/','buildserver/','runtime/','license/','usb/','server/')):assert d==files[rel],'Unrelated component changed: '+rel
 setup=s.replace('OutputDir=..\\outputs','OutputDir=package').replace('SetupIconFile=native\\resources\\brand.ico','SetupIconFile='+str(NATIVE/'resources/brand.ico'))
 setup=setup.replace('SetupLogging=yes','SetupLogging=yes\nInfoBeforeFile='+str(HERE/'before-install.txt'))
 a=setup.index('[Files]');b=setup.index('[Icons]',a);entries=['[Files]']
 for rel in sorted(files):
  parent=Path(rel).parent.as_posix();dest='{app}'+('\\'+parent.replace('/','\\').replace('{','{{') if parent!='.' else '')
  entries.append(f'Source: "{NATIVE/rel}"; DestDir: "{dest}"; Flags: ignoreversion')
 setup=setup[:a]+'\n'.join(entries)+'\n\n'+setup[b:]
 (HERE/'Setup-Full.iss').write_text(setup,encoding='utf-8-sig')
 report={'ok':True,'version':VERSION,'files':len(files),'uncompressedBytes':sum(d['bytes'] for d in files.values()),'runtimeAndCourseFilesUnchanged':True,'explicitPayload':True,'privateFilesExcluded':True}
 (HERE/'payload-audit.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
if __name__=='__main__':prepare()
