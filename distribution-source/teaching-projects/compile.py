from pathlib import Path
import os,subprocess,shutil,re,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
APP=Path('/home/yuxuan/appinventor-dev/appinventor-sources/appinventor/appengine')
env=dict(os.environ,JAVA_HOME='/usr/lib/jvm/java-17-openjdk-amd64')
env['PATH']=env['JAVA_HOME']+'/bin:'+env['PATH']
with (HERE/'gwt-build.log').open('w',encoding='utf8') as log:
 r=subprocess.run(['ant','-Dlocal.services=false','-Dlocale=en,zh_CN','-Dclient.flags=-style PRETTY -localWorkers 2','YaClientApp'],cwd=APP,env=env,stdout=log,stderr=subprocess.STDOUT)
if r.returncode:raise SystemExit('GWT build failed. See gwt-build.log')
compiled=APP/'build/war/ode';target=ROOT/'work/native/server/war/ode'
active={s for s in re.findall(r'[A-F0-9]{32}',(compiled/'ode.nocache.js').read_text()) if (compiled/(s+'.cache.js')).is_file()}
assert active
staged=[]
for f in compiled.iterdir():
 if f.is_file() and (f.name.endswith('.gwt.rpc') or f.name=='ode.nocache.js' or f.name in {s+'.cache.js' for s in active}):
  shutil.copy2(f,target/f.name);staged.append(f.name)
for s in active:
 shutil.copytree(compiled/'deferredjs'/s,target/'deferredjs'/s,dirs_exist_ok=True)
(HERE/'gwt-staging.json').write_text(json.dumps({'active':sorted(active),'files':staged},indent=2),encoding='utf8')
print('Compiled and staged teaching-project client:',sorted(active),flush=True)
