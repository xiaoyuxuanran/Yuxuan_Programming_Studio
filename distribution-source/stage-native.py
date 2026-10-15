from pathlib import Path
import shutil

root=Path('/home/yuxuan/appinventor-dev')
src=root/'appinventor-sources/appinventor'
out=Path('/mnt/c/Users/Yuxuan/Documents/Codex/2026-10-02/files-pasted-by-the-user-ap/work/native')
out.mkdir(parents=True,exist_ok=True)
shutil.copytree(src/'appengine/build/war',out/'server/war',dirs_exist_ok=True,ignore=shutil.ignore_patterns('appengine-generated','authkey','keystore'))
shutil.copytree(src/'buildserver/build/run/lib',out/'buildserver/lib',dirs_exist_ok=True)
shutil.copytree(root/'tools/buildserver-loopback/classes',out/'buildserver/classes',dirs_exist_ok=True)
shutil.copytree(root/'tools/google_appengine_java_delta/google/appengine/tools/java',out/'server/sdk',dirs_exist_ok=True)
(out/'resources').mkdir(exist_ok=True)
shutil.copy2(src/'lib/keyczar/KeyczarTool.jar',out/'resources/KeyczarTool.jar')
shutil.copy2(root/'appinventor-sources/LICENSE',out/'resources/AppInventor-LICENSE.txt')
print('Copied runtime artifacts only; source remains in Linux filesystem.')
