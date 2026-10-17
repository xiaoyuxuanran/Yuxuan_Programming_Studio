from pathlib import Path
import hashlib,json,sys,os
root=Path(sys.argv[1]).resolve();target=Path(sys.argv[2]).resolve();files={}
if os.name=='nt' and not str(root).startswith('\\\\?\\'):root=Path('\\\\?\\'+str(root))
for p in root.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(root).as_posix()
    if rel.startswith('unins') or rel=='user-preserved-project.txt' or '__pycache__' in p.parts:continue
    with p.open('rb') as f:files[rel]={'sha256':hashlib.file_digest(f,'sha256').hexdigest(),'bytes':p.stat().st_size}
target.write_text(json.dumps({'version':'2.2.0','files':files},indent=2),encoding='utf-8')
print('Captured actual 2.2.0 installed baseline: '+str(len(files))+' files',flush=True)
