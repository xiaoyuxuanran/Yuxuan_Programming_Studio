"""Draft first, verify bytes, mirror supported assets, then publish and advance feeds."""
from pathlib import Path
import json,hashlib,os,sys,subprocess,runpy,time
import requests
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];PACKAGE=HERE/'package';WORKTREE=ROOT/'work/github-publish/Yuxuan_Programming_Studio'
GH=ROOT/'work/github-tools/cli/bin/gh.exe';REPO='xiaoyuxuanran/Yuxuan_Programming_Studio';TAG='v2.4.6'
ENV={**os.environ,'HTTPS_PROXY':'http://127.0.0.1:7897'};GM=runpy.run_path(str(ROOT/'work/release-2.3.1/gitee-publish.py'));GITEE=GM['PAGE']
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def gh(*args):
 r=subprocess.run([str(GH),*args],env=ENV,capture_output=True,text=True,encoding='utf8');assert r.returncode==0,r.stderr;return r.stdout
def api(route):return json.loads(gh('api','-H','Cache-Control: no-cache',route+('&' if '?' in route else '?')+'yx_check='+str(time.time_ns())))
def release():
 for attempt in range(5):
  found=next((r for r in api('repos/'+REPO+'/releases?per_page=100') if r['tag_name']==TAG),None)
  if found:return found
  time.sleep(1)
 raise RuntimeError('Release is not visible yet')
def prepare():
 mirrored=json.loads((HERE/'gitee-assets.json').read_text(encoding='utf8')) if (HERE/'gitee-assets.json').exists() else []
 mirrored={a['name']:a for a in mirrored if a.get('publicSHA256Verified')}
 assets=[]
 for p in sorted(PACKAGE.iterdir()):
  if not p.is_file() or p.name in ['update.json','SHA256SUMS.txt']:continue
  a={'name':p.name,'size':p.stat().st_size,'digest':'sha256:'+sha(p),'browser_download_url':'https://github.com/'+REPO+'/releases/download/'+TAG+'/'+p.name,'mirrors':[]}
  if p.name in mirrored:
   assert mirrored[p.name]['sha256']==a['digest'][7:]
   a['mirrors']=[GITEE+'/releases/download/'+TAG+'/'+p.name]
  assets.append(a)
 data={'schema':1,'tag_name':TAG,'draft':False,'prerelease':False,'body':(HERE/'release-notes.md').read_text(encoding='utf8'),'html_url':GITEE+'/releases/tag/'+TAG,'assets':assets}
 raw=json.dumps(data,ensure_ascii=False,indent=2)+'\n';(PACKAGE/'update.json').write_text(raw,encoding='utf8')
 names=[a['name'] for a in assets]+['update.json'];(PACKAGE/'SHA256SUMS.txt').write_text(''.join(sha(PACKAGE/n)+'  '+n+'\n' for n in names),encoding='utf8');names+=['SHA256SUMS.txt']
 (HERE/'package-manifest.json').write_text(json.dumps({'version':'2.4.6','assets':[{'name':n,'bytes':(PACKAGE/n).stat().st_size,'sha256':sha(PACKAGE/n)} for n in names]},indent=2),encoding='utf8')
 print('Prepared '+str(len(names))+' assets; '+str(len(mirrored))+' publicly verified mirrors',flush=True)
def expected():
 assets=json.loads((HERE/'package-manifest.json').read_text())['assets']
 for a in assets:assert (PACKAGE/a['name']).stat().st_size==a['bytes'] and sha(PACKAGE/a['name'])==a['sha256'],a['name']
 return assets
def acceptance():
 a=json.loads((ROOT/'work/r246f/install-acceptance.json').read_text(encoding='utf-8-sig'))
 assert a['ok'] and a['userStateRestored'] and a['mergedUninstallVerified'] and a['fullInstallerVerified']
 u=json.loads((HERE/'incremental-acceptance.json').read_text(encoding='utf-8-sig'));assert u['ok'] and u['userStateRestored'] and u['incrementalVerified']
 assert json.loads((HERE/'components-acceptance.json').read_text(encoding='utf-8-sig'))['ok']
 assert a['installerSHA256'].lower()==next(x['sha256'] for x in expected() if x['name']=='AppInventor-Offline-Setup-x64.exe')
 assert u['incrementalInstallerSHA256']==next(x['sha256'] for x in expected() if x['name']=='Yuxuan-Programming-Studio-Update-2.4.5-to-2.4.6.exe')
 assert next(x['bytes'] for x in expected() if x['name']=='AppInventor-Offline-Setup-x64.exe')<2*1024**3
 for p in ['payload-audit.json','source-audit.json','updater-compatibility.json']:
  r=json.loads((HERE/p).read_text(encoding='utf8'));assert r.get('ok',r.get('passed')),p

