"""Loopback-only desktop code workspace. All tools live beside this application."""
from __future__ import annotations
import argparse, ast, codecs, contextlib, hashlib, importlib, json, mimetypes, os
import re, secrets, shutil, subprocess, sys, threading, time, traceback, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from runtime_support import seed_environment, https_context, ca_bundle

ROOT = Path(__file__).resolve().parent.parent
VERSIONS = {'3.8.9': ROOT/'runtime/python3.8.9/python.exe', '3.13.16': ROOT/'runtime/python3.13.16/python.exe'}
INDEX = 'https://pypi.tuna.tsinghua.edu.cn/simple'
MAX_OUTPUT = 4*1024*1024
PY_SAMPLE = 'import sys\n\nprint("你好，羽轩 Python 工作室！")\nprint("Python 版本：", sys.version.split()[0])\n\nfor i in range(1, 4):\n    print(f"第 {i} 次运行")\n'
CPP_SAMPLE = '#include <iostream>\n\nint main() {\n    std::cout << "Hello, Yuxuan C++ Studio!" << std::endl;\n    for (int i = 1; i <= 3; ++i) {\n        std::cout << "Run " << i << std::endl;\n    }\n    return 0;\n}\n'
GUI_SAMPLES = {
    'tkinter_demo.py': 'import tkinter as tk\n\nroot = tk.Tk()\nroot.title("羽轩 · Tkinter")\nroot.geometry("480x300")\nroot.configure(bg="#eaf6ff")\ntk.Label(root, text="你好，Tkinter！", font=("Microsoft YaHei", 22), bg="#eaf6ff", fg="#1583cf").pack(pady=55)\ntk.Button(root, text="点击打招呼", command=lambda: print("Hello from Tkinter!")).pack()\nroot.mainloop()\n',
    'turtle_demo.py': 'import turtle\n\nwindow = turtle.Screen()\nwindow.title("羽轩 · Turtle")\nwindow.bgcolor("#f0f8ff")\npen = turtle.Turtle()\npen.color("#1583cf")\npen.pensize(3)\npen.speed(6)\nfor i in range(36):\n    pen.circle(80)\n    pen.right(10)\nprint("绘图完成，关闭图形窗口结束运行。")\nturtle.done()\n',
    'pygame_demo.py': 'import pygame\n\npygame.init()\nscreen = pygame.display.set_mode((640, 400))\npygame.display.set_caption("羽轩 · Pygame")\nclock = pygame.time.Clock()\nrunning = True\nx = 80\nwhile running:\n    for event in pygame.event.get():\n        if event.type == pygame.QUIT:\n            running = False\n    screen.fill((234, 246, 255))\n    pygame.draw.circle(screen, (21, 131, 207), (int(x), 200), 35)\n    x = (x + 2) % 640\n    pygame.display.flip()\n    clock.tick(60)\npygame.quit()\nprint("Pygame 窗口已关闭。")\n'
}
LOCK = threading.RLock()
JOBS: dict[str, 'Job'] = {}
ENV_LOCKS: dict[str, threading.Lock] = {}
STATE: dict = {}
DATA: Path
TOKEN: str
HTTP: ThreadingHTTPServer

def save_state():
    target=DATA/'studio.json'; temp=target.with_suffix('.tmp')
    temp.write_text(json.dumps(STATE,ensure_ascii=False,indent=2),encoding='utf-8'); temp.replace(target)

def project(pid):
    with LOCK:
        p=next((x for x in STATE['projects'] if x['id']==pid),None)
        if not p: raise ValueError('项目不存在')
        return dict(p)

def location(p, rel='', allow_root=False):
    root=Path(p['path']).resolve(); rel=str(rel)
    if any(c in rel for c in '\x00:*?"<>|'): raise ValueError('文件名包含无效字符')
    path=(root/rel).resolve()
    if not path.is_relative_to(root) or (path==root and not allow_root): raise ValueError('文件必须在当前项目内')
    if any(x.startswith('.studio-') or x in {'.git','.venv','__pycache__'} for x in path.relative_to(root).parts): raise ValueError('此目录由工作区管理')
    if any(re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..*)?',x,re.I) or x.endswith((' ','.')) for x in path.relative_to(root).parts): raise ValueError('请使用有效的 Windows 文件名')
    return path

