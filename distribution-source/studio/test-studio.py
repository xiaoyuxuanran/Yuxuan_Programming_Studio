"""End-to-end checks against the bundled local workspace and real toolchains."""
import json, time, urllib.request, urllib.error, sys
from pathlib import Path
DATA=Path(sys.argv[1]);PORT=json.loads((DATA/'studio-running.json').read_text())['port']
URL=f'http://127.0.0.1:{PORT}/api/';results=[]
def api(path,body=None,token='test-studio-token'):
    req=urllib.request.Request(URL+path,data=json.dumps(body).encode() if body is not None else None,headers={'X-Studio-Token':token,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
def check(name,condition):
    if not condition:raise AssertionError(name)
    results.append(name);print('PASS',name,flush=True)
def denied(path,body=None,token='test-studio-token'):
    try:api(path,body,token)
    except urllib.error.HTTPError as e:return e.code in {400,403}
    return False
def job(body,route='run',input_text=None,stop=False):
    jid=api(route,body)['id'];deadline=time.time()+150;sent=False
    while time.time()<deadline:
        info=api('job?id='+jid)
        if input_text and not sent and 'READY' in info['output']:api('input',{'id':jid,'text':input_text});sent=True
        if stop and 'READY' in info['output']:api('stop',{'id':jid});stop=False
        if not info['running']:
            (DATA/('job-'+jid+'.json')).write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
            return info
        time.sleep(.2)
    api('stop',{'id':jid});raise AssertionError('job timeout')
state=api('state');py=next(p for p in state['projects'] if p['mode']=='python');cpp=next(p for p in state['projects'] if p['mode']=='cpp')
check('unauthorized API blocked',denied('state',token='wrong'))
check('path escape blocked',denied('file/create',{'project':py['id'],'path':'../escaped.py'}))
check('reserved path blocked',denied('file/create',{'project':py['id'],'path':'CON.py'}))
for version in ['3.8.9','3.13.16']:
    info=job({'project':py['id'],'path':'main.py','version':version})
    check('Python '+version+' real execution under Chinese/space path',info['code']==0 and version in info['output'] and '你好' in info['output'])
api('file/create',{'project':py['id'],'path':'输入测试.py'})
file=api('file?project='+py['id']+'&path='+urllib.parse.quote('输入测试.py'))
api('file/save',{'project':py['id'],'path':'输入测试.py','text':'print("READY", flush=True)\nprint("INPUT=" + input())\n','mtime':file['mtime']})
info=job({'project':py['id'],'path':'输入测试.py'},input_text='hello123')
check('interactive Python input',info['code']==0 and 'INPUT=hello123' in info['output'])
api('file/save',{'project':py['id'],'path':'输入测试.py','text':'import time\nprint("READY", flush=True)\ntime.sleep(120)\n'})
info=job({'project':py['id'],'path':'输入测试.py'},stop=True)
check('stop running program',info['code']!=0)
info=job({'project':cpp['id'],'path':'main.cpp'})
check('C++ real compile and run',info['code']==0 and 'Hello, Yuxuan' in info['output'])
api('file/create',{'project':cpp['id'],'path':'输入.cpp'})
api('file/save',{'project':cpp['id'],'path':'输入.cpp','text':'#include <iostream>\n#include <string>\nint main(){std::string s;std::cout<<"READY"<<std::endl;std::getline(std::cin,s);std::cout<<"INPUT="<<s<<std::endl;}\n'})
info=job({'project':cpp['id'],'path':'输入.cpp'},input_text='Cpp123')
check('interactive C++ input',info['code']==0 and 'INPUT=Cpp123' in info['output'])
api('file/save',{'project':cpp['id'],'path':'输入.cpp','text':'int main(){ syntax error; }'})
info=job({'project':cpp['id'],'path':'输入.cpp'})
check('C++ compile failure does not run stale executable',info['code']!=0 and 'error:' in info['output'] and '▶ 运行' not in info['output'])
check('Python member completion', 'sqrt' in api('complete',{'source':'import math\nmath.','line':2,'column':6}))
api('preferences',{'theme':'dark'});api('version',{'project':py['id'],'version':'3.8.9'})
check('preferences persisted',json.loads((DATA/'studio.json').read_text(encoding='utf-8'))['theme']=='dark')
api('preferences',{'theme':'light'})
meta=api('package?name=colorama');check('third-party library search',meta['name'].lower()=='colorama')
info=job({'project':py['id'],'version':'3.8.9','package':'colorama==0.4.6'},'package/install')
check('Tsinghua pip installation on Python 3.8.9',info['code']==0 and 'Successfully installed' in info['output'])
api('file/create',{'project':py['id'],'path':'依赖.py'});api('file/save',{'project':py['id'],'path':'依赖.py','text':'import colorama\nprint(colorama.__version__)\n'})
info=job({'project':py['id'],'path':'依赖.py','version':'3.8.9'});check('installed package import',info['code']==0 and '0.4.6' in info['output'])
info=job({'project':py['id'],'path':'依赖.py','version':'3.13.16'});check('version environments isolated',info['code']!=0 and 'ModuleNotFoundError' in info['output'])
info=job({'project':py['id'],'version':'3.13.16','package':'colorama==0.4.6'},'package/install');check('Tsinghua pip installation on Python 3.13.16',info['code']==0)
info=job({'project':py['id'],'path':'依赖.py','version':'3.13.16'});check('Python 3.13 installed package import',info['code']==0 and '0.4.6' in info['output'])
api('file/rename',{'project':py['id'],'path':'依赖.py','to':'sub/renamed.py'})
check('rename retains content',api('file?project='+py['id']+'&path=sub/renamed.py')['text'].startswith('import colorama'))
trash=api('file/trash',{'project':py['id'],'path':'sub/renamed.py'})
check('recoverable file removal',Path(trash['trash']).is_file())
(DATA/'acceptance.json').write_text(json.dumps({'passed':results},ensure_ascii=False,indent=2),encoding='utf-8')
print('ALL',len(results),'CHECKS PASSED',flush=True)
