from pathlib import Path
import subprocess,os,time,json,shutil,urllib.request,contextlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];NATIVE=ROOT/'work/native'
data=HERE/'data';ai=data/'ai';mix=data/'mixly'
ai.mkdir(parents=True,exist_ok=True);mix.mkdir(exist_ok=True)
source=Path(os.environ['LOCALAPPDATA'])/'AppInventorOffline/license/device-license.bin'
if not source.exists():source=ROOT/'work/release-2.3/数据 羽轩2.3/license/device-license.bin'
assert source.exists(),'Existing activated same-user grant required; no activation will be performed.'
(ai/'license').mkdir(exist_ok=True);shutil.copy2(source,ai/'license/device-license.bin')
stop=HERE/'stop-services.request';stop.unlink(missing_ok=True)
processes=[]
try:
    for command,name in [([str(NATIVE/'AppInventor.exe'),'--headless','--no-browser','--data-dir',str(ai)],'ai'),([str(NATIVE/'runtime/python3.13.16/python.exe'),'-X','utf8',str(NATIVE/'mixly/web/server.py'),'--data',str(mix),'--token','1'*64],'mixly')]:
        log=(HERE/(name+'-service.log')).open('wb')
        p=subprocess.Popen(command,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
        processes.append((p,name,log))
    deadline=time.monotonic()+260
    while time.monotonic()<deadline:
        for p,n,_ in processes:assert p.poll() is None,(n,p.returncode)
        if (ai/'running.ini').exists() and (mix/'mixly-running.json').exists():
            config=dict(l.split('=',1) for l in (ai/'running.ini').read_text(encoding='utf-8-sig').splitlines())
            try:
                with urllib.request.urlopen(config['url']+'login/_health',timeout=2) as r:assert r.status==200
                break
            except Exception:pass
        time.sleep(.5)
    else:raise RuntimeError('Services not ready')
    ports=json.loads((mix/'mixly-running.json').read_text())
    info={'ai':config['url'],'mixly':'http://127.0.0.1:'+str(ports['port'])+'/', 'token':'1'*64,'pids':{n:p.pid for p,n,_ in processes}}
    (HERE/'services.json').write_text(json.dumps(info),encoding='utf-8');print(json.dumps(info),flush=True)
    while not stop.exists():
        for p,n,_ in processes:assert p.poll() is None,(n,p.returncode)
        time.sleep(.5)
finally:
    if (mix/'mixly-running.json').exists():
        info=json.loads((mix/'mixly-running.json').read_text())
        with contextlib.suppress(Exception):
            urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:'+str(info['port'])+'/api/shutdown',data=b'{}',headers={'X-Suite-Token':'1'*64,'Content-Type':'application/json'}),timeout=5).close()
    for p,n,log in processes:
        deadline=time.monotonic()+90
        while p.poll() is None and time.monotonic()<deadline:
            if n=='ai':(ai/'stop.request').write_text('')
            with contextlib.suppress(subprocess.TimeoutExpired):p.wait(timeout=1)
        if p.poll() is None:subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True)
        log.close()