def verify_github():
 r=release();assets=expected();assert {x['name'] for x in assets}=={x['name'] for x in r['assets']}
 for a in assets:
  x=next(x for x in r['assets'] if x['name']==a['name']);assert x['state']=='uploaded' and x['size']==a['bytes'] and x['digest']=='sha256:'+a['sha256'],a['name']
 return r
def upload():
 acceptance();assets=expected()
 if not any(r['tag_name']==TAG for r in api('repos/'+REPO+'/releases?per_page=100')):gh('release','create',TAG,'--repo',REPO,'--verify-tag','--draft','--title','羽轩编程工作台 2.4.6','--notes-file',str(HERE/'release-notes.md'))
 r=release();assert r['draft'],'Do not replace published release assets'
 for a in assets:
  old=next((x for x in r['assets'] if x['name']==a['name']),None)
  if old and old['digest']=='sha256:'+a['sha256']:continue
  args=['release','upload',TAG,'--repo',REPO]
  if old:args+=['--clobber']
  gh(*args,str(PACKAGE/a['name']));print('Uploaded GitHub '+a['name'],flush=True)
 verify_github();print('GitHub draft asset names/sizes/digests verified',flush=True)
def public_hash(url,expected_bytes,expected_sha):
 with requests.get(url,stream=True,timeout=(20,180)) as r:
  r.raise_for_status();h=hashlib.sha256();size=0
  for chunk in r.iter_content(1024*1024):h.update(chunk);size+=len(chunk)
  assert size==expected_bytes and h.hexdigest()==expected_sha,url
def mirrors():
 acceptance();verify_github();g=GM['Gitee']();r=g.release(TAG,(HERE/'release-notes.md').read_text(encoding='utf8'));uploaded=[];skipped=[]
 for a in expected():
  if a['name'] in ['update.json','SHA256SUMS.txt']:continue
  if a['bytes']>100*1024*1024:skipped.append({'name':a['name'],'reason':'Gitee attachment size limit; canonical GitHub asset retained'});continue
  item=g.upload(r,PACKAGE/a['name']);assert item['size']==a['bytes'],a['name']
  public_hash(GITEE+'/releases/download/'+TAG+'/'+a['name'],a['bytes'],a['sha256'])
  uploaded.append({'name':a['name'],'bytes':a['bytes'],'sha256':a['sha256'],'publicSHA256Verified':True});(HERE/'gitee-assets.json').write_text(json.dumps(uploaded,ensure_ascii=False,indent=2),encoding='utf8');print('Verified public Gitee '+a['name'],flush=True)
 (HERE/'gitee-skipped.json').write_text(json.dumps(skipped,ensure_ascii=False,indent=2),encoding='utf8')
def publish():
 acceptance();r=verify_github();assert r['draft']
 g=GM['Gitee']();gr=g.release(TAG,(HERE/'release-notes.md').read_text(encoding='utf8'))
 for n in ['update.json','SHA256SUMS.txt']:
  p=PACKAGE/n;x=g.upload(gr,p);assert x['size']==p.stat().st_size;public_hash(GITEE+'/releases/download/'+TAG+'/'+n,p.stat().st_size,sha(p))
 gh('release','edit',TAG,'--repo',REPO,'--draft=false','--latest=true');time.sleep(2);r=verify_github();assert not r['draft'] and api('repos/'+REPO+'/releases/latest')['tag_name']==TAG
 (WORKTREE/'update.json').write_bytes((PACKAGE/'update.json').read_bytes())
 (HERE/'publish-result.json').write_text(json.dumps({'ok':True,'github':r['html_url'],'gitee':GITEE+'/releases/tag/'+TAG,'assets':expected()},ensure_ascii=False,indent=2),encoding='utf8');print('Published v2.4.6; advance the verified update feed now',flush=True)
if __name__=='__main__':{'prepare':prepare,'upload':upload,'mirrors':mirrors,'publish':publish}[sys.argv[1]]()
