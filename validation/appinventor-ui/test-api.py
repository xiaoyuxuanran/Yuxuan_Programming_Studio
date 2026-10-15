"""Live same-origin servlet regression in an isolated, already licensed workspace."""
from pathlib import Path
import hashlib
import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request

here = Path(__file__).resolve().parent
data = here / 'USB 接口验收'
base = next(line[4:] for line in (data / 'running.ini').read_text().splitlines() if line.startswith('url='))
jar = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(jar))
plain = urllib.request.build_opener(urllib.request.ProxyHandler({}))
checks = []

def request(path, body=None, headers=None, expected=200, opener=client):
    r = urllib.request.Request(base + path, data=body, headers=headers or {})
    try:
        response = opener.open(r, timeout=35)
    except urllib.error.HTTPError as response_error:
        response = response_error
    with response:
        actual, raw = response.status, response.read()
    assert actual == expected, (path, actual, raw[:250])
    return raw

request('ode/usb/devices', headers={'X-Offline-Usb':'1'}, expected=412, opener=plain)
checks.append('unauthenticated servlet blocked')
login = request('login').decode()
csrf = re.search("name='csrf' value='([^']+)'", login).group(1)
body = urllib.parse.urlencode({'username':'UsbTest2026','csrf':csrf}).encode()
index = request('login', body, {'Content-Type':'application/x-www-form-urlencoded'}).decode()
assert 'offline-usb.js' in index
checks.append('existing username entrance and USB resources')
request('ode/usb/devices', expected=403)
checks.append('missing anti-CSRF header blocked')
request('ode/usb/devices', headers={'X-Offline-Usb':'1','Origin':'https://example.invalid'}, expected=403)
checks.append('foreign Origin blocked')
device_info = json.loads(request('ode/usb/devices', headers={'X-Offline-Usb':'1'}))
assert isinstance(device_info['devices'], list)
checks.append('real ADB device enumeration through authenticated servlet')
request('ode/usb/install', b'{}', {'X-Offline-Usb':'1','Content-Type':'text/plain'}, expected=415)
checks.append('non-JSON installation blocked')
request('ode/usb/install', b'x' * 4097, {'X-Offline-Usb':'1','Content-Type':'application/json'}, expected=413)
checks.append('oversized request blocked')
request('ode/usb/install', b'{', {'X-Offline-Usb':'1','Content-Type':'application/json'}, expected=400)
checks.append('malformed JSON blocked')
request('ode/usb/install', json.dumps({'serial':'fixtureMissingPhone','downloadPath':'https://example.invalid/app.apk'}).encode(),
        {'X-Offline-Usb':'1','Content-Type':'application/json'}, expected=400)
checks.append('arbitrary APK address rejected through servlet')
request('ode/usb/install', json.dumps({'serial':'fixtureMissingPhone','downloadPath':'/ode/download/project-output/1/Android'}).encode(),
        {'X-Offline-Usb':'1','Content-Type':'application/json'}, expected=409)
checks.append('missing physical device fails without installing')
request('ode/usb/job?id=invalid', headers={'X-Offline-Usb':'1'}, expected=404)
checks.append('unknown deployment rejected')
request('ode/usb/other', headers={'X-Offline-Usb':'1'}, expected=404)
checks.append('unknown bridge route rejected')
report = {'ok':True,'passed':checks,'deviceCount':len(device_info['devices']),
          'physicalInstallationTested':False,
          'coreSha256':hashlib.sha256((here.parent/'native/AppInventorCore.exe').read_bytes()).hexdigest().upper()}
(here/'api-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
