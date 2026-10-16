from pathlib import Path
import shutil,re
HERE=Path(__file__).resolve().parent
native=HERE.parent/'native'
compiled=Path('/home/yuxuan/appinventor-dev/appinventor-sources/appinventor/appengine/build/war/ode')
dest=native/'server/war/ode'
active={v for v in re.findall(r'[A-F0-9]{32}',(compiled/'ode.nocache.js').read_text()) if (compiled/(v+'.cache.js')).is_file()}
assert active
for file in compiled.iterdir():
    if file.is_file() and (file.name.endswith('.gwt.rpc') or file.name in ('ode.nocache.js','aiblockly-0.nocache.js') or file.name in {v+'.cache.js' for v in active}):
        shutil.copy2(file,dest/file.name)
for v in active:shutil.copytree(compiled/'deferredjs'/v,dest/'deferredjs'/v,dirs_exist_ok=True)
shutil.copy2(Path('/home/yuxuan/appinventor-dev/appinventor-sources/appinventor/build/blocklyeditor/blockly-all.js'),dest/'aiblockly-0.nocache.js')
assert 'yuxuan-block-selector' in (dest/'aiblockly-0.nocache.js').read_text()
print('Staged GWT client and Blockly; active permutations:',sorted(active))
