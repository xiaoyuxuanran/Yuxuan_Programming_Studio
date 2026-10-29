from pathlib import Path
import json,sys,subprocess,time,urllib.request,urllib.error,secrets,hashlib,os
H=Path(__file__).resolve().parent;root=Path(sys.argv[1]);selected=set(sys.argv[2].split(','));data=Path(sys.argv[3]);data.mkdir(parents=True,exist_ok=True)
files=json.loads((H/'target-files.json').read_text(encoding='utf8'))['files'];components=json.loads((H/'component-files.json').read_text(encoding='utf8'));count=0
for rel,d in files.items():
 required=components[rel] is None or bool(set(components[rel].split(' or '))&selected)
 p='\\\\?\\'+str(root/rel)
 assert os.path.isfile(p)==required,('Unexpected component file',rel,required)
 if required:
  with open(p,'rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d['sha256'],rel
  count+=1
subprocess.run([str(H/'ComponentProbe.exe'),str(root),','.join(sorted(selected)),str(data)],check=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
if selected&{'python','cpp'}:
 token=secrets.token_hex(32);folder=data/'studio';log=(data/'studio.log').open('wb');proc=subprocess.Popen([str(root/'runtime/python3.13.16/python.exe'),'-X','utf8',str(root/'studio/server.py'),'--data',str(folder),'--token',token],stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 api=None
 try:
  for _ in range(150):
   assert proc.poll() is None,'Studio process exited'
   if (folder/'studio-running.json').exists():break
   time.sleep(.2)
  port=json.loads((folder/'studio-running.json').read_text(encoding='utf8'))['port'];http=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  def api(route,body=None):
   req=urllib.request.Request(f'http://127.0.0.1:{port}/api/'+route,data=json.dumps(body).encode() if body is not None else None,headers={'X-Studio-Token':token,'Content-Type':'application/json'})
   with http.open(req,timeout=30) as r:return json.load(r)
  state=api('state');assert set(state['installedModes'])==selected&{'python','cpp'}
  for mode in ('python','cpp'):
   if mode not in selected:
    try:api('project/create',{'name':'ShouldBeBlocked','mode':mode});raise AssertionError('Unavailable mode allowed')
    except urllib.error.HTTPError as e:assert e.code==400
    continue
   project=next((p for p in state['projects'] if p['mode']==mode),None)
   if project is None:project=api('project/create',{'name':'Added '+mode,'mode':mode})
   for version in (['3.8.9','3.13.16'] if mode=='python' else [None]):
    body={'project':project['id'],'path':'main.py' if mode=='python' else 'main.cpp'}
    if version:body['version']=version
    jid=api('run',body)['id']
    for _ in range(600):
     job=api('job?id='+jid)
     if not job['running']:break
     time.sleep(.1)
    assert not job['running'] and job['code']==0,job
 finally:
  if api:
   try:api('shutdown',{})
   except Exception:pass
  try:proc.wait(10)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(10)
  log.close()
print('PASS selected payload hashes, excluded runtimes, installed entries, shared license runtime and selected code execution: '+','.join(sorted(selected))+' ('+str(count)+' files)',flush=True)
