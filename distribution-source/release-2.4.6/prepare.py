from pathlib import Path
import json,hashlib,shutil,subprocess,os,re
H=Path(__file__).resolve().parent;R=H.parents[1];N=R/'work/native';OLD=R/'work/release-2.4.5'
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
def sha(p):
 with open('\\\\?\\'+str(p.absolute()),'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8-sig' if p.suffix=='.iss' else 'utf8')
s=R/'work/SuiteUpdates.cs';put(s,s.read_text(encoding='utf8').replace('2.4.5','2.4.6'))
s=R/'work/Setup.iss';put(s,s.read_text(encoding='utf-8-sig').replace('2.4.5','2.4.6').replace('lzma2/ultra64','lzma2/normal').replace('LZMADictionarySize=131072','LZMADictionarySize=65536'))
notes='''羽轩编程工作台 2.4.6 · 2026-10-29

新增羽轩蓝白启动动画：Logo 开场、五段标题、环形刻度、英文逐字显示和揭幕转场。
约 7 秒自动进入启动器，Esc 或右上角按钮随时跳过；快捷方式参数 --no-startup-animation 可禁用。
启动动画仅用于展示，之后仍按原流程检查激活授权，不自动启动任何编辑器。
提供完整安装包和从 2.4.5 升级的增量安装包；兼容已安装启动动画补丁的 2.4.5。
完整包可多选 App Inventor、Mixly、Python、C++，也可仅安装其中一个；共享授权依赖自动安装。增量包不含选择页。
保留四类编程环境、8 阶段 56 课资料、项目及激活数据。

'''
put(H/'CHANGELOG.txt',notes+(OLD/'CHANGELOG.txt').read_text(encoding='utf8'))
put(H/'User-Guide.txt',(OLD/'User-Guide.txt').read_text(encoding='utf8').replace('2.4.5','2.4.6')+'\n启动动画约 7 秒自动结束；按 Esc 或右上角按钮可跳过。快捷方式参数 --no-startup-animation 可禁用，--preview-startup-animation 仅预览动画后退出。\n')
put(H/'UPGRADE.md','''# 安装或升级到 2.4.6

新用户直接运行 AppInventor-Offline-Setup-x64.exe，不需要旧版。完整包可勾选四个项目中的一个或多个，默认全选；共享授权依赖自动安装。未安装入口会标记为未安装。重新运行完整包可添加项目，不删除已安装项目。增量包没有选择页面。

2.4.5 用户（含已安装启动动画补丁）：保存工程并退出工作台，运行 Yuxuan-Programming-Studio-Update-2.4.5-to-2.4.6.exe，选择原安装目录。

其他旧版本请选择完整包覆盖原目录。保留个人项目、第三方依赖与授权信息。首次使用仍需联网激活。升级前可备份 %LOCALAPPDATA%\\AppInventorOffline 和外部工程。

新增动画会自动结束，Esc 只跳过动画，不跳过授权检查。
''')
put(H/'before-install.txt','羽轩编程工作台 2.4.6\n\n整合蓝白启动动画，按 Esc 可跳过。\n完整包可全新安装；增量包适用 2.4.5（含动画补丁）。\n已有版本请保存项目、退出软件并安装到原目录。个人项目和授权数据保留。')
for name in ['CHANGELOG.txt','User-Guide.txt','UPGRADE.md']:copy(H/name,H/'package'/name)
copy(H/'CHANGELOG.txt',N/'resources/CHANGELOG.txt');copy(H/'User-Guide.txt',N/'resources/使用说明.txt');copy(H/'User-Guide.txt',N/'使用说明.txt')
put(N/'resources/build-version.txt','2026.10.29-startup-2.4.6\n')
for name in ['SuiteLauncher.cs','SuiteUpdates.cs','SuiteLicense.cs','Setup.iss']:copy(R/'work'/name,N/'resources/distribution-source'/name)
for name in ['prepare.py','CHANGELOG.txt','User-Guide.txt','UPGRADE.md']:copy(H/name,N/'resources/distribution-source/release-2.4.6'/name)
subprocess.run(['C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe','/nologo','/target:winexe','/platform:x64','/win32icon:'+str(N/'resources/brand.ico'),'/out:'+str(N/'AppInventor.exe'),'/r:System.Windows.Forms.dll','/r:System.Drawing.dll','/r:System.Core.dll','/r:System.Web.Extensions.dll',*[str(R/'work'/n) for n in ['SuiteLauncher.cs','SuiteUpdates.cs','SuiteLicense.cs']]],check=True)
base=json.loads((OLD/'target-files.json').read_text(encoding='utf8'))['files'];paths=set(base)
paths.update('resources/distribution-source/release-2.4.6/'+n for n in ['prepare.py','CHANGELOG.txt','User-Guide.txt','UPGRADE.md'])
files={};changes=[]
for rel in sorted(paths):
 p=N/rel;d={'sha256':sha(p),'bytes':os.stat('\\\\?\\'+str(p)).st_size};files[rel]=d
 if base.get(rel)!=d:changes.append(rel)
