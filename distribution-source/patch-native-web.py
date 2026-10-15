from pathlib import Path
import difflib
root=Path('/home/yuxuan/appinventor-dev/appinventor-sources/appinventor/appengine/src/com/google/appinventor/server/project/youngandroid')
out=Path('/mnt/c/Users/Yuxuan/Documents/Codex/2026-10-02/files-pasted-by-the-user-ap/work/native-patches')
path=root/'YoungAndroidProjectService.java'
before=path.read_text()
old='return "localhost:8888";'
new='return StringUtils.isNullOrEmpty(appengineHost.get()) ? "localhost:8888" : appengineHost.get();'
assert before.count(old)==1
after=before.replace(old,new)
(out/path.name).write_text(after)
(out/'local-callback-port.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=path.name,tofile=path.name)))
print('Prepared single-class configurable local callback overlay')
