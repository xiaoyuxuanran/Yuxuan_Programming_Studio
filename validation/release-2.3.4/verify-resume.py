"""Verify the owned earlier candidate before resuming with the corrected final package."""
from pathlib import Path
import json,hashlib,os
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];AREA=ROOT/'work/r234';APP=AREA/'app'
def sha(p):
 with open('\\\\?\\'+str(p.absolute()),'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
old=json.loads((AREA/'install-acceptance.json').read_text(encoding='utf-8-sig'))
assert old['freshExit']==0 and old['patchExit']==0 and old['userStateRestored'] and not old['cleanupFailure'] and not old['ok']
assert old['failure']=='payload installed acceptance failed'
manifest=json.loads((HERE/'update-manifest-2.2.0.json').read_text(encoding='utf8'))
different=[]
for f in manifest['files']:
 if sha(APP/f['path'])!=f['sha256']:different.append(f['path'])
assert different==['resources/distribution-source/release-2.3.4/prepare-package.py'],different
final=HERE/'package/Yuxuan-Programming-Studio-Update-2.2.0-to-2.3.4.exe'
record={'ok':True,'installed':str(APP),'previousInstallerSHA256':old['installerSHA256'],'finalInstallerSHA256':sha(final),'launcherSHA256':sha(APP/'AppInventor.exe'),'differencesBeforeFinalUpdate':different,'original220SetupExit':old['freshExit'],'previousPatchExit':old['patchExit']}
(AREA/'verified-resume.json').write_text(json.dumps(record,indent=2),encoding='utf8');print('Owned candidate verified: only the packaging source differs; original 2.2.0 install succeeded')
