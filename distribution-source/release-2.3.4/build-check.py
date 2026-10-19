from pathlib import Path
import json,hashlib,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];NATIVE=ROOT/'work/native'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
target=load(HERE/'target-files.json')['files'];report={'ok':False,'deltas':[]}
assert target['server/sdk/lib/impl/appengine-api-stubs.jar']['sha256']==load(ROOT/'work/course56/storage-fix/result.json')['sha256']
for version in ['2.2.0','2.3.1','2.3.2','2.3.3']:
 base=load(HERE/('base-'+version+'.json'))['files'];m=load(HERE/('update-manifest-'+version+'.json'));changes={f['path']:f for f in m['files']}
 remaining=set(base)-set(target)
 assert all(p.startswith('mixly/web/') or p=='mixly/arduino-cli/Arduino15/inventory.yaml' for p in remaining),'Unexpected payload omissions: '+str(list(remaining)[:3])
 expected={p for p,d in target.items() if base.get(p,{}).get('sha256')!=d['sha256']};assert expected==set(changes)
 for p,c in changes.items():assert c['oldSHA256']==base.get(p,{}).get('sha256') and c['sha256']==target[p]['sha256'] and c['bytes']==target[p]['bytes']
 text=(HERE/('Update-'+version+'.iss')).read_text(encoding='utf-8-sig');files=text[text.index('[Files]'):text.index('[Icons]')];assert len(re.findall(r'^Source:',files,re.M))==len(expected)
 assert 'AppVersion=2.3.4' in text and 'UninstallLogMode=append' in text and 'unins000.dat' in text
 exe=HERE/'package'/f'Yuxuan-Programming-Studio-Update-{version}-to-2.3.4.exe';assert exe.stat().st_size>10000000
 with exe.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 report['deltas'].append({'base':version,'files':len(expected),'uncompressedBytes':m['totalBytes'],'installerBytes':exe.stat().st_size,'installerSHA256':digest})
base=load(HERE/'base-2.3.3.json')['files']
for p,d in target.items():
 if p.startswith(('mixly/','studio/','buildserver/','runtime/','license/','usb/')) and p in base:assert d==base[p],'Unexpected unrelated component change: '+p
catalog=load(NATIVE/'server/war/static/teaching/catalog.json');assert len(catalog['stages'])==8
lessons=[l for s in catalog['stages'] for l in s['lessons']];assert [l['id'] for l in lessons]==list(range(1,57))
for l in lessons:
 assert len(l['projects'])==3 and len(l['materials'])==2
 for f in l['projects']+l['materials']:assert target['server/war/'+f['url']]['sha256']==f['sha256']
for f in ['ui/teaching-ui.json','ui/final-ui.json','validation/firmware-final.json','storage-fix/result.json']:assert load(ROOT/'work/course56'/f)['passed']
report.update(ok=True,lessons=56,projects=168,materialDownloads=112,unrelatedComponentsUnchanged=True)
(HERE/'build-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
