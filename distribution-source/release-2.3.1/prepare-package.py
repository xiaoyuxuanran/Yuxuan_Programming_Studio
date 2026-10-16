from pathlib import Path
import hashlib,json,shutil,re,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];NATIVE=ROOT/'work/native'
base=json.loads((HERE/'base-2.3.0.json').read_text())['files']
source=NATIVE/'resources/distribution-source'
(source/'mixly4').mkdir(exist_ok=True)
for name in ('SuiteLauncher.cs','SuiteLicense.cs','SuiteUpdates.cs','Setup.iss'):shutil.copy2(ROOT/'work'/name,source/name)
for name in ('fix-bluetooth.py','prepare-build.py','stage-web.py'):
    shutil.copy2(ROOT/'work/mixly4'/name,source/'mixly4'/name)
target=source/'release-2.3.1';target.mkdir(exist_ok=True)
for name in ('BundledExtensions.java','patch-appinventor.py','stage-appinventor.py','prepare-extensions.py','prepare-package.py','CHANGELOG.txt'):
    shutil.copy2(HERE/name,target/name)
shutil.copytree(HERE/'appinventor-source',target/'appinventor-source',dirs_exist_ok=True)
shutil.copytree(HERE/'bundled-extensions',target/'bundled-extensions',dirs_exist_ok=True)
for name in ('SuiteLauncher.cs','SuiteLicense.cs','SuiteUpdates.cs'):assert (source/name).stat().st_size>100
# Drop only newly generated, inactive development bundles, preserving every 2.3.0 file.
ode=NATIVE/'server/war/ode';active=set(re.findall('[A-F0-9]{32}',(ode/'ode.nocache.js').read_text()))
for file in ode.glob('*.cache.js'):
    stem=file.name.split('.')[0];rel=file.relative_to(NATIVE).as_posix()
    if rel not in base and stem not in active:
        assert file.resolve().is_relative_to(ode.resolve());file.unlink()
        folder=ode/'deferredjs'/stem
        if folder.exists():
            assert folder.resolve().is_relative_to((ode/'deferredjs').resolve());shutil.rmtree(folder)
board=NATIVE/'mixly/web/site/editor/boards/default/arduino_esp32'
current=(board/'index.xml').read_text(encoding='utf-8')
for file in board.glob('main.bundle.*.js'):
    if file.relative_to(NATIVE).as_posix() not in base and file.name not in current:
        assert file.resolve().is_relative_to(board.resolve());file.unlink()
changes=[]
paths=[NATIVE/c['path'] for c in json.loads((HERE/'update-manifest.json').read_text(encoding='utf-8'))['files']] if '--refresh-known-files' in sys.argv else NATIVE.rglob('*')
for p in paths:
    if not p.is_file():continue
    rel=p.relative_to(NATIVE).as_posix()
    if rel.startswith(('mixly/runtime/','mixly/src/')) or '__pycache__' in p.parts or rel in ('LayoutCheck.exe','mixly/arduino-cli/Arduino15/inventory.yaml'):continue
    digest=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
    if rel not in base or base[rel]['sha256']!=digest:changes.append({'path':rel,'oldSHA256':base.get(rel,{}).get('sha256'),'sha256':digest,'bytes':p.stat().st_size})
assert changes and any(c['path']=='AppInventor.exe' for c in changes)
manifest={'base':'2.3.0','version':'2.3.1','files':changes,'totalBytes':sum(c['bytes'] for c in changes)}
(HERE/'update-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
def quote(s):return s.replace("'","''")
setup=(ROOT/'work/Setup.iss').read_text(encoding='utf-8')
start=setup.index('[Files]');end=setup.index('[Icons]',start)
lines=['[Files]']
for c in changes:
    p=NATIVE/c['path'];parent=Path(c['path']).parent.as_posix()
    dest='{app}'+('\\'+parent.replace('/','\\') if parent!='.' else '')
    lines.append(f'Source: "{p}"; DestDir: "{dest}"; Flags: ignoreversion')
setup=setup[:start]+'\n'.join(lines)+'\n\n'+setup[end:]
setup=setup.replace('OutputBaseFilename=AppInventor-Offline-Setup-x64','OutputBaseFilename=Yuxuan-Programming-Studio-Update-2.3.0-to-2.3.1')
setup=setup.replace('OutputDir=..\\outputs','OutputDir=package').replace('SetupIconFile=native\\resources\\brand.ico','SetupIconFile='+str(NATIVE/'resources/brand.ico'))
setup=setup.replace('AppVersion=2.3.1','AppVersion=2.3.1\nAppComments=Incremental upgrade from version 2.3.0\nUninstallLogMode=append')
checks=[]
for c in changes:
    if c['oldSHA256']:checks.append((c['path'],c['oldSHA256'],c['sha256']))
for rel in ('AppInventorCore.exe','runtime/python3.13.16/python.exe','mixly/web/server.py'):
    if not any(c[0]==rel for c in checks):checks.append((rel,base[rel]['sha256'],base[rel]['sha256']))
code='''
[Code]
function CheckBaseFile(const Relative, BaseHash, NewHash: String): String;
var Path, Digest: String;
begin
  Result := '';
  Path := AddBackslash(ExpandConstant('{app}')) + Relative;
  if not FileExists(Path) then begin
    Result := '缺少基础文件：' + Relative + '。请安装完整版本或选择正确目录。';
    Exit;
  end;
  try
    Digest := Lowercase(GetSHA256OfFile(Path));
  except
    Result := '无法检查文件：' + Relative + '。请先退出工作台。';
    Exit;
  end;
  if (Digest <> BaseHash) and (Digest <> NewHash) then
    Result := '版本或文件不匹配：' + Relative + '。此增量包只适用于完整的 2.3.0（或修复 2.3.1）。';
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not FileExists(ExpandConstant('{app}\\unins000.dat')) then begin
    Result := '请先安装羽轩编程工作台 2.3.0，并选择原安装目录。此文件是增量升级包。';
    Exit;
  end;
'''
for rel,old,new in checks:
    code+="  Result := CheckBaseFile('"+quote(rel.replace('/','\\'))+"', '"+old+"', '"+new+"');\n  if Result <> '' then Exit;\n"
code+='end;\n'
(HERE/'Update.iss').write_text(setup+code,encoding='utf-8-sig')
print(json.dumps({'files':len(changes),'bytes':manifest['totalBytes'],'checks':len(checks)},ensure_ascii=False))
