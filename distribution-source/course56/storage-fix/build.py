from pathlib import Path
import shutil, subprocess, zipfile, hashlib, json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
JDK=ROOT/'work/native/runtime/java17/bin'
SDK=ROOT/'work/native/server/sdk'
JAR=SDK/'lib/impl/appengine-api-stubs.jar'
backup=HERE/'appengine-api-stubs-original.jar'
if not backup.exists():shutil.copy2(JAR,backup)
classes=HERE/'classes';classes.mkdir(exist_ok=True)
entry='com/google/appengine/api/blobstore/dev/FileBlobStorage.class'
with zipfile.ZipFile(backup) as z:(HERE/'FileBlobStorage-original.class').write_bytes(z.read(entry))
delete_entry='com/google/appengine/api/blobstore/dev/FileBlobStorage$4.class'
with zipfile.ZipFile(backup) as z:(HERE/'FileBlobStorage-delete-original.class').write_bytes(z.read(delete_entry))
api=ROOT/'work/native/server/war/WEB-INF/lib/appengine-api-1.0-sdk-2.0.19.jar'
classpath=str(SDK/'lib/impl/appengine-api-stubs.jar')+';'+str(api)
def run(*cmd):subprocess.run(list(map(str,cmd)),check=True,cwd=ROOT)
run(JDK/'javac.exe','--add-exports','java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED','-d',classes,HERE/'src/PatchBlobStorage.java')
run(JDK/'java.exe','--add-exports','java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED','-cp',classes,'PatchBlobStorage',HERE/'FileBlobStorage-original.class',HERE/'FileBlobStorage-patched.class')
run(JDK/'java.exe','--add-exports','java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED','-cp',classes,'PatchBlobStorage',HERE/'FileBlobStorage-delete-original.class',HERE/'FileBlobStorage-delete-patched.class')
run(JDK/'javac.exe','--release','11','-encoding','UTF-8','-cp',classpath,'-d',classes,HERE/'src/com/google/appengine/api/blobstore/dev/BlobFileNames.java',HERE/'src/com/google/appengine/api/blobstore/dev/StorageCheck.java')
patched=HERE/'appengine-api-stubs-patched.jar'
with zipfile.ZipFile(backup) as src, zipfile.ZipFile(patched,'w',zipfile.ZIP_DEFLATED) as out:
 for info in src.infolist():
  if info.filename.upper().startswith('META-INF/') and info.filename.upper().endswith(('.SF','.RSA','.DSA')):continue
  replacement={entry:'FileBlobStorage-patched.class',delete_entry:'FileBlobStorage-delete-patched.class'}.get(info.filename)
  out.writestr(info,(HERE/replacement).read_bytes() if replacement else src.read(info.filename))
 out.writestr('com/google/appengine/api/blobstore/dev/BlobFileNames.class',(classes/'com/google/appengine/api/blobstore/dev/BlobFileNames.class').read_bytes())
run(JDK/'java.exe','-cp',str(patched)+';'+str(api)+';'+str(classes),'com.google.appengine.api.blobstore.dev.StorageCheck',HERE/'test-data')
# Deployment is explicit, only after the owned validation service has stopped.
(HERE/'result.json').write_text(json.dumps({'passed':True,'version':2,'stressBlobs':1400,'legacyMigration':True,'deleteWithoutResurrection':True,'traversalRejection':True,'sha256':hashlib.sha256(patched.read_bytes()).hexdigest()},indent=2),encoding='utf8')
