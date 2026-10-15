"""Loopback-only USB deployment bridge for the locally installed App Inventor.

The web application's authenticated same-origin servlet is the only client.
Its random startup token stays in process environments, never browser storage.
"""
import argparse
import hmac
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
import urllib.request
import uuid
import zipfile

ROOT = Path(__file__).resolve().parent
APK_LIMIT = 128 * 1024 * 1024
BODY_LIMIT = 32768
JAVA_NAME = r'[A-Za-z_][A-Za-z0-9_$]*(?:\.[A-Za-z_][A-Za-z0-9_$]*)*'
PACKAGE_RE = re.compile(JAVA_NAME + r'\Z')
DOWNLOAD_RE = re.compile(r'/ode/download/project-output/[0-9]{1,20}/Android\Z')
SERIAL_RE = re.compile(r'[A-Za-z0-9_.-]{1,128}\Z')
DEPLOYMENT_RE = re.compile(r'deploy-[a-f0-9]{32}\.apk\Z')


class BridgeError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def validate_download(path):
    if not isinstance(path, str) or not DOWNLOAD_RE.fullmatch(path):
        raise BridgeError('请选择当前 App Inventor 项目生成的 APK。')
    return path


def parse_devices(output):
    devices = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 2 or not SERIAL_RE.fullmatch(parts[0]):
            continue
        serial, state = parts[:2]
        if state not in ('device', 'offline', 'unauthorized', 'recovery', 'sideload', 'bootloader'):
            continue
        # This feature is explicitly USB-only. Wireless and emulator transports
        # must not accidentally receive a project selected for a physical phone.
        if serial.startswith('emulator-') or '_adb-tls-' in serial or serial.endswith('._tcp'):
            continue
        fields = dict(item.split(':', 1) for item in parts[2:] if ':' in item)
        model = fields.get('model', serial).replace('_', ' ')
        suffix = {'device': '已连接', 'offline': '离线', 'unauthorized': '请在手机上允许 USB 调试'}.get(state, state)
        devices.append({'serial': serial, 'state': state, 'model': model,
                        'label': model + ' · ' + serial + ' · ' + suffix,
                        'transport': 'usb', 'transportId': fields.get('transport_id', '')})
    return devices


def apk_identity(apk):
    """Read the APK's compiled manifest without extracting platform build tools."""
    try:
        with zipfile.ZipFile(apk) as package:
            item = package.getinfo('AndroidManifest.xml')
            if item.file_size > 4 * 1024 * 1024:
                raise ValueError('manifest size')
            manifest = package.read(item)
        return manifest_identity(manifest)
    except (ValueError, KeyError, IndexError, OSError, zipfile.BadZipFile, struct.error, UnicodeError) as error:
        raise BridgeError('构建结果不是有效的 Android APK，无法读取应用信息。') from error