def add_project(name, mode, existing=None):
    if mode not in {'python','cpp'}: raise ValueError('不支持的语言')
    if not name or len(name)>60 or any(c in name for c in '/\\:*?"<>|') or name in {'.','..'}: raise ValueError('项目名称无效')
    path=Path(existing).expanduser().resolve() if existing else (DATA/'projects'/name).resolve()
    if not existing and not path.is_relative_to((DATA/'projects').resolve()): raise ValueError('项目路径无效')
    if existing and not path.is_dir(): raise ValueError('文件夹不存在')
    with LOCK:
        duplicate=next((p for p in STATE['projects'] if Path(p['path']).resolve()==path),None)
        if duplicate:return dict(duplicate)
        if not existing:
            path.mkdir(parents=True,exist_ok=False)
            (path/('main.py' if mode=='python' else 'main.cpp')).write_text(PY_SAMPLE if mode=='python' else CPP_SAMPLE,encoding='utf-8')
            if mode=='python':
                examples=path/'图形示例';examples.mkdir()
                for filename,source in GUI_SAMPLES.items():(examples/filename).write_text(source,encoding='utf-8')
        p={'id':secrets.token_hex(8),'name':name,'path':str(path),'mode':mode,'python':'3.13.16'}
        STATE['projects'].append(p);save_state();return p

def tree(p):
    root=Path(p['path']).resolve(); count=0
    def scan(folder,depth):
        nonlocal count
        result=[]
        if depth>8:return result
        for f in sorted(folder.iterdir(),key=lambda f:(not f.is_dir(),f.name.lower())):
            if f.is_symlink() or f.name.startswith('.studio-') or f.name in {'.git','.venv','__pycache__','node_modules'}:continue
            count+=1
            if count>3000:break
            node={'name':f.name,'path':f.relative_to(root).as_posix(),'folder':f.is_dir()}
            if f.is_dir():node['children']=scan(f,depth+1)
            result.append(node)
        return result
    return scan(root,0)

