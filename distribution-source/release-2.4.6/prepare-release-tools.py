from pathlib import Path
import shutil
R=Path.cwd();H=R/'work/release-2.4.6';O=R/'work/release-2.4.5';P=R/'work/github-publish/Yuxuan_Programming_Studio'
s=(O/'publish-release.py').read_text(encoding='utf8').replace('2.4.5','2.4.6').replace('r245','r246')
s=s.replace("assert a['ok'] and a['userStateRestored'] and a['mergedUninstallVerified'] and a['fullInstallerVerified']", "assert a['ok'] and a['userStateRestored'] and a['mergedUninstallVerified'] and a['fullInstallerVerified'] and a['incrementalVerified']\n assert json.loads((HERE/'components-acceptance.json').read_text(encoding='utf8'))['ok']")
(H/'publish-release.py').write_text(s,encoding='utf8')
s=(O/'verify-public.py').read_text(encoding='utf8').replace('2.4.5','2.4.6');(H/'verify-public.py').write_text(s,encoding='utf8')
s=(O/'finalize.py').read_text(encoding='utf8').replace('2.4.5','2.4.6').replace('r245','r246');(H/'finalize.py').write_text(s,encoding='utf8')
s=(O/'prepare-github.py').read_text(encoding='utf8');s=s[s.index('def bundle():'):s.index("if __name__")];s=s.replace('2.4.5','2.4.6').replace('r245','r246');s=s.replace("v.mkdir(exist_ok=True)","v.mkdir(exist_ok=True)")
header='''from pathlib import Path
import json,shutil,re,zipfile,runpy,hashlib,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];REPO=ROOT/'work/github-publish/Yuxuan_Programming_Studio'
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
'''
(H/'bundle-source.py').write_text(header+s+'\nbundle()\n',encoding='utf8')
print('Prepared publication and source audit helpers')
