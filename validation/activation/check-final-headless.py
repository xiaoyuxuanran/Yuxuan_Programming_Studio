"""Verify the final launcher with an existing grant; never activate or revoke."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

workspace = Path(__file__).resolve().parents[2]
native = workspace / 'work/native'
data = workspace / 'work/已安装版 羽轩2.1.0'
unactivated = workspace / 'work/activation/final-unactivated'
output = workspace / 'work/activation/final-headless-live.json'
sys.path.insert(0, str(native / 'license'))
sys.path.insert(0, str(native / 'license/vendor'))
from license_client import LicenseClient
from gate import URL, PRODUCT, PUBLIC_KEY

def online_time():
    # Read the DPAPI state only. Do not print device keys, identifiers or grants.
    return LicenseClient(URL, PRODUCT, PUBLIC_KEY, data / 'license').last_online

env = dict(os.environ)
env.pop('PYTHONHOME', None)
env.pop('PYTHONPATH', None)
launcher = native / 'AppInventor.exe'
denied = subprocess.run([str(launcher), '--headless', '--no-browser', '--data-dir', str(unactivated)], env=env, timeout=60)
assert denied.returncode == 4, denied.returncode
baseline = online_time()
process = subprocess.Popen([str(launcher), '--headless', '--no-browser', '--data-dir', str(data)], env=env)
try:
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        assert process.poll() is None, 'Authorized final launcher exited early'
        try:
            url = next(line[4:] for line in (data / 'running.ini').read_text().splitlines() if line.startswith('url='))
            with urllib.request.urlopen(url + 'login/_health', timeout=3) as response:
                if 'AppInventorOffline/1' in response.read().decode():
                    break
        except (OSError, StopIteration):
            pass
        time.sleep(.3)
    else:
        raise AssertionError('Final launcher startup timeout')
    first = online_time()
    assert first > baseline, 'Startup did not persist live validation'
    initial_mtime = (data / 'license/device-license.bin').stat().st_mtime_ns
    deadline = time.monotonic() + 85
    while time.monotonic() < deadline:
        assert process.poll() is None, 'Final launcher exited before its periodic validation'
        if (data / 'license/device-license.bin').stat().st_mtime_ns > initial_mtime:
            second = online_time()
            if second > first:
                break
        time.sleep(.5)
    else:
        raise AssertionError('Production periodic validation did not persist')
finally:
    (data / 'stop.request').write_text('', encoding='utf-8')
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
        raise
assert process.returncode == 0, process.returncode
report = {'ok': True, 'launcherSha256': hashlib.sha256(launcher.read_bytes()).hexdigest().upper(),
          'unactivatedExitCode': denied.returncode, 'authorizedStartup': True,
          'periodicOnlineValidation': True, 'lastOnlineAdvancedSeconds': second - first,
          'gracefulShutdownExitCode': process.returncode, 'existingGrantOnly': True}
output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False), flush=True)
