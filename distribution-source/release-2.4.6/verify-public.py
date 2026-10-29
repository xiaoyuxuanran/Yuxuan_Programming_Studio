"""Anonymous checks for public feeds, source refs and the actual full installer bytes."""
from pathlib import Path
import json,requests,subprocess,hashlib,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];G='https://gitee.com/studentcodeone/yuxuan_-programming_-studio';H='https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio';PROXY={'https':'http://127.0.0.1:7897'}
s=requests.Session();s.headers['User-Agent']='Yuxuan-Anonymous-Public-Verification/2.4.6';expected=json.loads((HERE/'package/update.json').read_text(encoding='utf8'));manifest=json.loads((HERE/'package-manifest.json').read_text())
report={'ok':False,'githubAssets':[]}
def get(url,**kw):
 r=s.get(url,timeout=(20,180),**kw);r.raise_for_status();return r
def git(*args):return subprocess.run(['git',*args],cwd=ROOT/'work/github-publish/Yuxuan_Programming_Studio',capture_output=True,text=True,check=True).stdout.strip()
try:
 cache={'yx_verify':time.time_ns()}
 assert get(G+'/raw/main/update.json',params=cache).json()==expected;report['giteeFeedMatches']=True
 assert get('https://raw.githubusercontent.com/xiaoyuxuanran/Yuxuan_Programming_Studio/main/update.json',params=cache,proxies=PROXY).json()==expected;report['githubFeedMatches']=True
 latest=get('https://api.github.com/repos/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/latest',params=cache,proxies=PROXY).json();assert latest['tag_name']=='v2.4.6' and not latest['draft']
 assert {a['name'] for a in latest['assets']}=={a['name'] for a in manifest['assets']}
 for a in manifest['assets']:
  actual=next(x for x in latest['assets'] if x['name']==a['name']);assert actual['size']==a['bytes'] and actual['digest']=='sha256:'+a['sha256'] and actual['state']=='uploaded'
  report['githubAssets'].append({'name':a['name'],'bytes':a['bytes'],'sha256':a['sha256']})
 report['githubPublicLatestVerified']=True
 mirrored=json.loads((HERE/'gitee-assets.json').read_text())
 for a in mirrored:
  assert a['publicSHA256Verified'];assert next(x for x in manifest['assets'] if x['name']==a['name'])['sha256']==a['sha256']
 for name in ['update.json','SHA256SUMS.txt']:
  p=HERE/'package'/name;r=get(G+'/releases/download/v2.4.6/'+name);assert r.content==p.read_bytes()
 report['giteeVerifiedMirrors']=len(mirrored);report['giteeNewMetadataAttachmentsVerified']=True
 main=git('rev-parse','HEAD');tag=git('rev-list','-n','1','v2.4.6')
 gmain=get(G.replace('https://gitee.com/','https://gitee.com/api/v5/repos/')+'/branches/main',params=cache).json()['commit']['sha'];assert gmain==main
 hmain=get('https://api.github.com/repos/xiaoyuxuanran/Yuxuan_Programming_Studio/branches/main',params=cache,proxies=PROXY).json()['commit']['sha'];assert hmain==main
 tags=get(G.replace('https://gitee.com/','https://gitee.com/api/v5/repos/')+'/tags',params={**cache,'per_page':100}).json()
 gtag=next(t['commit']['sha'] for t in tags if t['name']=='v2.4.6');assert gtag==tag
 htag=get('https://api.github.com/repos/xiaoyuxuanran/Yuxuan_Programming_Studio/git/ref/tags/v2.4.6',params=cache,proxies=PROXY).json()['object']
 if htag['type']=='tag':htag=get(htag['url'],proxies=PROXY).json()['object']
 assert htag['sha']==tag
 report.update(mainCommit=main,tagCommit=tag,sourceRefsVerified=True)
 a=next(x for x in manifest['assets'] if x['name']=='AppInventor-Offline-Setup-x64.exe')
 print('Downloading actual public full installer for anonymous SHA256 verification',flush=True)
 with get(H+'/releases/download/v2.4.6/'+a['name'],stream=True,proxies=PROXY) as r:
  digest=hashlib.sha256();size=0
  for chunk in r.iter_content(1024*1024):digest.update(chunk);size+=len(chunk)
  assert size==a['bytes'] and digest.hexdigest()==a['sha256']
 report['anonymousInstallerDownload']={'name':a['name'],'bytes':size,'sha256':digest.hexdigest()}
 report.update(ok=True,github=H+'/releases/tag/v2.4.6',gitee=G+'/releases/tag/v2.4.6');print('PASS public feeds, refs, release assets and actual installer download',flush=True)
finally:(HERE/'public-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
