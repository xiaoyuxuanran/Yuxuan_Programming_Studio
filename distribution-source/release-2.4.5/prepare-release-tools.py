from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'work/release-2.3.4'
s=(OLD/'publish-release.py').read_text(encoding='utf8').replace('2.3.4','2.4.5').replace('r234','r245')
a=s.index('def acceptance():');b=s.index('\ndef verify_github():',a)
s=s[:a]+'''def acceptance():
 a=json.loads((ROOT/'work/r245/install-acceptance.json').read_text(encoding='utf-8-sig'))
 assert a['ok'] and a['userStateRestored'] and a['mergedUninstallVerified'] and a['fullInstallerVerified']
 assert a['installerSHA256'].lower()==next(x['sha256'] for x in expected() if x['name']=='AppInventor-Offline-Setup-x64.exe')
 assert next(x['bytes'] for x in expected() if x['name']=='AppInventor-Offline-Setup-x64.exe')<2*1024**3
 for p in ['payload-audit.json','source-audit.json','updater-compatibility.json']:
  r=json.loads((HERE/p).read_text(encoding='utf8'));assert r.get('ok',r.get('passed')),p
''' +s[b:]
s=s.replace("def api(route):return json.loads(gh('api',route))","def api(route):return json.loads(gh('api','-H','Cache-Control: no-cache',route+('&' if '?' in route else '?')+'yx_check='+str(time.time_ns())))")
s=s.replace("def release():return next(r for r in api('repos/'+REPO+'/releases?per_page=100') if r['tag_name']==TAG)","""def release():
 for attempt in range(5):
  found=next((r for r in api('repos/'+REPO+'/releases?per_page=100') if r['tag_name']==TAG),None)
  if found:return found
  time.sleep(1)
 raise RuntimeError('Release is not visible yet')""")
s=s.replace("gh('release','edit',TAG,'--repo',REPO,'--draft=false','--latest=true');r=verify_github();assert not r['draft'] and api('repos/'+REPO+'/releases/latest')['tag_name']==TAG","gh('release','edit',TAG,'--repo',REPO,'--draft=false','--latest=true');time.sleep(2);r=verify_github();assert not r['draft'] and api('repos/'+REPO+'/releases/latest')['tag_name']==TAG")
(HERE/'publish-release.py').write_text(s,encoding='utf8')
s=(OLD/'verify-public.py').read_text(encoding='utf8').replace('2.3.4','2.4.5').replace("Yuxuan-Programming-Studio-Update-2.2.0-to-2.4.5.exe","AppInventor-Offline-Setup-x64.exe").replace('actual 2.2.0 update bytes','actual full installer bytes').replace('actual public 2.2.0 update','actual public full installer')
(HERE/'verify-public.py').write_text(s,encoding='utf8')
print('Prepared full-release publishing and anonymous verification tools')
