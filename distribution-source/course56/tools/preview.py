from pathlib import Path
import json,sys,zipfile,xml.etree.ElementTree as E,base64,mimetypes
HERE=Path(__file__).resolve().parent
def tag(x):return x.tag.split('}')[-1]
def child(x,name):return next((c for c in x if tag(c)==name),None)
def ast(x):
 if x is None:return None
 d={'type':x.get('type'),'fields':{},'values':{},'statements':{}}
 for c in x:
  t=tag(c)
  if t=='field':d['fields'][c.get('name')]=c.text or ''
  elif t in ('value','statement'):
   b=child(c,'block')
   if b is None:b=child(c,'shadow')
   d['values' if t=='value' else 'statements'][c.get('name')]=ast(b)
  elif t=='mutation':d['mutation']={**c.attrib,'args':[a.get('name') for a in c if tag(a)=='arg']}
  elif t=='next':d['next']=ast(child(c,'block'))
 return d
def build(aia,out):
 with zipfile.ZipFile(aia) as z:
  scm=z.read(next(n for n in z.namelist() if n.endswith('/Screen1.scm'))).decode('utf8')
  form=json.loads(scm.split('$JSON\n',1)[1].rsplit('\n|#',1)[0])['Properties']
  xml=E.fromstring(z.read(next(n for n in z.namelist() if n.endswith('/Screen1.bky'))))
  assets={n.removeprefix('assets/'):'data:'+str(mimetypes.guess_type(n)[0] or 'application/octet-stream')+';base64,'+base64.b64encode(z.read(n)).decode() for n in z.namelist() if n.startswith('assets/') and not n.endswith('/')}
 data={'form':form,'blocks':[ast(b) for b in xml if tag(b)=='block'],'assets':assets}
 template=(HERE/'preview.template.html').read_text(encoding='utf8')
 Path(out).write_text(template.replace('__COURSE_DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')),encoding='utf8')
if __name__=='__main__':build(*sys.argv[1:3])
