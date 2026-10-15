"""Start an isolated workspace, run existing API/GUI acceptance, stop that server."""
from pathlib import Path
import json
import subprocess
import sys
import time
import urllib.request

root = Path(__file__).resolve().parents[1] / 'native'
data = Path(sys.argv[1]).resolve()
if data.exists():
    raise SystemExit('Choose a fresh test data folder')
exe = root / 'runtime/python3.13.16/python.exe'
process = subprocess.Popen([str(exe), '-X', 'utf8', str(root / 'studio/server.py'), '--data', str(data), '--token', 'test-studio-token'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=0x08000000)
try:
    deadline = time.monotonic() + 15
    while not (data / 'studio-running.json').is_file() and time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(process.stdout.read().decode('utf-8', 'replace'))
        time.sleep(.05)
    if not (data / 'studio-running.json').is_file():
        raise RuntimeError('workspace startup timeout')
    for name in ['test-studio.py', 'test-graphics.py']:
        result = subprocess.run([str(exe), '-X', 'utf8', str(Path(__file__).parent / name), str(data)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=0x08000000)
        print(result.stdout.decode('utf-8', 'replace'), end='', flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
finally:
    if (data / 'studio-running.json').is_file():
        port = json.loads((data / 'studio-running.json').read_text())['port']
        request = urllib.request.Request('http://127.0.0.1:' + str(port) + '/api/shutdown', data=b'{}', headers={'X-Studio-Token': 'test-studio-token', 'Content-Type': 'application/json'})
        try:
            urllib.request.urlopen(request, timeout=5).close()
        except Exception:
            pass
    try:
        process.wait(10)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(5)
