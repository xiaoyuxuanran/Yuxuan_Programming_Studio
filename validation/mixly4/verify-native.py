"""Exercise the staged HTTP bridge using isolated test projects and a fixture token."""
import http.client
import json
from pathlib import Path
import time
import urllib.request
import urllib.error

HERE = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8768'
TOKEN = '1' * 64
report = {'security': [], 'compiles': [], 'catalogs': {}}

def request(path, body=None, headers=None):
    headers = {'X-Suite-Token': TOKEN, **(headers or {})}
    if body is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)

def check(name, path, body, headers, expected):
    status, value = request(path, body, headers)
    assert status == expected, (name, status, value)
    report['security'].append({'name': name, 'status': status})

try:
    check('unauthenticated API', '/api/ports', None, {'X-Suite-Token': ''}, 403)
    check('invalid session', '/api/session', {'token': 'bad'}, {}, 403)
    check('cross-origin mutation', '/api/serial/close', {}, {'Origin': 'https://example.com'}, 403)
    check('invalid Host', '/api/ports', None, {'Host': 'example.com'}, 403)
    check('unsupported board', '/api/arduino', {'fqbn': 'bad:bad:bad', 'code': ''}, {}, 400)
    check('path traversal source', '/api/arduino', {'fqbn': 'arduino:avr:uno', 'code': '', 'files': {'../bad.h': ''}}, {}, 400)
    check('unconnected upload port', '/api/arduino', {'fqbn': 'arduino:avr:uno', 'code': '', 'upload': True, 'port': 'COM9999'}, {}, 400)
    check('invalid serial port', '/api/serial/open', {'port': 'COM9999', 'baud': 115200}, {}, 400)
    for board in ('arduino_avr', 'arduino_esp32', 'arduino_esp8266', 'micropython_esp32'):
        status, catalog = request('/api/cloud/catalog?board=' + board)
        assert status == 200 and isinstance(catalog, list) and catalog, (board, status, catalog)
        report['catalogs'][board] = len(catalog)
    for fqbn in ('arduino:avr:uno', 'esp8266:esp8266:generic', 'esp32:esp32:esp32'):
        start = time.monotonic()
        status, job = request('/api/arduino', {'fqbn': fqbn, 'code': '#include <Arduino.h>\nvoid setup(){pinMode(2,OUTPUT);}\nvoid loop(){digitalWrite(2,HIGH);delay(50);digitalWrite(2,LOW);delay(50);}'})
        assert status == 202, (status, job)
        while time.monotonic() - start < 900:
            status, result = request('/api/jobs/' + job['id'])
            if result['state'] != 'running':
                break
            time.sleep(1)
        entry = {'fqbn': fqbn, 'seconds': round(time.monotonic() - start, 2), **result}
        report['compiles'].append(entry)
        (HERE / 'native-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(fqbn, result['exitCode'], entry['seconds'], flush=True)
        assert result['state'] == 'done' and result['exitCode'] == 0, result
    report['ok'] = True
finally:
    (HERE / 'native-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