for rel in changes:assert rel.startswith(('resources/','AppInventor.exe','使用说明.txt','studio/server.py','studio/studio.js')),rel
put(H/'target-files.json',json.dumps({'version':'2.4.6','files':files},indent=2))
put(H/'payload-audit.json',json.dumps({'ok':True,'files':len(files),'changedFiles':changes,'unchangedRuntimeAndCourseBytes':True,'studioAvailabilityChanged':True,'uncompressedBytes':sum(x['bytes'] for x in files.values()),'base':'2.4.5'},indent=2))
template=(R/'work/Setup.iss').read_text(encoding='utf-8-sig').replace('OutputDir=..\\outputs','OutputDir=package').replace('SetupIconFile=native\\resources\\brand.ico','SetupIconFile='+str(N/'resources/brand.ico')).replace('SetupLogging=yes','SetupLogging=yes\nInfoBeforeFile='+str(H/'before-install.txt'))
def component(rel):
 if rel=='AppInventorCore.exe' or rel.startswith(('server/','buildserver/','usb/','examples/','runtime/java11/','runtime/java17/')) or rel=='resources/KeyczarTool.jar':return 'ai'
 if rel.startswith('mixly/'):return 'mixly'
 if rel.startswith('runtime/python3.8.9/'):return 'python'
 if rel.startswith('runtime/llvm-mingw/'):return 'cpp'
 if rel.startswith('studio/'):return 'python or cpp'
 return None

def recipe(paths, selective=False):
 a=template.index('[Files]');b=template.index('[Icons]',a);entries=['[Files]']
 for rel in sorted(paths):
  parent=Path(rel).parent.as_posix();dest='{app}'+('\\'+parent.replace('/','\\').replace('{','{{') if parent!='.' else '')
  entries.append(f'Source: "{N/rel}"; DestDir: "{dest}"; Flags: ignoreversion'+('; Components: '+component(rel) if selective and component(rel) else ''))
 return template[:a]+'\n'.join(entries)+'\n\n'+template[b:]
full=recipe(files,True)
sections='[Types]\nName: "full"; Description: "完整安装 - 全部四个项目"\nName: "custom"; Description: "自定义安装 - 可选一个或多个"; Flags: iscustom\n\n[Components]\nName: "ai"; Description: "App Inventor - 安卓应用开发与 56 课教学资料"; Types: full\nName: "mixly"; Description: "Mixly - AVR / ESP8266 / ESP32 硬件编程"; Types: full\nName: "python"; Description: "Python - 双版本运行环境与图形库"; Types: full\nName: "cpp"; Description: "C++ - 代码编辑器与 Clang++ 编译器"; Types: full\n\n'
full=full.replace('[Files]',sections+'[Files]')
full+="\n[Code]\nfunction PrepareToInstall(var NeedsRestart: Boolean): String;\nbegin\n  Result := '';\n  if not (WizardIsComponentSelected('ai') or WizardIsComponentSelected('mixly') or WizardIsComponentSelected('python') or WizardIsComponentSelected('cpp')) then\n    Result := 'Select at least one project to install.';\nend;\n"
put(H/'Setup-Full.iss',full)
put(H/'component-files.json',json.dumps({rel:component(rel) for rel in files},indent=2))
patch=recipe(changes).replace('OutputBaseFilename=AppInventor-Offline-Setup-x64','OutputBaseFilename=Yuxuan-Programming-Studio-Update-2.4.5-to-2.4.6')
checks=list(changes)+['AppInventorCore.exe','runtime/python3.13.16/python.exe','mixly/arduino-cli/arduino-cli.exe']
code='''
[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var Digest: String;
begin
  Result := '';
  if not FileExists(ExpandConstant('{app}\\unins000.dat')) then begin Result := 'Select the existing 2.4.5 installation folder; this is an update package.'; Exit; end;
'''
for rel in checks:
 if rel not in base:continue
 allowed={base[rel]['sha256'],files[rel]['sha256']}
 if rel=='AppInventor.exe':allowed.add(sha(R/'work/startup-animation/AppInventor.exe'))
 if rel=='resources/distribution-source/SuiteLauncher.cs':allowed.add(sha(R/'work/startup-animation/StartupLauncher-2.4.5.cs'))
 q=rel.replace('/','\\').replace("'","''")
 code+=f"  if not FileExists(ExpandConstant('{{app}}\\{q}')) then begin Result := 'Missing base file: {q}'; Exit; end;\n"
 code+=f"  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{{app}}\\{q}'))); except Result := 'Close the workbench before updating.'; Exit; end;\n"
 code+='  if '+ ' and '.join("(Digest <> '"+v+"')" for v in sorted(allowed))+f" then begin Result := 'Incompatible base; use the complete installer. File: {q}'; Exit; end;\n"
code+='end;\n';put(H/'Update-2.4.5.iss',patch+code)
put(H/'update-manifest-2.4.5.json',json.dumps({'base':'2.4.5','version':'2.4.6','files':changes,'bytes':sum(files[r]['bytes'] for r in changes)},indent=2))
print(json.dumps({'files':len(files),'changedFiles':len(changes),'updateBytes':sum(files[r]['bytes'] for r in changes)}),flush=True)
