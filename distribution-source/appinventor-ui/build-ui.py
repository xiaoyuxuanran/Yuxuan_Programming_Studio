"""Apply the narrow desktop client overlay to the existing checkout and compile GWT."""
from pathlib import Path
import difflib
import os
import re
import shutil
import subprocess
import sys

here = Path(__file__).resolve().parent
repo = Path('/home/yuxuan/appinventor-dev/appinventor-sources')
app = repo / 'appinventor/appengine'
client = app / 'src/com/google/appinventor/client'
native = here.parent / 'native'

def edit(relative, transform):
    path = client / relative
    before = subprocess.check_output(['git', 'show', 'HEAD:appinventor/appengine/src/com/google/appinventor/client/' + relative], cwd=repo).decode()
    after = transform(before)
    path.write_text(after)
    (here / Path(relative).name).write_text(after)
    (here / (Path(relative).name + '.patch')).write_text(''.join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True), fromfile=relative, tofile=relative)))

def toolbar(text):
    needle = '    bindUI();'
    assert text.count(needle) == 1
    return text.replace(needle, needle + '\n    com.google.appinventor.client.actions.OfflineUsbAction.register();')

def download(text):
    start = text.index('      // The Android App Bundle should only be used')
    end = text.index('      // OK button', start)
    return text[:start] + '''      // Desktop APK export keeps a local download only; USB testing has its own Run action.
      contentPanel.add(container);

''' + text[end:]

edit('TopToolbar.java', toolbar)
edit('explorer/commands/ShowBarcodeCommand.java', download)
edit('explorer/commands/WaitForBuildResultCommand.java', lambda t: t.replace(
    'WAIT_INTERVAL_MILLIS = 10000;', 'WAIT_INTERVAL_MILLIS = 1000;'))
edit('explorer/commands/ShowProgressBarCommand.java', lambda t: t.replace(
    'MESSAGES.waitingForBarcode()', 'MESSAGES.preparingFinalPackage()'))
shutil.copy2(here / 'OfflineUsbAction.java', client / 'actions/OfflineUsbAction.java')
env = dict(os.environ, JAVA_HOME='/usr/lib/jvm/java-17-openjdk-amd64')
env['PATH'] = env['JAVA_HOME'] + '/bin:' + env['PATH']
if '--prepare-only' not in sys.argv:
    if '--stage-only' not in sys.argv:
        subprocess.run(['ant', '-Dlocal.services=false', '-Dlocale=en,zh_CN',
                        '-Dclient.flags=-style PRETTY -localWorkers 2', 'YaClientApp'],
                       cwd=app, env=env, check=True)
    compiled = app / 'build/war/ode'
    target = native / 'server/war/ode'
    active = {value for value in re.findall(r'[A-F0-9]{32}', (compiled / 'ode.nocache.js').read_text())
              if (compiled / (value + '.cache.js')).is_file()}
    assert active, 'No active GWT permutation found'
    # Keep only the current generated client, including its code-splitting fragments.
    # Other module assets, translations and server RPC policies are retained.
    for file in target.glob('*.cache.js'):
        if file.stem.split('.')[0] not in active:
            assert file.resolve().is_relative_to(target.resolve())
            file.unlink()
    for folder in (target / 'deferredjs').iterdir():
        if folder.is_dir() and folder.name not in active:
            assert folder.resolve().is_relative_to((target / 'deferredjs').resolve())
            shutil.rmtree(folder)
    for file in compiled.iterdir():
        if file.is_file() and (file.name.endswith('.gwt.rpc') or file.name == 'ode.nocache.js'
                               or file.name in {name + '.cache.js' for name in active}):
            shutil.copy2(file, target / file.name)
    for name in active:
        shutil.copytree(compiled / 'deferredjs' / name, target / 'deferredjs' / name, dirs_exist_ok=True)
    print('Updated GWT client; other WAR resources and local adapters retained.')