def manifest_identity(data):
    if len(data) < 8:
        raise ValueError('short manifest')
    kind, header, total = struct.unpack_from('<HHI', data)
    if kind != 3 or header != 8 or total > len(data):
        raise ValueError('not binary XML')
    strings, stack, package, launcher = [], [], None, None
    position = header
    current_activity = None
    intent = None

    def string(index):
        if index == 0xffffffff:
            return ''
        if index >= len(strings):
            raise ValueError('string index')
        return strings[index]

    while position < total:
        if position + 8 > total:
            raise ValueError('chunk header')
        kind, header, size = struct.unpack_from('<HHI', data, position)
        if header < 8 or size < header or position + size > total:
            raise ValueError('chunk size')
        chunk = data[position:position + size]
        if kind == 1:
            if header < 28:
                raise ValueError('string pool header')
            count, _, flags, start, _ = struct.unpack_from('<IIIII', chunk, 8)
            if count > 100000 or header + count * 4 > size:
                raise ValueError('string pool count')
            utf8 = bool(flags & 0x100)
            strings = []
            for index in range(count):
                at = start + struct.unpack_from('<I', chunk, header + index * 4)[0]
                def length(at, wide):
                    if wide:
                        value = struct.unpack_from('<H', chunk, at)[0]
                        at += 2
                        if value & 0x8000:
                            value = ((value & 0x7fff) << 16) | struct.unpack_from('<H', chunk, at)[0]
                            at += 2
                    else:
                        value = chunk[at]
                        at += 1
                        if value & 0x80:
                            value = ((value & 0x7f) << 8) | chunk[at]
                            at += 1
                    return value, at
                if utf8:
                    _, at = length(at, False)
                    count_bytes, at = length(at, False)
                    end = at + count_bytes
                    if end >= len(chunk) or chunk[end] != 0:
                        raise ValueError('string length')
                    value = chunk[at:end].decode('utf-8')
                else:
                    count_units, at = length(at, True)
                    end = at + count_units * 2
                    if end + 2 > len(chunk) or chunk[end:end + 2] != b'\0\0':
                        raise ValueError('string length')
                    value = chunk[at:end].decode('utf-16le')
                strings.append(value)
        elif kind == 0x102:
            if header < 16 or header + 20 > size:
                raise ValueError('element header')
            _, name, attribute_start, attribute_size, count = struct.unpack_from('<IIHHH', chunk, header)
            if attribute_size < 20 or header + attribute_start + count * attribute_size > size:
                raise ValueError('attributes')
            name, attributes = string(name), {}
            for index in range(count):
                at = header + attribute_start + index * attribute_size
                namespace, key, raw, value_size, _, value_type, value = struct.unpack_from('<IIIHBBI', chunk, at)
                attributes[(string(namespace), string(key))] = string(raw) if raw != 0xffffffff else string(value) if value_type == 3 else ''
            def attr(key):
                return attributes.get(('http://schemas.android.com/apk/res/android', key), '')
            if name == 'manifest':
                package = attributes.get(('', 'package'))
            elif name in ('activity', 'activity-alias'):
                current_activity = attr('name')
            elif name == 'intent-filter' and current_activity:
                intent = {'activity': current_activity, 'main': False, 'launcher': False}
            elif name == 'action' and intent is not None and attr('name') == 'android.intent.action.MAIN':
                intent['main'] = True
            elif name == 'category' and intent is not None and attr('name') == 'android.intent.category.LAUNCHER':
                intent['launcher'] = True
            stack.append(name)
        elif kind == 0x103:
            if not stack:
                raise ValueError('element nesting')
            name = stack.pop()
            if name == 'intent-filter':
                if intent and intent['main'] and intent['launcher']:
                    launcher = intent['activity']
                intent = None
            elif name in ('activity', 'activity-alias'):
                current_activity = None
        position += size
    if not package or not PACKAGE_RE.fullmatch(package) or not launcher:
        raise ValueError('no launchable package')
    if launcher.startswith('.'):
        launcher = package + launcher
    elif '.' not in launcher:
        launcher = package + '.' + launcher
    if len(launcher) > 512 or not PACKAGE_RE.fullmatch(launcher):
        raise ValueError('activity name')
    return package, launcher


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BridgeError('APK 下载地址发生跳转，请重新构建当前项目。')


class Deployment:
    def __init__(self, serial):
        self.id = uuid.uuid4().hex
        self.serial = serial
        self.state = 'running'
        self.stage = '正在获取构建结果'
        self.output = []
        self.package = self.activity = ''
        self.created = time.monotonic()
        self.lock = threading.Lock()

    def write(self, text):
        with self.lock:
            self.output.append(str(text))
            if sum(map(len, self.output)) > 65536:
                self.output = self.output[-20:]

    def snapshot(self):
        with self.lock:
            return {'job': self.id, 'state': self.state, 'stage': self.stage,
                    'output': '\n'.join(self.output), 'serial': self.serial,
                    'package': self.package, 'activity': self.activity}


