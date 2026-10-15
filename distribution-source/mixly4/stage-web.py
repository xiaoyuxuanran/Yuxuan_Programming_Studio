"""Stage browser assets and the native bridge; keep existing user data separate."""
from pathlib import Path
import json
import shutil

HERE = Path(__file__).resolve().parent
UP = HERE / 'upstream'
NATIVE = HERE.parent / 'native'
DEST = NATIVE / 'mixly/web'
SITE = DEST / 'site'
VENDOR = SITE / 'editor'
VERSION = 'yuxuan-2.3.0-web-1'


def copytree(source, target, extra=()):
    shutil.copytree(source, target, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', '*.map', *extra))


DEST.mkdir(parents=True, exist_ok=True)
SITE.mkdir(parents=True, exist_ok=True)
VENDOR.mkdir(parents=True, exist_ok=True)
for name in ('server.py', 'cloud.py', 'compiler-paths.py', 'toolchain_paths.py', 'sdk-junction.ps1', 'UPSTREAM.json'):
    shutil.copy2(HERE / name, DEST / name)
for name in ('index.html', 'workbench.css', 'workbench.js'):
    shutil.copy2(HERE / name, SITE / name)
shutil.copy2(HERE / 'editor-theme.css', VENDOR / 'yuxuan-theme.css')
shutil.copy2(NATIVE / 'resources/brand-logo.png', SITE / 'brand-logo.jpg')
shutil.copy2(NATIVE / 'resources/brand.ico', SITE / 'brand.ico')

copytree(UP / 'common', VENDOR / 'common', ('mixly-modules-es6',))
copytree(UP / 'files', VENDOR / 'files')
copytree(UP / 'mixvm', VENDOR / 'mixvm', ('scripts', '.cursorindexingignore'))
copytree(UP / 'ai_tools', VENDOR / 'ai_tools', ('scripts',))
copytree(UP / 'boards/default', VENDOR / 'boards/default')
copytree(UP / 'boards/default_src/micropython/origin', VENDOR / 'boards/default/micropython')
shutil.copy2(UP / 'boards/index.html', VENDOR / 'boards/index.html')
for name in ('sw-config.json', 'manifest.json', 'version.json', 'mixly-static-cache-sw.js', 'index.html', 'LICENSE', 'README.txt'):
    shutil.copy2(UP / name, VENDOR / name)
boards = json.loads((UP / 'boards.json').read_text(encoding='utf-8'))
allowed = {'arduino_avr', 'arduino_esp32', 'arduino_esp8266', 'micropython_esp32'}
filtered = [b for b in boards if b['boardIndex'].split('/')[3] in allowed]
assert len(filtered) == 4
(VENDOR / 'boards.json').write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding='utf-8')
for board in allowed:
    entry = VENDOR / 'boards/default' / board
    if not (entry / 'index.xml').is_file():
        raise RuntimeError('Missing compiled hardware board: ' + board)
    config = json.loads((entry / 'config.json').read_text(encoding='utf-8'))
    # Official Mixly4 catalogs are currently empty; keep the existing usable
    # official catalogs and convert packages to the current plugin format.
    config['plugins'] = {'mixly': {'urls': ['/api/cloud/catalog?board=' + board]}}
    config.pop('lib', None)
    (entry / 'config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
for filename in (VENDOR / 'common/main.js', VENDOR / 'boards/index.html'):
    text = filename.read_text(encoding='utf-8')
    filename.write_text(text.replace('20260927-esptool-070e', VERSION), encoding='utf-8')
page = VENDOR / 'boards/index.html'
page.write_text(page.read_text(encoding='utf-8').replace('</head>', '<link rel="stylesheet" href="/editor/yuxuan-theme.css"></head>'), encoding='utf-8')

# Preserve upstream package notices together with the bundled browser build.
licenses = DEST / 'licenses'
licenses.mkdir(exist_ok=True)
for source_root, label in [(UP / 'node_modules', 'build'), (UP / 'common/modules/mixly-modules-es6/node_modules', 'core'), (UP / 'boards/default_src/python_pyodide/node_modules', 'pyodide')]:
    for package in source_root.iterdir():
        packages = list(package.iterdir()) if package.name.startswith('@') else [package]
        for actual in packages:
            if not actual.is_dir():
                continue
            key = actual.relative_to(source_root).as_posix().replace('/', '--')
            for file in actual.iterdir():
                if file.is_file() and file.name.lower().startswith(('license', 'notice', 'copying')):
                    target = licenses / label / key / file.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, target)
report = {'version': '2.3.0', 'hardwareEnvironments': sorted(allowed), 'androidAppIncluded': False,
          'files': sum(1 for f in DEST.rglob('*') if f.is_file()),
          'bytes': sum(f.stat().st_size for f in DEST.rglob('*') if f.is_file())}
(HERE / 'stage-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
