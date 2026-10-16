"""Prepare reproducible Mixly 4 browser sources without changing the released 2.2 package."""
from pathlib import Path
import io
import json
import re
import shutil
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
UP = HERE / 'upstream'
PIN = 'd1141e0fd73255f8705983d2252e8b049119dac1'
ESP32_PIN = '7241435d8bd50543f884e8ff9cb67956cf8e3652'
assert subprocess.check_output(['git', '-C', str(UP), 'rev-parse', 'HEAD'], text=True).strip() == PIN

# Both removed Arduino modules are available in the official preceding commit.
# Restoring the pair also preserves ESP32's shared ESP8266 sensor generators.
for ident in ('arduino_esp32', 'arduino_esp8266'):
    prefix = f'boards/default_src/{ident}/'
    archive = subprocess.check_output(['git', '-C', str(UP), 'archive', ESP32_PIN, prefix])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar:
            if not member.isfile():
                continue
            target = (UP / member.name).resolve()
            assert target.is_relative_to(UP.resolve()) and member.name.startswith(prefix)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tar.extractfile(member).read())

core = UP / 'common/modules/mixly-modules-es6'
shutil.copy2(HERE / 'arduino-shell.js', core / 'src/web/arduino-shell.js')

# Webpack 5.111 treats assignment to an imported namespace as read-only.
# Board entry points intentionally attach generators to the shared Blockly.
for entry in (UP / 'boards/default_src').glob('*/index.js'):
    source = entry.read_text(encoding='utf-8')
    if re.search(r'^Blockly\.\w+\s*=', source, re.M):
        source = source.replace("import * as Blockly from 'blockly/core';", 'const Blockly = globalThis.Blockly;')
        entry.write_text(source, encoding='utf-8')

# Keep every simulator's internal board resources, while exposing just the four
# requested physical programming environments in the workbench's own catalog.
boards = json.loads((UP / 'boards.json').read_text(encoding='utf-8'))
for ident, label, image in [('arduino_esp32', 'Arduino ESP32', 'esp32_compressed.png'), ('arduino_esp8266', 'Arduino ESP8266', 'esp8266_compressed.png')]:
    boards = [b for b in boards if ident not in b['boardIndex']]
    boards.append({'boardImg': f'./boards/default/{ident}/media/{image}', 'boardType': label, 'boardIndex': f'./boards/default/{ident}/index.xml', 'env': {'web': True, 'electron': True, 'webCompiler': False, 'webSocket': False}, 'language': 'C/C++'})
(UP / 'boards.json').write_text(json.dumps(boards, ensure_ascii=False, indent=2), encoding='utf-8')
(HERE / 'UPSTREAM.json').write_text(json.dumps({'source': 'https://gitee.com/bnu_mixly/mixly4', 'commit': PIN, 'restoredArduinoESP32Commit': ESP32_PIN, 'restoredArduinoESP8266Commit': ESP32_PIN, 'androidAppIncluded': False}, ensure_ascii=False, indent=2), encoding='utf-8')
print('Prepared Mixly 4 with both official Arduino ESP32 and ESP8266 modules restored.')
subprocess.run([__import__('sys').executable, str(HERE / 'fix-bluetooth.py')], check=True)
