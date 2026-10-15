import importlib.util
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / 'native/mixly/web/server.py'
sys.path.insert(0, str(SERVER.parent))
spec = importlib.util.spec_from_file_location('mixly_path_check', SERVER)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
bridge.ROOT = Path(os.environ.get('YX_PATH_ROOT', str(HERE / '编译路径 验证')))
workspace = bridge.Workspace(HERE / '编译数据 中文 空格', '3' * 64)
report = {'ok': False, 'compiles': [], 'drive': workspace.sdk_path.drive}
drive = workspace.sdk_path.drive
try:
    assert drive and str(workspace.sdk).isascii()
    for fqbn in ('arduino:avr:uno', 'esp8266:esp8266:generic', 'esp32:esp32:esp32'):
        started = time.monotonic()
        job = workspace.start_job({'fqbn': fqbn, 'code': '#include <Arduino.h>\nvoid setup(){pinMode(2,OUTPUT);}\nvoid loop(){digitalWrite(2,HIGH);delay(20);}'})
        while time.monotonic() - started < 300:
            result = workspace.job(job['id'])
            if result['state'] != 'running':
                break
            time.sleep(.3)
        report['compiles'].append({'fqbn': fqbn, 'seconds': round(time.monotonic() - started, 2), **result})
        print(fqbn, result['exitCode'], flush=True)
        assert result['state'] == 'done' and result['exitCode'] == 0, result
    report['ok'] = True
finally:
    workspace.stop()
    workspace.sdk_path.close()
    from toolchain_paths import device_target
    report['driveRemoved'] = device_target(drive) is None
    report['ok'] = report['ok'] and report['driveRemoved']
    (HERE / 'path-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    assert report['driveRemoved'], 'Fixture drive was not released'