class Job:
    def __init__(self, title, worker):
        self.id=secrets.token_hex(12);self.title=title;self.output='';self.running=True
        self.code=None;self.process=None;self.cancelled=False;self.truncated=False
        self.lock=threading.RLock();self.started=time.time()
        with LOCK:
            # Retain completed logs without unbounded growth.
            for jid in list(JOBS)[:-30]:
                if not JOBS[jid].running:del JOBS[jid]
            JOBS[self.id]=self
        def execute():
            try:self.code=worker(self)
            except Exception as e:self.write('\n'+str(e)+'\n');self.code=1
            finally:self.running=False;self.process=None
        threading.Thread(target=execute,daemon=True).start()
    def write(self,text):
        with self.lock:
            if len(self.output)<MAX_OUTPUT:self.output+=text[:MAX_OUTPUT-len(self.output)]
            elif not self.truncated:self.output+='\n[输出已达到 4 MB，上方输出停止记录；可停止程序。]\n';self.truncated=True
    def stop(self):
        self.cancelled=True
        with self.lock:proc=self.process
        if proc and proc.poll() is None:
            subprocess.run(['taskkill.exe','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
    def command(self,args,cwd,env=None,interactive=False):
        if self.cancelled:return -1
        proc=subprocess.Popen([str(x) for x in args],cwd=cwd,env=env,stdin=subprocess.PIPE if interactive else subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        with self.lock:self.process=proc
        if self.cancelled:self.stop()
        decoder=codecs.getincrementaldecoder('utf-8')('replace')
        while True:
            chunk=os.read(proc.stdout.fileno(),4096)
            if not chunk:break
            self.write(decoder.decode(chunk))
        self.write(decoder.decode(b'',final=True));code=proc.wait()
        with self.lock:self.process=None
        return code

def environment(p, version, job):
    if version not in VERSIONS:raise ValueError('Python 版本无效')
    base=VERSIONS[version];target=DATA/'environments'/p['id']/version
    with LOCK:guard=ENV_LOCKS.setdefault(str(target),threading.Lock())
    with guard:
        exe=target/'Scripts/python.exe';marker=target/'studio-runtime.txt'
        expected=str(base.resolve())+'|gui-2'
        if not exe.is_file() or not marker.exists() or marker.read_text(encoding='utf-8')!=expected:
            job.write(f'正在准备 Python {version} 项目环境…\n')
            # Repoint a moved installation without deleting the user's packages.
            old=marker.read_text(encoding='utf-8') if marker.is_file() else ''
            if not exe.is_file() or not old.startswith(str(base.resolve())+'|'):
                code=job.command([base,'-X','utf8','-m','venv','--without-pip',target],DATA,process_env(base))
                if code:raise ValueError('无法创建 Python 项目环境')
            # All wheels already ship with the installer. Avoid ensurepip's
            # subprocesses and expensive pip dependency scans/bytecode generation.
            seed_environment(ROOT,target,version)
            marker.write_text(expected,encoding='utf-8')
        return exe

def process_env(exe=None):
    env=dict(os.environ)
    for key in ['PYTHONHOME','PYTHONPATH','PIP_CONFIG_FILE','PIP_EXTRA_INDEX_URL','PIP_INDEX_URL']:
        env.pop(key,None)
    env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONUNBUFFERED='1',PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_CONFIG_FILE=os.devnull,PIP_INDEX_URL=INDEX)
    # WinINET's implicit HTTPS proxy is usually an HTTP CONNECT endpoint.
    # Preserve explicitly configured proxy environment variables.
    if not any(k.lower()=='https_proxy' for k in env):
        proxy=urllib.request.getproxies().get('https','')
        if proxy.startswith(('https://127.0.0.1:','https://localhost:')):
            proxy='http://'+proxy[len('https://'):]
        if proxy:env['HTTPS_PROXY']=proxy
    if exe:env['PATH']=str(Path(exe).parent)+os.pathsep+env.get('PATH','')
    return env

def package_env(exe):
    env=process_env(exe)
    bundle=str(ca_bundle(DATA))
    for name in ['PIP_CERT','REQUESTS_CA_BUNDLE','SSL_CERT_FILE']:
        if not env.get(name):env[name]=bundle
    return env

def run(p, rel, version, arguments):
    file=location(p,rel)
    if not file.is_file():raise ValueError('请先保存并选择代码文件')
    args=arguments if isinstance(arguments,list) else []
    if len(args)>100 or any(not isinstance(x,str) or len(x)>4096 for x in args):raise ValueError('运行参数无效')
    def work(job):
        if file.suffix.lower()=='.py':
            exe=environment(p,version,job)
            job.write(f'▶ Python {version} · {rel}\n\n')
            return job.command([exe,'-X','utf8','-u',file,*args],p['path'],process_env(exe),True)
        if file.suffix.lower() not in {'.cpp','.cc','.cxx'}:raise ValueError('运行支持 .py、.cpp、.cc 和 .cxx 文件')
        compiler=ROOT/'runtime/llvm-mingw/bin/clang++.exe'
        folder=DATA/'build'/p['id']/job.id;folder.mkdir(parents=True,exist_ok=True)
        prepared=folder/'source.ii'
        env=process_env();env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','')
        flags=['-std=c++17','-O0','-Wall','-Wextra','-fdiagnostics-color=never','-finput-charset=UTF-8']
        try:
            # Preprocess on every Run. This sees changed system/project headers,
            # newly created __has_include targets and volatile compiler macros.
            # Compile that exact snapshot to avoid races with external editors.
            code=job.command([compiler,*flags,'-E','-I',p['path'],file,'-o',prepared],p['path'],env)
            if code or job.cancelled:return code
            # Clang 23 prints UTF-8 filename bytes as octal in #line markers,
            # then rejects those escapes when reading C++ preprocessed output.
            # Keep string literals (including __FILE__) intact; normalize only
            # non-ASCII bytes inside line-marker filenames back to UTF-8.
            raw=prepared.read_bytes()
            def line_path(match):
                name=re.sub(rb'\\\\|\\([0-7]{3})',lambda byte:bytes([int(byte[1],8)]) if byte[1] is not None and int(byte[1],8)>=128 else byte[0],match[2])
                return match[1]+name+match[3]
            normalized=re.sub(rb'^(#[ \t]+[0-9]+[ \t]+")((?:\\.|[^"\\\r\n])*)(")',line_path,raw,flags=re.M)
            if normalized!=raw:prepared.write_bytes(normalized)
            digest=hashlib.sha256(normalized)
            for tool in [compiler,compiler.parent/'ld.lld.exe']:
                stat=tool.stat();digest.update((str(tool.resolve())+'|'+str(stat.st_size)+'|'+str(stat.st_mtime_ns)).encode())
            digest.update(json.dumps(flags).encode());digest.update(str(Path(p['path']).resolve()).encode())
            cache=DATA/'build'/p['id']/'cache'/digest.hexdigest();output=cache/'program.exe';record=cache/'build.json'
            with LOCK:guard=ENV_LOCKS.setdefault('cpp:'+str(cache),threading.Lock())
            with guard:
                build=None
                if output.is_file() and record.is_file():
                    with contextlib.suppress(OSError,ValueError,KeyError):
                        candidate=json.loads(record.read_text(encoding='utf-8'))
                        if hashlib.sha256(output.read_bytes()).hexdigest()==candidate['sha256']:build=candidate
                if build is None:
                    job.write(f'正在编译 {rel}…\n');cache.mkdir(parents=True,exist_ok=True)
                    temporary=folder/'program.exe';start=len(job.output)
                    code=job.command([compiler,*flags,'-x','c++-cpp-output',prepared,'-o',temporary],p['path'],env)
                    if code or job.cancelled:return code
                    temporary.replace(output)
                    record.write_text(json.dumps({'diagnostics':job.output[start:],'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}),encoding='utf-8')
                else:
                    job.write('代码和依赖未变化，使用已编译程序。\n'+build.get('diagnostics',''))
            job.write('\n▶ 运行 C++ 程序\n\n');return job.command([output,*args],p['path'],env,True)
        finally:
            with contextlib.suppress(OSError):prepared.unlink()
            with contextlib.suppress(OSError):folder.rmdir()
    return Job('运行 '+rel,work)

def package_job(p,version,package):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*(?:==[A-Za-z0-9._+-]+)?',package):raise ValueError('请输入库名称或名称==版本，例如 requests 或 numpy==1.24.4')
    def install(job):
        exe=environment(p,version,job)
        job.write(f'清华源 · Python {version} · 安装 {package}\n\n')
        return job.command([exe,'-m','pip','install','--index-url',INDEX,'--no-input',package],p['path'],package_env(exe))
    return Job('安装 '+package,install)

def complete(source,line,column):
    keywords=['print','input','len','range','enumerate','zip','list','dict','set','tuple','str','int','float','bool','open','sum','min','max','sorted','reversed','isinstance','Exception','ValueError','super','any','all','abs','round','map','filter']
    names=set(keywords)
    try:
        parsed=ast.parse(source)
        for node in ast.walk(parsed):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):names.add(node.name)
            elif isinstance(node,ast.Name):names.add(node.id)
            elif isinstance(node,ast.alias):names.add(node.asname or node.name.split('.')[0])
    except SyntaxError:pass
    prefix=(source.splitlines()+[''])[max(0,line-1)][:max(0,column-1)] if line<=len(source.splitlines())+1 else ''
    dotted=re.search(r'\b([A-Za-z_]\w*)\.[A-Za-z_]*$',prefix)
    if dotted and dotted.group(1) in {'math','json','os','sys','random','re','statistics','itertools','collections','pathlib','datetime','string'}:
        module=importlib.import_module(dotted.group(1));names={x for x in dir(module) if not x.startswith('_')}
    return sorted(names)[:500]

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def response(self,status,value):
        raw=json.dumps(value,ensure_ascii=False).encode('utf-8');self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
    def authorized(self):
        origin=self.headers.get('Origin')
        return secrets.compare_digest(self.headers.get('X-Studio-Token',''),TOKEN) and (not origin or origin==f'http://127.0.0.1:{HTTP.server_port}')
    def do_GET(self):
        url=urllib.parse.urlsplit(self.path);q={k:v[0] for k,v in urllib.parse.parse_qs(url.query).items()}
        if url.path=='/health':self.response(200,{'app':'YuxuanStudio','ready':True});return
        if url.path.startswith('/api/'):
            if not self.authorized():self.response(403,{'error':'请从启动器打开工作区'});return
            try:
                if url.path=='/api/state':
                    with LOCK:result={**STATE,'versions':list(VERSIONS),'pipIndex':INDEX}
                elif url.path=='/api/tree':result=tree(project(q['project']))
                elif url.path=='/api/file':
                    path=location(project(q['project']),q['path'])
                    if path.stat().st_size>2*1024*1024:raise ValueError('文件超过 2 MB，请使用外部工具打开')
                    result={'text':path.read_text(encoding='utf-8-sig'),'mtime':str(path.stat().st_mtime_ns)}
                elif url.path=='/api/job':
                    with LOCK:job=JOBS[q['id']]
                    with job.lock:result={'output':job.output[max(0,int(q.get('cursor','0'))):],'cursor':len(job.output),'running':job.running,'code':job.code,'title':job.title,'elapsed':round(time.time()-job.started,1)}
                elif url.path=='/api/package':
                    name=q.get('name','').strip()
                    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,120}',name):raise ValueError('请输入第三方库名称，例如 requests、numpy')
                    request=urllib.request.Request('https://pypi.org/pypi/'+urllib.parse.quote(name)+'/json',headers={'User-Agent':'YuxuanStudio/2.0'})
                    with urllib.request.urlopen(request,timeout=15,context=https_context()) as response:meta=json.load(response)['info']
                    result={'name':meta['name'],'version':meta['version'],'summary':meta['summary'],'requiresPython':meta.get('requires_python') or ''}
                else:self.response(404,{'error':'接口不存在'});return
                self.response(200,result)
            except urllib.error.HTTPError as e:self.response(400,{'error':'没有找到此第三方库' if e.code==404 else '库信息获取失败'})
            except Exception as e:self.response(400,{'error':str(e)})
            return
        rel='index.html' if url.path=='/' else urllib.parse.unquote(url.path).lstrip('/')
        static=(ROOT/'studio'/rel).resolve()
        if not static.is_relative_to((ROOT/'studio').resolve()) or not static.is_file() or static.suffix in {'.py','.pyc','.ps1'} or '/pip-wheels/' in str(static).replace('\\','/'):
            self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(static)[0] or 'application/octet-stream')
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-cache');self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; worker-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        try:
            with static.open('rb') as file:shutil.copyfileobj(file,self.wfile)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_POST(self):
        if not self.authorized():self.response(403,{'error':'工作区请求被拒绝'});return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<1 or length>3*1024*1024:raise ValueError('请求大小无效')
            body=json.loads(self.rfile.read(length));url=urllib.parse.urlsplit(self.path).path
            if url=='/api/project/create':result=add_project(body['name'],body['mode'])
            elif url=='/api/project/open':
                folder=Path(body['path']);result=add_project(folder.name,body['mode'],folder)
            elif url=='/api/preferences':
                with LOCK:
                    if body.get('theme') in {'light','dark'}:STATE['theme']=body['theme']
                    save_state();result={'ok':True}
            elif url=='/api/version':
                if body['version'] not in VERSIONS:raise ValueError('Python 版本无效')
                with LOCK:
                    for p in STATE['projects']:
                        if p['id']==body['project']:p['python']=body['version']
                    save_state();result={'ok':True}
            elif url in {'/api/file/save','/api/file/create','/api/folder/create','/api/file/rename','/api/file/trash'}:
                p=project(body['project']);path=location(p,body['path'])
                if url=='/api/file/save':
                    if path.exists() and 'mtime' in body:
                        actual=path.stat().st_mtime_ns;expected=body['mtime']
                        matches=actual==int(expected) if isinstance(expected,str) else float(actual)==float(expected)
                        if not matches:raise ValueError('文件已被其他程序修改，请重新打开后保存')
                    path.parent.mkdir(parents=True,exist_ok=True);text=body['text']
                    if not isinstance(text,str) or len(text)>2*1024*1024:raise ValueError('文件太大')
                    temp=path.with_name(path.name+'.studio-tmp');temp.write_text(text,encoding='utf-8');temp.replace(path)
                    result={'mtime':str(path.stat().st_mtime_ns)}
                elif url=='/api/file/create':
                    if path.exists():raise ValueError('文件已存在')
                    path.parent.mkdir(parents=True,exist_ok=True);path.write_text('',encoding='utf-8');result={'ok':True}
                elif url=='/api/folder/create':path.mkdir(parents=True,exist_ok=False);result={'ok':True}
                elif url=='/api/file/rename':
                    target=location(p,body['to'])
                    if target.exists():raise ValueError('目标名称已存在')
                    target.parent.mkdir(parents=True,exist_ok=True);path.rename(target);result={'ok':True}
                else:
                    trash=Path(p['path'])/'.studio-trash';trash.mkdir(exist_ok=True);target=trash/(str(time.time_ns())+'-'+path.name);path.rename(target);result={'ok':True,'trash':str(target)}
            elif url=='/api/run':
                with LOCK:
                    if sum(j.running for j in JOBS.values())>=4:raise ValueError('请先停止或等待其他运行任务')
                p=project(body['project']);job=run(p,body['path'],body.get('version',p['python']),body.get('args',[]));result={'id':job.id}
            elif url=='/api/package/install':
                with LOCK:
                    if sum(j.running for j in JOBS.values())>=4:raise ValueError('请先停止或等待其他运行任务')
                p=project(body['project']);job=package_job(p,body.get('version',p['python']),body['package']);result={'id':job.id}
            elif url=='/api/stop':JOBS[body['id']].stop();result={'ok':True}
            elif url=='/api/input':
                job=JOBS[body['id']]
                with job.lock:
                    if not job.process or not job.process.stdin or job.process.poll() is not None:raise ValueError('当前没有等待输入的程序')
                    job.process.stdin.write((str(body['text'])+'\n').encode('utf-8'));job.process.stdin.flush()
                result={'ok':True}
            elif url=='/api/complete':result=complete(body.get('source','')[:200000],int(body['line']),int(body['column']))
            elif url=='/api/shutdown':
                self.response(200,{'ok':True})
                threading.Thread(target=HTTP.shutdown,daemon=True).start();return
            else:self.response(404,{'error':'接口不存在'});return
            self.response(200,result)
        except Exception as e:self.response(400,{'error':str(e)})

def main():
    global DATA,TOKEN,STATE,HTTP
    parser=argparse.ArgumentParser();parser.add_argument('--data',required=True);parser.add_argument('--port',type=int,default=0);parser.add_argument('--token',required=True)
    args=parser.parse_args();DATA=Path(args.data).resolve();DATA.mkdir(parents=True,exist_ok=True);TOKEN=args.token
    file=DATA/'studio.json'
    STATE=json.loads(file.read_text(encoding='utf-8-sig')) if file.exists() else {'theme':'light','projects':[]}
    if not STATE['projects']:
        add_project('Python 入门','python');add_project('C++ 入门','cpp')
    HTTP=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);HTTP.daemon_threads=True
    (DATA/'studio-running.json').write_text(json.dumps({'port':HTTP.server_port,'pid':os.getpid()}),encoding='utf-8')
    print(f'YuxuanStudio http://127.0.0.1:{HTTP.server_port}',flush=True)
    try:HTTP.serve_forever(poll_interval=.25)
    finally:
        for job in list(JOBS.values()):
            if job.running:job.stop()
        HTTP.server_close()
        with contextlib.suppress(OSError):(DATA/'studio-running.json').unlink()

if __name__=='__main__':main()
