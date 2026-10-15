"""Developer-only fake device to verify long serial streams without physical hardware."""
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
TARGET = HERE.parent / 'native/mixly/web/server.py'
sys.path.insert(0, str(TARGET.parent))
spec = importlib.util.spec_from_file_location('mixly_bridge_fixture', TARGET)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

class FakeSerial:
    def __init__(self, *args, **kwargs):
        self.is_open = True
        self.wave = 0
        self.buffer = b''
        self.next_wave = time.monotonic() + .8

    @property
    def in_waiting(self):
        return len(self.buffer)

    def read(self, size):
        if not self.buffer and self.wave < 3 and time.monotonic() >= self.next_wave:
            self.wave += 1
            self.buffer = (('温度😀\n' * 70000) + f'WAVE{self.wave} END😀\n12345\n').encode('utf-8')
            self.next_wave = time.monotonic() + 2
        output, self.buffer = self.buffer[:size], self.buffer[size:]
        if not output:
            time.sleep(.02)
        return output

    def close(self):
        self.is_open = False

    def write(self, data):
        return len(data)

bridge.serial.Serial = FakeSerial
bridge.Workspace.ports = staticmethod(lambda: [{'device': 'COM42', 'description': 'Simulated serial stream', 'vid': None, 'pid': None}])
app = bridge.Workspace(HERE / 'serial-fixture-data', '2' * 64)
server = bridge.LocalHTTPServer(('127.0.0.1', 0), bridge.Handler)
server.workspace = app
(HERE / 'serial-fixture.json').write_text(json.dumps({'port': server.server_port}), encoding='utf-8')
try:
    server.serve_forever(poll_interval=.1)
finally:
    app.stop()
    server.server_close()