class Bridge:
    def __init__(self, data, app_port, runner=None, fetcher=None, adb=None):
        self.data = Path(data)
        self.data.mkdir(parents=True, exist_ok=True)
        self.cleanup_deployments()
        self.app_port = app_port
        self.adb = Path(adb) if adb else ROOT / 'platform-tools/adb.exe'
        self.runner = runner or self.command
        self.fetcher = fetcher or self.fetch
        self.jobs, self.deployed = {}, {}
        self.lock = threading.Lock()

    def cleanup_deployments(self):
        # Core serializes this userdata directory. An age threshold also avoids
        # touching recent APKs if a developer starts a second bridge manually.
        cutoff = time.time() - 24 * 60 * 60
        for candidate in self.data.iterdir():
            if not DEPLOYMENT_RE.fullmatch(candidate.name):
                continue
            try:
                info = candidate.lstat()
                if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)
                        or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
                        or info.st_mtime >= cutoff):
                    continue
                candidate.unlink(missing_ok=True)
            except OSError:
                # A concurrently opened file or antivirus lock must not prevent
                # startup; a later launch can remove the old managed artifact.
                continue

    def command(self, args, timeout=15):
        environment = os.environ.copy()
        # Ignore unrelated Android Studio/emulator environment overrides.
        for key in ('ANDROID_SERIAL', 'ADB_SERVER_SOCKET', 'ANDROID_ADB_SERVER_PORT', 'ADB_TRACE'):
            environment.pop(key, None)
        environment['ADB_MDNS_AUTO_CONNECT'] = '0'
        environment['ADB_MDNS'] = '0'
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            # Keep ADB's default localhost host. Explicit -H 127.0.0.1 makes
            # ADB treat it as remote and prevents starting a missing daemon.
            result = subprocess.run([str(self.adb), '-P', '5037', *args],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=timeout, encoding='utf-8', errors='replace',
                                    env=environment, creationflags=flags, cwd=self.data)
        except subprocess.TimeoutExpired as error:
            raise BridgeError('设备操作超时，请解锁手机并确认 USB 调试 / 安装提示后重试。', 504) from error
        except OSError as error:
            raise BridgeError('内置 Android USB 工具无法启动，请重新安装软件。', 500) from error
        if result.returncode:
            raise BridgeError(result.stdout.strip() or 'Android USB 工具执行失败。', 502)
        return result.stdout.strip()

    def devices(self):
        return parse_devices(self.runner(['devices', '-l'], 20))

    def require_device(self, serial):
        if not isinstance(serial, str) or not SERIAL_RE.fullmatch(serial) or serial.startswith('emulator-'):
            raise BridgeError('请选择通过 USB 连接的 Android 手机。')
        match = next((device for device in self.devices() if device['serial'] == serial), None)
        if not match:
            raise BridgeError('手机已断开，请检查 USB 数据线并刷新设备列表。', 409)
        if match['state'] == 'unauthorized':
            raise BridgeError('请解锁手机，并点击“允许此计算机进行 USB 调试”，然后刷新设备列表。', 409)
        if match['state'] != 'device':
            raise BridgeError('手机当前离线或尚未启动完成，请重新连接并刷新设备列表。', 409)
        return match

    def fetch(self, path, cookie, target):
        validate_download(path)
        if not isinstance(cookie, str) or len(cookie) > 16384 or '\r' in cookie or '\n' in cookie:
            raise BridgeError('App Inventor 会话无效，请刷新网页后重试。')
        request = urllib.request.Request('http://127.0.0.1:%d%s' % (self.app_port, path),
                                         headers={'Cookie': cookie, 'Accept': 'application/vnd.android.package-archive'})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        try:
            with opener.open(request, timeout=45) as response, target.open('wb') as output:
                claimed = response.headers.get('Content-Length')
                if claimed and int(claimed) > APK_LIMIT:
                    raise BridgeError('APK 大于 128 MB，请下载到本地后安装。')
                total = 0
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    total += len(block)
                    if total > APK_LIMIT:
                        raise BridgeError('APK 大于 128 MB，请下载到本地后安装。')
                    output.write(block)
        except BridgeError:
            raise
        except Exception as error:
            raise BridgeError('无法获取当前项目的 APK，请等待构建完成后重试。', 502) from error

    def start(self, serial, path, cookie=''):
        validate_download(path)
        self.require_device(serial)
        with self.lock:
            self.jobs = {key: job for key, job in self.jobs.items()
                         if job.state == 'running' or time.monotonic() - job.created < 3600}
            if any(job.state == 'running' and job.serial == serial for job in self.jobs.values()):
                raise BridgeError('这台手机正在安装 APK，请等待当前任务完成。', 409)
            finished = sorted((job for job in self.jobs.values() if job.state != 'running'),
                              key=lambda job: job.created)
            for previous in finished[:max(0, len(self.jobs) - 63)]:
                self.jobs.pop(previous.id, None)
            if len(self.jobs) >= 64:
                raise BridgeError('运行任务过多，请稍后重试。', 429)
            job = Deployment(serial)
            self.jobs[job.id] = job
        threading.Thread(target=self.install, args=(job, path, cookie), daemon=True).start()
        return job

    def install(self, job, path, cookie):
        target = self.data / ('deploy-' + job.id + '.apk')
        try:
            self.fetcher(path, cookie, target)
            job.package, job.activity = apk_identity(target)
            self.require_device(job.serial)
            job.stage = '正在安装 APK，请留意手机提示'
            job.write('安装 ' + job.package + '（保留已有应用数据）')
            result = self.runner(['-s', job.serial, 'install', '-r', str(target)], 180)
            job.write(result)
            if not re.search(r'(?m)^Success\s*$', result):
                raise BridgeError(result or '手机未确认安装，请允许 USB 安装后重试。', 502)
            with self.lock:
                self.deployed[(job.serial, job.package)] = {'pid': '', 'created': time.monotonic()}
            job.stage = '正在手机上启动应用'
            self.require_device(job.serial)
            result = self.runner(['-s', job.serial, 'shell', 'am', 'start', '-W', '-S', '-n',
                                  job.package + '/' + job.activity], 45)
            job.write(result)
            if re.search(r'(?mi)^\s*(Error:|Exception|Status:\s*(?:timeout|error))', result):
                raise BridgeError('APK 已安装，但启动失败；请在手机上打开应用并查看运行日志。', 502)
            pid = ''
            try:
                value = self.runner(['-s', job.serial, 'shell', 'pidof', job.package], 10)
                pid = next((item for item in value.split() if item.isdigit()), '')
            except BridgeError:
                pass
            with self.lock:
                self.deployed[(job.serial, job.package)] = {'pid': pid, 'created': time.monotonic()}
            job.stage = '安装完成，应用已在手机上运行'
            job.state = 'done'
        except Exception as error:
            message = str(error)
            if 'INSTALL_FAILED_UPDATE_INCOMPATIBLE' in message:
                message += '\n手机上已有同名但签名不同的应用。请先备份其数据，再由你在手机上卸载旧应用后重试。'
            elif 'INSTALL_FAILED_USER_RESTRICTED' in message:
                message += '\n请在手机设置中允许 USB 安装，并确认手机上的安装提示。'
            elif 'INSTALL_FAILED_VERSION_DOWNGRADE' in message:
                message += '\n手机上的版本更高，请提高当前项目版本号后重新构建。'
            job.write(message)
            job.stage, job.state = '安装 / 启动失败', 'failed'
        finally:
            target.unlink(missing_ok=True)

    def job(self, identifier):
        if not re.fullmatch(r'[a-f0-9]{32}', identifier or ''):
            raise BridgeError('运行任务不存在。', 404)
        with self.lock:
            job = self.jobs.get(identifier)
        if not job:
            raise BridgeError('运行任务已结束或软件已重新启动，请重新运行。', 404)
        return job.snapshot()

    def logcat(self, serial, package):
        self.require_device(serial)
        if not isinstance(package, str) or not PACKAGE_RE.fullmatch(package):
            raise BridgeError('无效的应用标识。')
        with self.lock:
            record = self.deployed.get((serial, package))
        if record is None:
            raise BridgeError('请先将当前项目运行到这台手机，再查看应用日志。', 409)
        pid = record['pid']
        try:
            value = self.runner(['-s', serial, 'shell', 'pidof', package], 10)
            pid = next((item for item in value.split() if item.isdigit()), pid)
        except BridgeError:
            pass
        if not pid:
            return {'output': '', 'hint': '应用尚未运行，请重新点击运行。', 'package': package}
        record['pid'] = pid
        try:
            text = self.runner(['-s', serial, 'logcat', '--pid=' + pid, '-d', '-t', '250', '-v', 'threadtime'], 15)
        except BridgeError as error:
            if not any(term in str(error).lower() for term in ('unknown option', 'unrecognized option', 'invalid option')):
                raise
            text = self.runner(['-s', serial, 'logcat', '-d', '-t', '250', '-v', 'threadtime'], 15)
            # Old Android lacks --pid. Keep only the selected application's PID.
            text = '\n'.join(line for line in text.splitlines()
                             if re.match(r'^\d\d-\d\d\s+\S+\s+' + re.escape(pid) + r'\s+', line))
        return {'output': text[-65536:], 'hint': '', 'package': package, 'pid': pid}


