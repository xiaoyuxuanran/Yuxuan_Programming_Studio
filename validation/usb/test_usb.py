"""Hardware-independent USB bridge tests; never install onto a real phone."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile
import threading
import time
import unittest
from unittest import mock
import urllib.error
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WORK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('yuxuan_usb', WORK / 'native/usb/server.py')
usb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(usb)


def compiled_manifest(package='appinventor.ai_test.UsbTest', activity='.Screen1'):
    values = ['manifest', 'application', 'activity', 'intent-filter', 'action', 'category',
              'package', 'name', package, activity, 'android.intent.action.MAIN',
              'android.intent.category.LAUNCHER', 'http://schemas.android.com/apk/res/android']
    offsets, payload = [], bytearray()
    for item in values:
        encoded = item.encode('utf-8')
        offsets.append(len(payload))
        payload.extend(bytes([len(item), len(encoded)]) + encoded + b'\0')
    payload.extend(b'\0' * (-len(payload) % 4))
    pool = struct.pack('<HHIIIIII', 1, 28, 28 + len(values) * 4 + len(payload), len(values), 0, 0x100, 28 + len(values) * 4, 0)
    pool += struct.pack('<' + 'I' * len(offsets), *offsets) + payload
    def start(name, attributes=()):
        body = struct.pack('<IIHHHHHH', 0xffffffff, values.index(name), 20, 20, len(attributes), 0, 0, 0)
        for key, value, android in attributes:
            body += struct.pack('<IIIHBBI', 12 if android else 0xffffffff, values.index(key), values.index(value), 8, 0, 3, values.index(value))
        return struct.pack('<HHIII', 0x102, 16, 16 + len(body), 1, 0xffffffff) + body
    def end(name):
        return struct.pack('<HHIIIII', 0x103, 16, 24, 1, 0xffffffff, 0xffffffff, values.index(name))
    nodes = start('manifest', [('package', package, False)]) + start('application')
    nodes += start('activity', [('name', activity, True)]) + start('intent-filter')
    nodes += start('action', [('name', values[10], True)]) + end('action')
    nodes += start('category', [('name', values[11], True)]) + end('category')
    nodes += end('intent-filter') + end('activity') + end('application') + end('manifest')
    return struct.pack('<HHI', 3, 8, 8 + len(pool) + len(nodes)) + pool + nodes


class FakeAdb:
    def __init__(self, state='device', install_failure='', old_logcat=False, launch_failure=False):
        self.state, self.install_failure = state, install_failure
        self.calls = []
        self.old_logcat, self.launch_failure = old_logcat, launch_failure

    def __call__(self, args, timeout=15):
        self.calls.append(list(args))
        if args == ['devices', '-l']:
            return 'List of devices attached\nUSB012 %s model:Test_Phone transport_id:1\n' % self.state
        if args[2] == 'install':
            if self.install_failure:
                raise usb.BridgeError(self.install_failure, 502)
            return 'Performing Streamed Install\nSuccess'
        if args[2:5] == ['shell', 'am', 'start']:
            return 'Error: activity not found' if self.launch_failure else 'Starting: Intent\nStatus: ok\nTotalTime: 120'
        if args[2:4] == ['shell', 'pidof']:
            return '151'
        if args[2] == 'logcat':
            if self.old_logcat and any(arg.startswith('--pid=') for arg in args):
                raise usb.BridgeError('logcat: unknown option --pid', 502)
            return '10-04 12:00:00.000  151  152 I UsbTest: app log\n10-04 12:00:00.000  999  999 I Other: private log' if self.old_logcat else '10-04 12:00:00.000  151  152 I UsbTest: app log'
        raise AssertionError(args)


class UsbTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='yuxuan-usb-')
        self.data = Path(self.directory.name) / '带空格 数据目录'
        self.fixture = Path(self.directory.name) / 'fixture.apk'
        with zipfile.ZipFile(self.fixture, 'w') as package:
            package.writestr('AndroidManifest.xml', compiled_manifest())
        self.adb = FakeAdb()
        self.bridge = usb.Bridge(self.data, 8888, self.adb, self.fetch)

    def tearDown(self):
        self.directory.cleanup()

    def fetch(self, path, cookie, target):
        self.assertEqual(path, '/ode/download/project-output/123/Android')
        shutil.copyfile(self.fixture, target)

    def wait(self, job):
        limit = time.monotonic() + 4
        while job.state == 'running' and time.monotonic() < limit:
            time.sleep(0.01)
        self.assertNotEqual(job.state, 'running')
        return job.snapshot()

    def test_real_appinventor_apk_manifest(self):
        real = WORK.parent / 'outputs/HelloOfflineTest-Windows.apk'
        self.assertTrue(real.is_file())
        package, activity = usb.apk_identity(real)
        self.assertEqual(package, 'appinventor.ai_native_test.HelloOfflineTest')
        self.assertEqual(activity, package + '.Screen1')

    def test_relative_launcher_resolved_and_shell_names_rejected(self):
        self.assertEqual(usb.apk_identity(self.fixture), ('appinventor.ai_test.UsbTest', 'appinventor.ai_test.UsbTest.Screen1'))
        for name in ('x;rm', 'x/Screen1', 'x $(touch)', 'x\nother'):
            with self.assertRaises(ValueError):
                usb.manifest_identity(compiled_manifest(name))

    def test_only_usb_devices_and_states_retained(self):
        result = usb.parse_devices('List of devices attached\nUSB1 device model:Pixel_8 usb:1\nUSB2 unauthorized\nUSB3 offline\nemulator-5554 device\n192.0.2.1:5555 device\nadb-ABC._adb-tls-connect._tcp device')
        self.assertEqual([item['serial'] for item in result], ['USB1', 'USB2', 'USB3'])
        self.assertEqual(result[0]['model'], 'Pixel 8')
        self.assertEqual(result[1]['state'], 'unauthorized')

    def test_adb_uses_localhost_default_so_first_use_can_start_daemon(self):
        result = type('Result', (), {'returncode': 0, 'stdout': 'List of devices attached'})()
        with mock.patch.object(usb.subprocess, 'run', return_value=result) as command:
            self.assertEqual(self.bridge.command(['devices', '-l'], 20), result.stdout)
        argv = command.call_args.args[0]
        self.assertEqual(argv, [str(self.bridge.adb), '-P', '5037', 'devices', '-l'])
        self.assertNotIn('-H', argv)
        self.assertNotIn('-a', argv)

    def test_loopback_download_path_rejects_ssrf_and_traversal(self):
        for path in ('http://evil.test/a.apk', '//evil/a.apk', '/ode/download/project-output/../Android',
                     '/ode/download/project-output/123/Android?redirect=evil',
                     '/ode/download/project-output/123/Android#x', '/ode/download/project-output/123/Android/extra',
                     '/ode/download/project-output/%31/Android', '/ode/download/file/123/secret', '/ode/download/project-output/-1/Android',
                     '/ode/download/project-output/123/android'):
            with self.assertRaises(usb.BridgeError):
                self.bridge.start('USB012', path)
        self.assertEqual(self.adb.calls, [])

    def test_install_launch_and_bound_app_logs(self):
        result = self.wait(self.bridge.start('USB012', '/ode/download/project-output/123/Android'))
        self.assertEqual(result['state'], 'done')
        install = next(call for call in self.adb.calls if call[2:3] == ['install'])
        self.assertEqual(install[:4], ['-s', 'USB012', 'install', '-r'])
        self.assertTrue(Path(install[-1]).is_relative_to(self.data))
        self.assertFalse(Path(install[-1]).exists())
        launch = next(call for call in self.adb.calls if call[2:5] == ['shell', 'am', 'start'])
        self.assertEqual(launch[-1], 'appinventor.ai_test.UsbTest/appinventor.ai_test.UsbTest.Screen1')
        logs = self.bridge.logcat('USB012', result['package'])
        self.assertIn('app log', logs['output'])
        with self.assertRaises(usb.BridgeError):
            self.bridge.logcat('USB012', 'other.app')

    def test_unauthorized_offline_and_disconnected_block_install(self):
        for state in ('unauthorized', 'offline', 'recovery', 'missing'):
            self.adb.state = state
            with self.assertRaises(usb.BridgeError):
                self.bridge.start('USB012', '/ode/download/project-output/123/Android')
        self.assertFalse(any(call[2:3] == ['install'] for call in self.adb.calls))

    def test_bad_apk_never_reaches_adb_install(self):
        self.fixture.write_bytes(b'not an APK')
        result = self.wait(self.bridge.start('USB012', '/ode/download/project-output/123/Android'))
        self.assertEqual(result['state'], 'failed')
        self.assertIn('有效的 Android APK', result['output'])
        self.assertFalse(any(call[2:3] == ['install'] for call in self.adb.calls))

    def test_failed_install_can_retry_without_automatic_uninstall(self):
        self.adb.install_failure = 'INSTALL_FAILED_UPDATE_INCOMPATIBLE'
        failed = self.wait(self.bridge.start('USB012', '/ode/download/project-output/123/Android'))
        self.assertEqual(failed['state'], 'failed')
        self.assertIn('备份', failed['output'])
        self.assertFalse(any('uninstall' in call for call in self.adb.calls))
        self.adb.install_failure = ''
        retried = self.wait(self.bridge.start('USB012', '/ode/download/project-output/123/Android'))
        self.assertEqual(retried['state'], 'done')

    def test_launch_error_still_allows_app_logs(self):
        self.adb.launch_failure = True
        result = self.wait(self.bridge.start('USB012', '/ode/download/project-output/123/Android'))
        self.assertEqual(result['state'], 'failed')
        self.assertIn('app log', self.bridge.logcat('USB012', result['package'])['output'])

    def test_old_android_logcat_filters_other_applications(self):
        self.adb.old_logcat = True
        result = self.wait(self.bridge.start('USB012', '/ode/download/project-output/123/Android'))
        text = self.bridge.logcat('USB012', result['package'])['output']
        self.assertIn('app log', text)
        self.assertNotIn('private log', text)

    def test_device_busy_prevents_overlapping_install(self):
        entered, finish = threading.Event(), threading.Event()
        def held_fetch(path, cookie, target):
            entered.set()
            finish.wait(3)
            self.fetch(path, cookie, target)
        self.bridge.fetcher = held_fetch
        job = self.bridge.start('USB012', '/ode/download/project-output/123/Android')
        entered.wait(1)
        with self.assertRaises(usb.BridgeError) as raised:
            self.bridge.start('USB012', '/ode/download/project-output/123/Android')
        self.assertEqual(raised.exception.status, 409)
        finish.set()
        self.wait(job)

    def test_completed_history_eviction_allows_more_than_64_runs_and_keeps_active_jobs(self):
        now = time.monotonic()
        previous = []
        for index in range(63):
            job = usb.Deployment('USB012')
            job.state = 'done'
            job.created = now - (index + 1)
            previous.append(job)
            self.bridge.jobs[job.id] = job
        active = usb.Deployment('OTHER_USB_DEVICE')
        self.bridge.jobs[active.id] = active
        first = self.wait(self.bridge.start('USB012', '/ode/download/project-output/123/Android'))
        self.assertEqual(first['state'], 'done')
        self.assertNotIn(previous[-1].id, self.bridge.jobs)
        for _ in range(70):
            result = self.wait(self.bridge.start('USB012', '/ode/download/project-output/123/Android'))
            self.assertEqual(result['state'], 'done')
            self.assertLessEqual(len(self.bridge.jobs), 64)
            self.assertIs(self.bridge.jobs[active.id], active)

    def test_startup_cleanup_only_removes_old_exact_managed_regular_apks(self):
        old = self.data / ('deploy-' + 'a' * 32 + '.apk')
        recent = self.data / ('deploy-' + 'b' * 32 + '.apk')
        personal = self.data / 'personal.apk'
        almost = self.data / ('deploy-' + 'c' * 31 + '.apk')
        backup = self.data / ('deploy-' + 'd' * 32 + '.apk.backup')
        nested = self.data / 'projects'
        nested.mkdir()
        nested_apk = nested / ('deploy-' + 'e' * 32 + '.apk')
        directory = self.data / ('deploy-' + 'f' * 32 + '.apk')
        directory.mkdir()
        for path in (old, recent, personal, almost, backup, nested_apk):
            path.write_bytes(b'fixture APK')
        expired = time.time() - 25 * 60 * 60
        for path in (old, personal, almost, backup, nested_apk, directory):
            os.utime(path, (expired, expired))
        usb.Bridge(self.data, 8888, self.adb, self.fetch)
        self.assertFalse(old.exists())
        for path in (recent, personal, almost, backup, nested_apk, directory):
            self.assertTrue(path.exists(), str(path))

    def test_authenticated_http_api_rejects_rebinding_csrf_invalid_json(self):
        token = 'a' * 64
        service = ThreadingHTTPServer(('127.0.0.1', 0), usb.make_handler(self.bridge, token, 0))
        port = service.server_port
        service.RequestHandlerClass = usb.make_handler(self.bridge, token, port)
        threading.Thread(target=service.serve_forever, daemon=True).start()
        def request(path, headers=None, body=None):
            req = urllib.request.Request('http://127.0.0.1:%d%s' % (port, path), data=body, headers=headers or {})
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.status, response.read().decode()
            except urllib.error.HTTPError as error:
                return error.code, error.read().decode()
        try:
            self.assertEqual(request('/health'), (200, 'YuxuanUsb/1'))
            self.assertEqual(request('/api/devices')[0], 403)
            headers = {'X-Offline-Control': token}
            self.assertEqual(request('/api/devices', headers)[0], 200)
            self.assertEqual(request('/api/devices', dict(headers, Host='evil.test'))[0], 403)
            self.assertEqual(request('/api/devices', dict(headers, Origin='https://evil.test'))[0], 403)
            self.assertEqual(request('/api/devices', dict(headers, Origin='http://127.0.0.1:8888'))[0], 200)
            self.assertEqual(request('/api/install', headers, b'{}')[0], 415)
            headers['Content-Type'] = 'application/json'
            self.assertEqual(request('/api/install', headers, b'[]')[0], 400)
            self.assertEqual(request('/api/install', headers, b'notjson')[0], 400)
            body = json.dumps({'serial': 'USB012', 'downloadPath': '/ode/download/project-output/123/Android'}).encode()
            status, response = request('/api/install', headers, body)
            self.assertEqual(status, 202)
            job = json.loads(response)['job']
            self.wait(self.bridge.jobs[job])
            status, response = request('/api/job?id=' + job, headers)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(response)['state'], 'done')
        finally:
            service.shutdown()
            service.server_close()

    def test_download_does_not_follow_redirect_and_forwards_cookie_locally(self):
        fixture = self.fixture.read_bytes()
        received = []
        class DownloadHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                received.append(self.headers.get('Cookie'))
                if self.path == '/ode/download/project-output/124/Android':
                    self.send_response(302)
                    self.send_header('Location', 'http://192.0.2.1:9999/attack')
                    self.end_headers()
                else:
                    self.send_response(200)
                    self.send_header('Content-Length', str(len(fixture)))
                    self.end_headers()
                    self.wfile.write(fixture)
            def log_message(self, *args):
                pass
        service = ThreadingHTTPServer(('127.0.0.1', 0), DownloadHandler)
        threading.Thread(target=service.serve_forever, daemon=True).start()
        bridge = usb.Bridge(self.data, service.server_port)
        try:
            target = self.data / 'download.apk'
            bridge.fetch('/ode/download/project-output/123/Android', 'SID=fixture', target)
            self.assertEqual(usb.apk_identity(target)[0], 'appinventor.ai_test.UsbTest')
            self.assertEqual(received, ['SID=fixture'])
            with self.assertRaises(usb.BridgeError):
                bridge.fetch('/ode/download/project-output/124/Android', 'SID=fixture', target)
            with self.assertRaises(usb.BridgeError):
                bridge.fetch('/ode/download/project-output/123/Android', 'SID=x\r\nInjected: value', target)
        finally:
            service.shutdown()
            service.server_close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
