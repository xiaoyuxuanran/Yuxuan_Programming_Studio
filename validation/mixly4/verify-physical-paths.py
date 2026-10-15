"""Check that GCC physically installed under Chinese names uses its mapped prefix."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'native/mixly/arduino-cli'
FIXTURE = HERE / '实体工具链 中文'
SDK = FIXTURE / 'mixly/arduino-cli'
SDK.mkdir(parents=True, exist_ok=True)

def junction(alias, target):
    alias.parent.mkdir(parents=True, exist_ok=True)
    if alias.exists():
        assert alias.is_junction() and alias.resolve() == target.resolve(), alias
        return
    subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                    'New-Item -ItemType Junction -Path $env:YX_ALIAS -Target $env:YX_TARGET | Out-Null'],
                   env={**os.environ, 'YX_ALIAS': str(alias), 'YX_TARGET': str(target)},
                   check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

shutil.copy2(SOURCE / 'arduino-cli.exe', SDK / 'arduino-cli.exe')
junction(SDK / 'libraries', SOURCE / 'libraries')
for package in (SOURCE / 'Arduino15/packages').iterdir():
    if package.is_dir() and package.name != 'esp8266':
        relative = package.relative_to(SOURCE)
        cached = SDK / relative
        if package.name == 'builtin' and cached.is_dir() and not cached.is_junction():
            continue  # An earlier fixture run may have initialized discovery tools.
        junction(cached, package)
for metadata in (SOURCE / 'Arduino15').iterdir():
    if metadata.is_file():
        shutil.copy2(metadata, SDK / metadata.relative_to(SOURCE))
relative = Path('Arduino15/packages/esp8266/hardware')
junction(SDK / relative, SOURCE / relative)
for tool in (SOURCE / 'Arduino15/packages/esp8266/tools').iterdir():
    target = SDK / tool.relative_to(SOURCE)
    if tool.name == 'xtensa-lx106-elf-gcc':
        assert not target.is_junction()
        shutil.copytree('\\\\?\\' + str(tool), '\\\\?\\' + str(target), dirs_exist_ok=True)
    else:
        junction(target, tool)
result = subprocess.run([sys.executable, '-X', 'utf8', str(HERE / 'verify-paths.py')],
                        env={**os.environ, 'YX_PATH_ROOT': str(FIXTURE)},
                        creationflags=subprocess.CREATE_NO_WINDOW)
assert result.returncode == 0
report = json.loads((HERE / 'path-verification.json').read_text(encoding='utf-8'))
report['physicalESP8266Toolchain'] = True
(HERE / 'physical-path-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('PASS physical Chinese SDK prefix and drive cleanup')
