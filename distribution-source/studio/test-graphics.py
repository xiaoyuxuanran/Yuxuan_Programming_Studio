import json,sys,time,urllib.request
from pathlib import Path
DATA=Path(sys.argv[1]);port=json.loads((DATA/'studio-running.json').read_text())['port'];url=f'http://127.0.0.1:{port}/api/'
def api(path,body=None):
    request=urllib.request.Request(url+path,data=json.dumps(body).encode() if body is not None else None,headers={'X-Studio-Token':'test-studio-token','Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=20) as r:return json.load(r)
p=next(p for p in api('state')['projects'] if p['mode']=='python');results=[]
for version in ['3.8.9','3.13.16']:
    sources={
        'tkinter':f'import tkinter as tk\nroot=tk.Tk()\nroot.title("验收 Tkinter {version}")\nroot.geometry("440x280")\nroot.configure(bg="#eaf6ff")\ntk.Label(root,text="羽轩 · Tkinter {version}",font=("Microsoft YaHei",18),bg="#eaf6ff",fg="#1583cf").pack(pady=75)\nroot.update()\nprint("GUI_VISIBLE",root.winfo_viewable(),flush=True)\nroot.after(8000,root.destroy)\nroot.mainloop()\n',
        'turtle':f'import turtle\ns=turtle.Screen()\ns.title("验收 Turtle {version}")\ns.setup(440,280)\ns.bgcolor("#eaf6ff")\nt=turtle.Turtle()\nt.color("#1583cf")\nt.pensize(4)\nt.speed(0)\nfor i in range(5):\n    t.forward(110)\n    t.right(144)\ns.update()\nprint("GUI_VISIBLE",s.getcanvas().winfo_viewable(),flush=True)\ns.ontimer(turtle.bye,8000)\nturtle.done()\n',
        'pygame':f'import pygame\npygame.init()\ns=pygame.display.set_mode((440,280))\npygame.display.set_caption("验收 Pygame {version}")\ns.fill((234,246,255))\npygame.draw.circle(s,(21,131,207),(220,140),70)\npygame.display.flip()\nprint("GUI_VISIBLE",int(pygame.display.get_init()),flush=True)\nstart=pygame.time.get_ticks()\nwhile pygame.time.get_ticks()-start<8000:\n    pygame.event.pump()\n    pygame.time.wait(20)\npygame.quit()\n'
    }
    for library,source in sources.items():
        name=library+'-'+version+'.py';api('file/create',{'project':p['id'],'path':name});api('file/save',{'project':p['id'],'path':name,'text':source})
        jid=api('run',{'project':p['id'],'path':name,'version':version})['id'];deadline=time.time()+120
        while time.time()<deadline:
            info=api('job?id='+jid)
            if not info['running']:break
            time.sleep(.25)
        (DATA/(name+'.result.json')).write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
        if info['running'] or info['code']!=0 or 'GUI_VISIBLE 1' not in info['output']:raise AssertionError(library+' '+version+': '+info['output'])
        label=library+' '+version+' native GUI';results.append(label);print('PASS',label,flush=True)
(DATA/'graphics-acceptance.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('ALL SIX GRAPHICS CHECKS PASSED',flush=True)
