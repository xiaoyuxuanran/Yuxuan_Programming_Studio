"""Versioned mirror publishing. Credentials stay in per-user DPAPI storage."""
from pathlib import Path
import base64, hashlib, json, os, subprocess, sys, uuid
import requests

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REPO='studentcodeone/yuxuan_-programming_-studio'
PAGE='https://gitee.com/'+REPO
GHREPO='xiaoyuxuanran/Yuxuan_Programming_Studio'
GH=ROOT/'work/github-tools/cli/bin/gh.exe'
SECRET=ROOT/'work/github-publish/gitee-release-token.dpapi.xml'

def token():
    script="$s=Import-Clixml -LiteralPath $env:YUXUAN_GITEE_SECRET; [System.Net.NetworkCredential]::new('', $s).Password"
    p=subprocess.run(['powershell','-NoProfile','-Command',script],env={**os.environ,'YUXUAN_GITEE_SECRET':str(SECRET)},capture_output=True,text=True,check=True)
    return p.stdout.strip()

class Gitee:
    def __init__(self):
        self.token=token();self.session=requests.Session()
        self.session.headers['User-Agent']='Yuxuan-Programming-Studio-Release/2.3.1'
    def api(self,path,method='GET',data=None):
        r=self.session.request(method,'https://gitee.com/api/v5/'+path,params={'access_token':self.token},json=data,timeout=(20,90))
        if r.status_code>=400:
            # Never include request URLs, which contain authentication parameters.
            raise RuntimeError('Gitee API '+str(r.status_code)+': '+r.text[:400].replace(self.token,'[redacted]'))
        return r.json() if r.content else None
    def release(self,tag,body):
        releases=self.api('repos/'+REPO+'/releases?per_page=100')
        found=next((r for r in releases if r['tag_name']==tag),None)
        fields={'name':'羽轩编程工作台 '+tag[1:],'body':body,'prerelease':False,'tag_name':tag}
        if found:return self.api('repos/'+REPO+'/releases/'+str(found['id']),'PATCH',fields)
        return self.api('repos/'+REPO+'/releases','POST',{**fields,'tag_name':tag,'target_commitish':'main'})
    def upload(self,release,path,name=None):
        path=Path(path);name=name or path.name
        existing=self.api('repos/'+REPO+'/releases/'+str(release['id'])+'/attach_files')
        # Gitee returns either the list or a paging wrapper, depending on deployment.
        items=existing if isinstance(existing,list) else existing.get('list',existing.get('data',[]))
        item=next((a for a in items if a.get('name')==name),None)
        if item:return item
        boundary='YuxuanRelease'+uuid.uuid4().hex
        head=('--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="'+name+'"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()
        tail=('\r\n--'+boundary+'--\r\n').encode()
        def chunks():
            yield head
            with path.open('rb') as f:
                while block:=f.read(1024*1024):yield block
            yield tail
        headers={'Content-Type':'multipart/form-data; boundary='+boundary,'Content-Length':str(len(head)+path.stat().st_size+len(tail))}
        class Body:
            def __iter__(self):return chunks()
            def __len__(self):return int(headers['Content-Length'])
        r=self.session.post('https://gitee.com/api/v5/repos/'+REPO+'/releases/'+str(release['id'])+'/attach_files',params={'access_token':self.token},headers=headers,data=Body(),timeout=(20,180))
        if r.status_code>=400:raise RuntimeError('Gitee upload '+str(r.status_code)+': '+r.text[:400].replace(self.token,'[redacted]'))
        print('Uploaded Gitee '+release['tag_name']+'/'+name,flush=True)
        return r.json()
    def push(self,*refs):
        auth=base64.b64encode(('studentcodeone:'+self.token).encode()).decode()
        env={**os.environ,'GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'credential.helper','GIT_CONFIG_VALUE_0':'','GIT_CONFIG_KEY_1':'http.https://gitee.com/.extraHeader','GIT_CONFIG_VALUE_1':'Authorization: Basic '+auth,'GIT_TERMINAL_PROMPT':'0'}
        p=subprocess.run(['git','push','gitee',*refs],cwd=ROOT/'work/github-publish/Yuxuan_Programming_Studio',env=env,capture_output=True,text=True)
        if p.returncode:raise RuntimeError(p.stderr.replace(self.token,'[redacted]').replace(auth,'[redacted]'))
        print(p.stderr,flush=True)

def github_release(tag):
    p=subprocess.run([str(GH),'api','repos/'+GHREPO+'/releases/tags/'+tag],env={**os.environ,'HTTPS_PROXY':'http://127.0.0.1:7897'},capture_output=True,text=True,encoding='utf-8',check=True)
    return json.loads(p.stdout)

def legacy():
    g=Gitee();report=[]
    for version in ('2.2.0','2.3.0'):
        tag='v'+version;gh=github_release(tag)
        links='\n'.join('- ['+a['name']+']('+a['browser_download_url']+')' for a in gh['assets'])
        body=gh['body']+'\n\n### 镜像下载\n\n源码与版本标签已同步至 Gitee。完整安装包保留 GitHub 下载，升级至 2.3.1 后更新优先使用 Gitee。\n\n'+links
        release=g.release(tag,body)
        folder=ROOT/('work/github-publish/release-assets-2.2' if version=='2.2.0' else 'work/github-publish/release-assets')
        candidates=[(folder/'SHA256SUMS.txt','SHA256SUMS.txt')]
        guide=ROOT/('work/release-2.2/docs/使用说明.txt' if version=='2.2.0' else 'outputs/使用说明.txt')
        candidates.append((guide,'User-Guide.txt'))
        if version=='2.2.0':candidates.append((ROOT/'work/release-2.2/package/适配源码与补丁.zip','Source-and-Patches.zip'))
        else:candidates.append((ROOT/'outputs/Mixly网页版迁移说明.md','Mixly-Migration.md'))
        assets=[]
        for path,name in candidates:
            if path.exists():assets.append(g.upload(release,path,name))
        report.append({'version':version,'id':release['id'],'url':PAGE+'/releases/tag/'+tag,'assets':assets})
    (HERE/'gitee-legacy-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Gitee legacy version pages complete',flush=True)

if __name__=='__main__':
    if sys.argv[1:]==['legacy']:legacy()
