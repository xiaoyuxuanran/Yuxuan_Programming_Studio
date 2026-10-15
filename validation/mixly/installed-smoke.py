"""Acceptance against an installed copy; uses the user's existing signed device grant."""
import pathlib,sys,json,subprocess,time,urllib.request,os
root=pathlib.Path(sys.argv[1]).resolve();data=pathlib.Path(sys.argv[2]).resolve()
python=root/'runtime/python3.13.16/python.exe';results=[]
env=dict(os.environ);env.pop('PYTHONHOME',None);env.pop('PYTHONPATH',None)
def record(name,**details):
    results.append(dict(test=name,ok=True,**details));print('PASS',name,flush=True)
    (data/'installed-smoke.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
def license_check(folder):
    reply=subprocess.run([str(python),'-X','utf8',str(root/'license/gate.py'),'--state',str(folder)],input='{"action":"check","online":true}\n{"action":"exit"}\n',capture_output=True,text=True,encoding='utf-8',env=env,timeout=60)
    return json.loads(reply.stdout.splitlines()[0])
unauthorized=license_check(data/'unactivated/license')
assert not unauthorized['ok'];record('unactivated installation refuses tools')
authorized=license_check(data/'license');assert authorized['ok'];record('installed signed grant and live server validation',expires=authorized['expires'])
core=subprocess.Popen([str(root/'AppInventor.exe'),'--headless','--no-browser','--data-dir',str(data)],env=env)
try:
    deadline=time.time()+240;url=None
    while time.time()<deadline:
        if core.poll() is not None:raise AssertionError('Authorized launcher exited before App Inventor became ready')
        try:
            url=next(line[4:] for line in (data/'running.ini').read_text().splitlines() if line.startswith('url='))
            with urllib.request.urlopen(url+'login/_health',timeout=3) as response:
                assert 'AppInventorOffline/1' in response.read().decode();break
        except (OSError,StopIteration,AssertionError):time.sleep(.3)
    else:raise AssertionError('App Inventor startup timeout')
    record('authorized installed App Inventor startup',url=url)
finally:
    (data/'stop.request').write_text('',encoding='utf-8')
    try:core.wait(timeout=60)
    except subprocess.TimeoutExpired:core.kill();raise
assert core.returncode==0;record('App Inventor graceful shutdown')
studio_data=data/'studio';token='test-studio-token'
server=subprocess.Popen([str(python),'-X','utf8',str(root/'studio/server.py'),'--data',str(studio_data),'--token',token],env=env)
try:
    deadline=time.time()+30
    while time.time()<deadline:
        if server.poll() is not None:raise AssertionError('Studio startup failed')
        try:port=json.loads((studio_data/'studio-running.json').read_text())['port'];break
        except (OSError,ValueError):time.sleep(.2)
    else:raise AssertionError('Studio startup timeout')
    url='http://127.0.0.1:'+str(port)+'/api/'
    def api(action,body=None):
        request=urllib.request.Request(url+action,data=json.dumps(body).encode() if body is not None else None,headers={'X-Studio-Token':token,'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
    state=api('state');py=next(p for p in state['projects'] if p['mode']=='python');cpp=next(p for p in state['projects'] if p['mode']=='cpp')
    file=api('file?project='+py['id']+'&path=main.py')
    api('file/save',{'project':py['id'],'path':'main.py','text':'import sys\nprint(sys.version.split()[0])\nprint("installed smoke")\n','mtime':file['mtime']})
    for project,path,version in [(py,'main.py','3.8.9'),(py,'main.py','3.13.16'),(cpp,'main.cpp',None)]:
        body={'project':project['id'],'path':path}
        if version:body['version']=version
        job=api('run',body)['id'];deadline=time.time()+150
        while time.time()<deadline:
            info=api('job?id='+job)
            if not info['running']:break
            time.sleep(.2)
        else:api('stop',{'id':job});raise AssertionError('Studio run timeout')
        assert info['code']==0,info['output']
        if version:assert version in info['output'] and 'installed smoke' in info['output']
        else:assert 'Yuxuan' in info['output']
        record('installed '+(version or 'C++')+' compile/run')
finally:
    try:api('shutdown',{})
    finally:server.wait(timeout=20)
record('studio graceful shutdown')