def make_handler(bridge, token, port):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self, *args):
            pass

        def reply(self, status, body):
            encoded = json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(encoded)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(encoded)

        def authorized(self):
            if self.client_address[0] != '127.0.0.1' or self.headers.get('Host') != '127.0.0.1:' + str(port):
                raise BridgeError('USB 服务仅允许本机访问。', 403)
            if not hmac.compare_digest(self.headers.get('X-Offline-Control', ''), token):
                raise BridgeError('USB 服务验证失败，请重新启动软件。', 403)
            origin = self.headers.get('Origin')
            if origin and origin != 'http://127.0.0.1:' + str(bridge.app_port):
                raise BridgeError('USB 操作来源无效。', 403)

        def handle_request(self, post=False):
            try:
                if not post and self.path == '/health':
                    if self.client_address[0] != '127.0.0.1' or self.headers.get('Host') != '127.0.0.1:' + str(port):
                        raise BridgeError('USB 服务仅允许本机访问。', 403)
                    encoded = b'YuxuanUsb/1'
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.send_header('Content-Length', str(len(encoded)))
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    self.wfile.write(encoded)
                    return
                self.authorized()
                url = urlsplit(self.path)
                query = parse_qs(url.query, max_num_fields=6)
                if post:
                    if url.path != '/api/install' or url.query:
                        raise BridgeError('USB 接口不存在。', 404)
                    if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
                        raise BridgeError('请求必须为 JSON。', 415)
                    count = int(self.headers.get('Content-Length', '-1'))
                    if count < 0 or count > BODY_LIMIT or self.headers.get('Transfer-Encoding'):
                        raise BridgeError('请求内容过大或无效。', 413)
                    body = json.loads(self.rfile.read(count))
                    if not isinstance(body, dict) or set(body) - {'serial', 'downloadPath', 'cookie'}:
                        raise BridgeError('无效的 USB 运行请求。')
                    job = bridge.start(body.get('serial'), body.get('downloadPath'), body.get('cookie', ''))
                    self.reply(202, {'job': job.id, 'state': 'running'})
                elif url.path == '/api/devices' and not query:
                    devices = bridge.devices()
                    self.reply(200, {'devices': devices, 'hint': '' if devices else '请用 USB 数据线连接手机，开启开发者选项中的 USB 调试，并在手机上允许此计算机。'})
                elif url.path == '/api/job' and set(query) == {'id'} and len(query['id']) == 1:
                    self.reply(200, bridge.job(query['id'][0]))
                elif url.path == '/api/logcat' and set(query) == {'serial', 'package'} and all(len(values) == 1 for values in query.values()):
                    self.reply(200, bridge.logcat(query['serial'][0], query['package'][0]))
                elif url.path == '/api/health' and not query:
                    self.reply(200, {'ok': True})
                else:
                    raise BridgeError('USB 接口不存在。', 404)
            except BridgeError as error:
                self.reply(error.status, {'error': str(error)})
            except (ValueError, TypeError, KeyError, UnicodeError):
                self.reply(400, {'error': '无效的 USB 请求。'})
            except Exception:
                self.reply(500, {'error': 'USB 操作失败，请刷新设备列表后重试。'})

        def do_GET(self):
            self.handle_request()

        def do_POST(self):
            self.handle_request(True)
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--app-port', type=int, required=True)
    parser.add_argument('--data', type=Path, required=True)
    options = parser.parse_args()
    token = os.environ.pop('YX_USB_TOKEN', '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{32,128}', token):
        raise SystemExit('USB startup token is missing or invalid.')
    if not (1 <= options.port <= 65535 and 1 <= options.app_port <= 65535):
        raise SystemExit('USB ports are invalid.')
    bridge = Bridge(options.data, options.app_port)
    server = ThreadingHTTPServer(('127.0.0.1', options.port), make_handler(bridge, token, options.port))
    print('USB service ready on 127.0.0.1:%d' % options.port, flush=True)
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
