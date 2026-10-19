"""Stage audited 56-lesson sources and generate deltas from immutable baselines."""
from pathlib import Path
import json,hashlib,shutil,os,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];NATIVE=ROOT/'work/native';COURSE=ROOT/'work/course56'
SOURCE=NATIVE/'resources/distribution-source';VERSION='2.3.4'
BASES=['2.2.0','2.3.1','2.3.2','2.3.3']
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def longpath(p):
 value=str(p.absolute())
 return '\\\\?\\'+value if os.name=='nt' and not value.startswith('\\\\?\\') else value
def sha(p):
 with open(longpath(p),'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def stage():
 for n in ['SuiteLauncher.cs','SuiteLicense.cs','SuiteUpdates.cs','Setup.iss']:copy(ROOT/'work'/n,SOURCE/n)
 for name in ['CHANGELOG.txt','使用说明.txt']:copy(HERE/name,NATIVE/'resources'/name)
 copy(HERE/'使用说明.txt',NATIVE/'使用说明.txt')
 target=SOURCE/'teaching-projects';target.mkdir(exist_ok=True)
 for name in ['README.md','课程大纲.md','TeachingProjectsAction.java','prepare.py','compile.py','catalog.py','catalog.json','teaching-projects.js','teaching-projects.css']:
  copy(ROOT/'work/teaching-projects'/name,target/name)
 for d in ['source','patches']:shutil.copytree(ROOT/'work/teaching-projects'/d,target/d,dirs_exist_ok=True)
 copy(NATIVE/'server/war/index.jsp',SOURCE/'index.jsp')
 target=SOURCE/'course56';target.mkdir(exist_ok=True)
 for name in ['progress.json','STATUS.md','assets-source.json','school-image-source.json','init.py']:copy(COURSE/name,target/name)
 for d in ['content','blueprints','teaching-api']:
  shutil.copytree(COURSE/d,target/d,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for pattern in ['aia_*.py','deck.mjs','package.py','record-visual.py','verify-native.cjs','teaching-ui-check.cjs','final-ui-check.cjs','final-firmware.py','preview.py','preview.template.html','test-preview.cjs','capture-block.cjs','recapture.cjs']:
  for f in (COURSE/'tools').glob(pattern):copy(f,target/'tools'/f.name)
 for d in ['shared','tests','43-serial-protocol','44-45-classic-spp','46-ble-led','47-tcp-ap','48-tcp-sta','49-50-tcp-reliable']:
  shutil.copytree(COURSE/'firmware'/d,target/'firmware'/d,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for n in ['接线与使用说明.md','协议与技术依据.md','tcp_lab_server.py','prepare.py']:copy(COURSE/'firmware'/n,target/'firmware'/n)
 for n in ['build.py','result.json']:copy(COURSE/'storage-fix'/n,target/'storage-fix'/n)
 shutil.copytree(COURSE/'storage-fix/src',target/'storage-fix/src',dirs_exist_ok=True)
 for n in ['prepare-package.py','CHANGELOG.txt','UPGRADE.md']:copy(HERE/n,SOURCE/'release-2.3.4'/n)
 (target/'README.md').write_text('''# 56课课程源文件

课程内容以 content/lessonNN/content.json 为最终审校版本。AIA生成器在 tools/aia_*.py，PPT生成器为 tools/deck.mjs，需 @oai/artifact-tool。生成器路径沿用源码工作区结构；导出的PPT、AIA和配套资料见2.3.4发布附件及软件内教学项目。

author_remaining.py 等初稿脚本没有作为最终课程正文发布。服务测试时的授权文件、浏览器会话、设备数据和本机SDK配置不属于课程源码。验证记录只收录汇总与匿名课程检查结果。

内部App Inventor工程标识沿用英文字母与数字，方便包名和编译链兼容；中文课程目录、界面、资料文件名均受支持。
''',encoding='utf8')
def included(p):
 rel=p.relative_to(NATIVE).as_posix()
 return os.path.isfile(longpath(p)) and '__pycache__' not in p.parts and not rel.startswith(('mixly/web/','server/war/WEB-INF/authkey/','server/war/WEB-INF/keystore/','server/war/WEB-INF/appengine-generated/')) and rel not in ['LayoutCheck.exe','mixly/arduino-cli/Arduino15/inventory.yaml'] and not (rel.startswith('AppInventor-2.') and rel.endswith('.exe')) and p.suffix!='.pyc'
def inventory():
 files={};start=time.monotonic()
 nativeprefix=longpath(NATIVE)
 for root,dirs,names in os.walk(nativeprefix,followlinks=False):
  # Never traverse runtime junctions or generated/private trees.
  dirs[:]=[d for d in dirs if not (Path(root)/d).is_junction() and d!='__pycache__']
  for n in names:
   rel=(Path(root)/n).relative_to(Path(nativeprefix));p=NATIVE/rel
   if included(p):files[rel.as_posix()]={'sha256':sha(p),'bytes':os.stat(longpath(p)).st_size}
  if len(files) and len(files)%20000==0:print('Hashed '+str(len(files)),flush=True)
 (HERE/'target-files.json').write_text(json.dumps({'version':VERSION,'files':files},indent=2),encoding='utf8')
 print('Inventoried '+str(len(files))+' files in '+str(round(time.monotonic()-start))+' seconds',flush=True)
 return files
def deltas(files):
 template=(ROOT/'work/Setup.iss').read_text(encoding='utf-8-sig')
 preview=json.loads((ROOT/'work/teaching-projects/preview-manifest.json').read_text(encoding='utf8'))
 preview={c['path']:c['sha256'] for c in preview['files']}
 for version in BASES:
  source=ROOT/'work/release-2.3.3'/('target-files.json' if version=='2.3.3' else 'base-'+version+'.json')
  copy(source,HERE/('base-'+version+'.json'))
  base=json.loads(source.read_text(encoding='utf8'))['files']
  changes=[{'path':p,'oldSHA256':base.get(p,{}).get('sha256'),**d} for p,d in files.items() if base.get(p,{}).get('sha256')!=d['sha256']]
  manifest={'base':version,'version':VERSION,'totalBytes':sum(c['bytes'] for c in changes),'files':changes}
  (HERE/('update-manifest-'+version+'.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
  a=template.index('[Files]');b=template.index('[Icons]',a);lines=['[Files]']
  for c in changes:
   parent=Path(c['path']).parent.as_posix();dest='{app}'+('\\'+parent.replace('/','\\').replace('{','{{') if parent!='.' else '')
   lines.append(f'Source: "{NATIVE/c["path"]}"; DestDir: "{dest}"; Flags: ignoreversion')
  setup=template[:a]+'\n'.join(lines)+'\n\n'+template[b:]
  setup=setup.replace('OutputBaseFilename=AppInventor-Offline-Setup-x64','OutputBaseFilename=Yuxuan-Programming-Studio-Update-'+version+'-to-'+VERSION).replace('OutputDir=..\\outputs','OutputDir=package').replace('SetupIconFile=native\\resources\\brand.ico','SetupIconFile='+str(NATIVE/'resources/brand.ico'))
  setup=setup.replace('AppVersion='+VERSION,'AppVersion='+VERSION+'\nUninstallLogMode=append\nInfoBeforeFile='+str(HERE/'before-install.txt')).replace('Compression=lzma2/normal','Compression=lzma2/max')
  checks=[(c['path'],c['oldSHA256'],c['sha256']) for c in changes if c['oldSHA256']]
  for rel in ['AppInventor.exe','AppInventorCore.exe','runtime/python3.13.16/python.exe','mixly/arduino-cli/arduino-cli.exe']:
   if not any(c[0]==rel for c in checks):checks.append((rel,base[rel]['sha256'],files[rel]['sha256']))
  code='''
[Code]
function CheckBaseFile(const Relative, BaseHash, NewHash, PreviewHash: String): String;
var Digest: String;
begin
  Result := '';
  if not FileExists(AddBackslash(ExpandConstant('{app}')) + Relative) then begin
    Result := '基础文件缺失，请选择原安装目录：' + Relative; Exit;
  end;
  try Digest := Lowercase(GetSHA256OfFile(AddBackslash(ExpandConstant('{app}')) + Relative));
  except Result := '无法检查基础文件，请先退出软件：' + Relative; Exit; end;
  if (Digest <> BaseHash) and (Digest <> NewHash) and (Digest <> PreviewHash) then
    Result := '版本或文件不匹配，请下载与当前版本对应的更新包：' + Relative;
end;
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not FileExists(ExpandConstant('{app}\\unins000.dat')) then begin
    Result := '请先安装完整基础版，并选择原安装目录。此文件是更新包。'; Exit;
  end;
'''
  q=lambda x:x.replace("'","''")
  for rel,old,new in checks:
   allowed=preview.get(rel,'') if version=='2.3.3' else ''
   code+="  Result := CheckBaseFile('"+q(rel.replace('/','\\'))+"', '"+old+"', '"+new+"', '"+allowed+"');\n  if Result <> '' then Exit;\n"
  code+='end;\n'
  (HERE/('Update-'+version+'.iss')).write_text(setup+code,encoding='utf-8-sig')
  print(json.dumps({'base':version,'files':len(changes),'bytes':manifest['totalBytes'],'checks':len(checks)}),flush=True)
if __name__=='__main__':
 stage();deltas(inventory())
