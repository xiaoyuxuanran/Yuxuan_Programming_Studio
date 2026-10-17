from pathlib import Path
import hashlib,json,shutil,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];NATIVE=ROOT/'work/native'
source=NATIVE/'resources/distribution-source';adapt=source/'mixly-adaptation'
adapt.mkdir(parents=True,exist_ok=True)
for name in ['SuiteLauncher.cs','SuiteLicense.cs','SuiteUpdates.cs','Setup.iss']:shutil.copy2(ROOT/'work'/name,source/name)
for name in ['suite-main.js','preload.js','compiler-paths.py','sdk-junction.ps1','prepare-mixly.py','workspace-recovery.js','workspace-theme.css','home.js','home.html','home.css','fix-desktop.py','cloud-fallback.js']:
    shutil.copy2(ROOT/'work/mixly'/name,adapt/name)
shutil.copytree(ROOT/'work/mixly/bluetooth',adapt/'bluetooth',dirs_exist_ok=True)
own=source/'release-2.3.2';own.mkdir(exist_ok=True)
for name in ['prepare-package.py','snapshot-installed.py','CHANGELOG.txt']:shutil.copy2(HERE/name,own/name)

def included(p):
    rel=p.relative_to(NATIVE).as_posix()
    return p.is_file() and '__pycache__' not in p.parts and not rel.startswith(('mixly/web/','server/war/WEB-INF/authkey/','server/war/WEB-INF/keystore/','server/war/WEB-INF/appengine-generated/')) and rel not in ['LayoutCheck.exe','mixly/arduino-cli/Arduino15/inventory.yaml'] and not (rel.startswith('AppInventor-2.') and rel.endswith('.exe'))
files={}
paths=NATIVE.rglob('*')
if '--refresh-known-files' in sys.argv:
    files=json.loads((HERE/'target-files.json').read_text(encoding='utf-8'))['files']
    changed=set()
    for version in ['2.2.0','2.3.1']:
        changed.update(c['path'] for c in json.loads((HERE/('update-manifest-'+version+'.json')).read_text(encoding='utf-8'))['files'])
    paths=[NATIVE/rel for rel in changed]
for p in paths:
    if included(p):
        with p.open('rb') as f:files[p.relative_to(NATIVE).as_posix()]={'sha256':hashlib.file_digest(f,'sha256').hexdigest(),'bytes':p.stat().st_size}
(HERE/'target-files.json').write_text(json.dumps({'version':'2.3.2','files':files},indent=2),encoding='utf-8')
template=(ROOT/'work/Setup.iss').read_text(encoding='utf-8-sig')
for version in ['2.2.0','2.3.1']:
    base=json.loads((HERE/('base-'+version+'.json')).read_text(encoding='utf-8'))['files'];changes=[]
    for rel,details in files.items():
        old=base.get(rel,{}).get('sha256')
        if old!=details['sha256']:changes.append({'path':rel,'oldSHA256':old,**details})
    manifest={'base':version,'version':'2.3.2','totalBytes':sum(c['bytes'] for c in changes),'files':changes}
    (HERE/('update-manifest-'+version+'.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    start=template.index('[Files]');end=template.index('[Icons]',start)
    lines=['[Files]']
    for c in changes:
        p=NATIVE/c['path'];parent=Path(c['path']).parent.as_posix();dest='{app}'+('\\'+parent.replace('/','\\').replace('{','{{') if parent!='.' else '')
        src=str(p) # Source is a literal build-time path; only DestDir expands constants.
        lines.append(f'Source: "{src}"; DestDir: "{dest}"; Flags: ignoreversion')
    setup=template[:start]+'\n'.join(lines)+'\n\n'+template[end:]
    setup=setup.replace('OutputBaseFilename=AppInventor-Offline-Setup-x64','OutputBaseFilename=Yuxuan-Programming-Studio-Update-'+version+'-to-2.3.2')
    setup=setup.replace('OutputDir=..\\outputs','OutputDir=package').replace('SetupIconFile=native\\resources\\brand.ico','SetupIconFile='+str(NATIVE/'resources/brand.ico'))
    setup=setup.replace('AppVersion=2.3.2','AppVersion=2.3.2\nUninstallLogMode=append\nInfoBeforeFile='+str(HERE/'before-install.txt'))
    setup=setup.replace('Compression=lzma2/normal','Compression=lzma2/max')
    checks=[(c['path'],c['oldSHA256'],c['sha256']) for c in changes if c['oldSHA256']]
    for rel in ['AppInventor.exe','AppInventorCore.exe','runtime/python3.13.16/python.exe','mixly/arduino-cli/arduino-cli.exe']:
        if not any(x[0]==rel for x in checks):checks.append((rel,base[rel]['sha256'],files[rel]['sha256']))
    code='''
[Code]
function CheckBaseFile(const Relative, BaseHash, NewHash: String): String;
var Digest: String;
begin
  Result := '';
  if not FileExists(AddBackslash(ExpandConstant('{app}')) + Relative) then begin
    Result := '基础文件缺失，请选择原安装目录：' + Relative; Exit;
  end;
  try Digest := Lowercase(GetSHA256OfFile(AddBackslash(ExpandConstant('{app}')) + Relative));
  except Result := '无法检查基础文件，请先退出软件：' + Relative; Exit; end;
  if (Digest <> BaseHash) and (Digest <> NewHash) then
    Result := '版本或文件不匹配，请下载与当前版本对应的更新包：' + Relative;
end;
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not FileExists(ExpandConstant('{app}\\unins000.dat')) then begin
    Result := '请先安装完整基础版，并选择原安装目录。此文件是更新包。'; Exit;
  end;
'''
    def quote(s):return s.replace("'","''")
    for rel,old,new in checks:
        code+="  Result := CheckBaseFile('"+quote(rel.replace('/','\\'))+"', '"+old+"', '"+new+"');\n  if Result <> '' then Exit;\n"
    code+='end;\n'
    (HERE/('Update-'+version+'.iss')).write_text(setup+code,encoding='utf-8-sig')
    print(json.dumps({'base':version,'files':len(changes),'bytes':manifest['totalBytes'],'checks':len(checks)}),flush=True)
