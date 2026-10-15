"""Copy only the reviewable release sources, never local runtime/user state."""
from pathlib import Path
import shutil

work = Path(__file__).resolve().parent.parent
out = work / 'native/resources/distribution-source'
for name in ['AppInventor.cs','Setup.iss','patch-native-build.py']:
    shutil.copy2(work / name, out / name)
for source in (work / 'native-patches').iterdir():
    if source.suffix in {'.java','.patch'}:
        shutil.copy2(source, out / source.name)
target = out / 'appinventor-ui'
target.mkdir(exist_ok=True)
for source in (work / 'appinventor-ui').iterdir():
    if source.is_file() and source.suffix in {'.java','.patch','.py','.ps1','.js','.css'}:
        shutil.copy2(source, target / source.name)
target = out / 'build-speed'
target.mkdir(exist_ok=True)
for source in (work / 'build-speed').iterdir():
    if source.name in {'README.md','prepare-overlays.py','compile-overlays.py','prepare-seeds.py',
                       'benchmark.py','validate-seeds.py','SeedValidation.java',
                       'dex-seed-manifest.json','resource-seed-manifest.json'}:
        shutil.copy2(source, target / source.name)
for name in ['index.jsp','WEB-INF/web.xml']:
    source = work / 'native/server/war' / name
    shutil.copy2(source, out / Path(name).name)
print('Synchronized scoped UI, core, setup and build optimization sources.')
