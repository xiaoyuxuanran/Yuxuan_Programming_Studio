"""Loopback-only Mixly browser workspace and bounded native Arduino bridge."""
from __future__ import annotations
import argparse
import codecs
import hashlib
import hmac
import http.cookies
import io
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import socket
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if not (ROOT / 'runtime').is_dir():
    ROOT = ROOT / 'work/native'
sys.path.insert(0, str(ROOT / 'mixly/python-libs'))
import serial
from serial.tools import list_ports
sys.path.insert(0, str(ROOT / 'studio'))
from runtime_support import https_context
from cloud import CloudLibraries
from toolchain_paths import SDKPath

ENVIRONMENTS = {
    'arduino_avr': ('Arduino AVR', 'arduino:avr:'),
    'arduino_esp32': ('Arduino ESP32', 'esp32:esp32:'),
    'micropython_esp32': ('MicroPython ESP32', None),
    'arduino_esp8266': ('Arduino ESP8266', 'esp8266:esp8266:'),
}
MAX_BODY = 8 * 1024 * 1024


class Workspace:
    def __init__(self, data: Path, token: str):
        self.data = data
        self.token = token
        self.jobs = {}
        self.lock = threading.RLock()
        self.serial = None
        self.serial_output = ''
        self.serial_end = 0
        self.serial_lock = threading.RLock()
        self.stopping = False
        data.mkdir(parents=True, exist_ok=True)
        self.sdk_path = SDKPath(ROOT / 'mixly/arduino-cli')
        self.data_path = SDKPath(data)
        data = self.data_path.path
        self.data = data
        self.cloud = CloudLibraries(data, https_context)
        self.sdk = self.sdk_path.path
        self.cli = self.sdk / 'arduino-cli.exe'
        self.config = data / 'arduino-cli.json'
        self.config.write_text(json.dumps({'directories': {
            'data': str(self.sdk / 'Arduino15'),
            'downloads': str(data / 'staging'), 'user': str(data / 'Arduino')},
            'metrics': {'enabled': False}, 'updater': {'enable_notification': False}}), encoding='utf-8')
        probe = subprocess.run([sys.executable, '-X', 'utf8', str(HERE / 'compiler-paths.py'),
                                str(self.sdk), str(data)],
                               capture_output=True, text=True, encoding='utf-8',
                               timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        if probe.returncode:
            raise RuntimeError('编译器路径准备失败：' + probe.stderr[-1000:])
        self.compiler_properties = json.loads(probe.stdout)['properties']

    @staticmethod
    def ports():
        return [{'device': p.device, 'description': p.description,
                 'vid': p.vid, 'pid': p.pid} for p in list_ports.comports()]

    def start_job(self, payload):
        fqbn = payload.get('fqbn', '')
        if not isinstance(fqbn, str) or not re.fullmatch(r'[A-Za-z0-9_.:=,+-]{1,300}', fqbn):
            raise ValueError('开发板参数无效')
        package = ':'.join(fqbn.split(':')[:2])
        if package not in self.compiler_properties:
            raise ValueError('不支持的开发板环境')
        code = payload.get('code')
        if not isinstance(code, str) or len(code.encode('utf-8')) > 1024 * 1024:
            raise ValueError('程序内容无效或过大')
        upload = payload.get('upload') is True
        port = payload.get('port', '')
        if upload and port not in {p['device'] for p in self.ports()}:
            raise ValueError('请选择当前已连接的 USB 串口')
        options = payload.get('options') or {}
        if not isinstance(options, dict) or len(options) > 40:
            raise ValueError('开发板选项无效')
        option_parts = []
        for key, value in options.items():
            # Mixly command parameters may include non-board metadata.
            if isinstance(value, (dict, list)):
                continue
            if not re.fullmatch(r'[A-Za-z0-9_]{1,60}', str(key)) or not re.fullmatch(r'[A-Za-z0-9_.+-]{1,120}', str(value)):
                raise ValueError('开发板选项含非法字符')
            option_parts.append(f'{key}={value}')
        files = payload.get('files') or {}
        plugins = payload.get('plugins') or []
        if not isinstance(plugins, list) or len(plugins) > 64 or any(not isinstance(p, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', p) for p in plugins):
            raise ValueError('扩展库列表无效')
        if not isinstance(files, dict) or len(files) > 256:
            raise ValueError('附加源文件过多')
        validated = []
        total = 0
        for name, content in files.items():
            if not isinstance(name, str) or not isinstance(content, str):
                raise ValueError('附加源文件无效')
            name = name.replace('\\', '/')
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or ':' in name or not path.name:
                raise ValueError('源文件路径无效')
            if not path.suffix:
                path = path.with_suffix('.h')
            size = len(content.encode('utf-8'))
            total += size
            if size > 2 * 1024 * 1024 or total > 6 * 1024 * 1024:
                raise ValueError('附加源文件过大')
            validated.append((path, content))
        with self.lock:
            if any(j['state'] == 'running' for j in self.jobs.values()):
                raise RuntimeError('已有编译或上传任务运行中，请先等待完成或停止')
            for key in list(self.jobs)[:-19]:
                self.jobs.pop(key)
            ident = secrets.token_hex(16)
            folder = self.data / 'build' / ident
            sketch = folder / 'sketch'
            sketch.mkdir(parents=True)
            (sketch / 'sketch.ino').write_text(code, encoding='utf-8')
            for path, content in validated:
                target = sketch / Path(path)
                if target.name == 'sketch.ino':
                    raise ValueError('附加文件不能覆盖主程序')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding='utf-8')
            args = [str(self.cli), 'compile', '--config-file', str(self.config),
                    '--fqbn', fqbn, '--build-path', str(folder / 'output'),
                    '--build-cache-path', str(self.data / 'core-cache'),
                    '--libraries', str(self.sdk / 'libraries'),
                    '--libraries', str(self.data / 'Arduino/libraries')]
            (self.data / 'Arduino/libraries').mkdir(parents=True, exist_ok=True)
            for plugin in plugins:
                library_dir = self.data / 'cloud/packages' / plugin / 'libraries'
                if library_dir.is_dir():
                    args += ['--libraries', str(library_dir)]
            if option_parts:
                args += ['--board-options', ','.join(option_parts)]
            for key, value in self.compiler_properties[package]:
                args += ['--build-property', f'{key}={value}']
            args.append(str(sketch))
            if upload:
                self.close_serial()
            job = {'id': ident, 'state': 'running', 'output': '', 'outputEnd': 0, 'exitCode': None,
                   'cancelled': False, '_process': None, '_folder': folder}
            self.jobs[ident] = job
            threading.Thread(target=self.run_job, args=(job, args, fqbn, port if upload else ''), daemon=True).start()
            return {'id': ident}

    def run_job(self, job, args, fqbn, upload_port):
        started = time.monotonic()
        def append(text):
            with self.lock:
                job['outputEnd'] += len(text.encode('utf-16-le')) // 2
                job['output'] = (job['output'] + text)[-2 * 1024 * 1024:]
        def execute(command):
            if job['cancelled']:
                return 130
            process = subprocess.Popen(command, cwd=self.data, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
                                       env={**os.environ, 'PYTHONUTF8': '1'})
            with self.lock:
                job['_process'] = process
            def timeout():
                while process.poll() is None:
                    if job['cancelled'] or self.stopping or time.monotonic() - started > 900:
                        job['cancelled'] = True
                        subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                                       capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                        break
                    time.sleep(.2)
            threading.Thread(target=timeout, daemon=True).start()
            for line in iter(process.stdout.readline, b''):
                append(line.decode('utf-8', errors='replace'))
            return process.wait()
        try:
            result = execute(args)
            if result == 0 and upload_port and not job['cancelled']:
                append('\n正在上传至 ' + upload_port + '…\n')
                result = execute([str(self.cli), 'upload', '--config-file', str(self.config),
                                  '--fqbn', fqbn, '--port', upload_port,
                                  '--input-dir', str(job['_folder'] / 'output')])
            job['exitCode'] = 130 if job['cancelled'] else result
        except Exception as error:
            append('\n' + str(error))
            job['exitCode'] = 1
        finally:
            job['_process'] = None
            job['state'] = 'done'

    def job(self, ident):
        with self.lock:
            if ident not in self.jobs:
                raise KeyError('任务不存在')
            return {k: v for k, v in self.jobs[ident].items() if not k.startswith('_')}

    def close_serial(self):
        with self.serial_lock:
            if self.serial:
                self.serial.close()
                self.serial = None

    def open_serial(self, port, baud):
        if port not in {p['device'] for p in self.ports()} or baud not in (300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 74880, 115200, 230400, 460800, 921600):
            raise ValueError('串口或波特率无效')
        self.close_serial()
        with self.serial_lock:
            self.serial = serial.Serial(port, baudrate=baud, timeout=.1, write_timeout=2)
            self.serial_output = ''
            self.serial_end = 0
        def read():
            connection = self.serial
            decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
            while not self.stopping and connection is self.serial and connection.is_open:
                try:
                    value = connection.read(max(1, min(connection.in_waiting, 8192)))
                    if value:
                        text = decoder.decode(value)
                        with self.serial_lock:
                            self.serial_end += len(text.encode('utf-16-le')) // 2
                            self.serial_output = (self.serial_output + text)[-200000:]
                except (serial.SerialException, OSError):
                    break
        threading.Thread(target=read, daemon=True).start()

    def stop(self):
        self.stopping = True
        for job in self.jobs.values():
            if job['state'] == 'running':
                job['cancelled'] = True
        self.close_serial()


class Handler(SimpleHTTPRequestHandler):
    server_version = 'YuxuanMixlyWeb/2.3.0'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE / 'site'), **kwargs)

    @property
    def app(self):
        return self.server.workspace

    def log_message(self, *_):
        pass

    def valid_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

    def authorized(self):
        if not self.valid_host():
            return False
        if hmac.compare_digest(self.headers.get('X-Suite-Token', ''), self.app.token):
            return True
        try:
            cookies = http.cookies.SimpleCookie(self.headers.get('Cookie', ''))
            return hmac.compare_digest(cookies['yx_mixly'].value, self.app.token)
        except (KeyError, http.cookies.CookieError):
            return False

    def json_response(self, status, data, cookie=False):
        raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if cookie:
            self.send_header('Set-Cookie', f'yx_mixly={self.app.token}; HttpOnly; SameSite=Strict; Path=/')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if not self.valid_host():
            return self.json_response(403, {'error': 'Forbidden Host'})
        path = urlsplit(self.path).path
        if path == '/health':
            return self.json_response(200, {'app': 'YuxuanMixlyWeb', 'version': '2.3.0'})
        if path.startswith('/api/'):
            if not self.authorized():
                return self.json_response(403, {'error': '请从已激活的启动器打开米思齐'})
            try:
                if path == '/api/contest/health':
                    return self.json_response(200, {'ok': False, 'hasSession': False})
                if path == '/api/update/health':
                    return self.json_response(200, {'ok': False, 'enabled': False})
                if path == '/api/ports':
                    return self.json_response(200, {'ports': self.app.ports()})
                if path == '/api/cloud/catalog':
                    query = parse_qs(urlsplit(self.path).query)
                    items = self.app.cloud.catalog(query.get('board', [''])[0])
                    return self.json_response(200, [{k: v for k, v in item.items() if not k.startswith('_')} for item in items])
                if path == '/api/cloud/package':
                    query = parse_qs(urlsplit(self.path).query)
                    raw = self.app.cloud.package(query.get('board', [''])[0], query.get('id', [''])[0])
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/zip')
                    self.send_header('Content-Length', str(len(raw)))
                    self.send_header('Cache-Control', 'private, max-age=300')
                    self.end_headers()
                    self.wfile.write(raw)
                    return
                if re.fullmatch(r'/api/jobs/[0-9a-f]{32}', path):
                    return self.json_response(200, self.app.job(path.rsplit('/', 1)[1]))
                if path == '/api/serial':
                    with self.app.serial_lock:
                        return self.json_response(200, {'open': bool(self.app.serial and self.app.serial.is_open), 'output': self.app.serial_output, 'outputEnd': self.app.serial_end})
                return self.json_response(404, {'error': '接口不存在'})
            except KeyError as error:
                return self.json_response(404, {'error': str(error)})
            except Exception as error:
                return self.json_response(400, {'error': str(error)})
        if path.startswith('/editor/') and not self.authorized():
            return self.json_response(403, {'error': '请先从启动器进入工作台'})
        translated = Path(self.translate_path(path)).resolve()
        if not translated.is_relative_to((HERE / 'site').resolve()) or translated.is_dir() and not (translated / 'index.html').is_file():
            return self.json_response(404, {'error': '文件不存在'})
        super().do_GET()

    def do_POST(self):
        if not self.valid_host():
            return self.json_response(403, {'error': 'Forbidden Host'})
        expected_origin = f'http://127.0.0.1:{self.server.server_port}'
        if self.headers.get('Origin') not in (None, expected_origin):
            return self.json_response(403, {'error': 'Forbidden Origin'})
        path = urlsplit(self.path).path
        try:
            length = int(self.headers.get('Content-Length', '-1'))
            if not 0 <= length <= MAX_BODY:
                return self.json_response(413, {'error': '请求内容过大或无效'})
            if not self.headers.get('Content-Type', '').startswith('application/json'):
                return self.json_response(415, {'error': '需要 JSON 请求'})
            body = json.loads(self.rfile.read(length) or b'{}')
            if not isinstance(body, dict):
                raise ValueError('请求格式无效')
            if path == '/api/session':
                if not hmac.compare_digest(str(body.get('token', '')), self.app.token):
                    return self.json_response(403, {'error': '请从启动器重新打开工作台'})
                return self.json_response(200, {'ok': True}, cookie=True)
            if not self.authorized() or not (self.headers.get('X-Yuxuan-Mixly') == '1' or self.headers.get('X-Suite-Token')):
                return self.json_response(403, {'error': 'Forbidden'})
            if path == '/api/arduino':
                return self.json_response(202, self.app.start_job(body))
            if re.fullmatch(r'/api/jobs/[0-9a-f]{32}/stop', path):
                ident = path.split('/')[3]
                self.app.job(ident)
                self.app.jobs[ident]['cancelled'] = True
                return self.json_response(200, {'ok': True})
            if path == '/api/serial/open':
                self.app.open_serial(body.get('port'), int(body.get('baud', 115200)))
                return self.json_response(200, {'ok': True})
            if path == '/api/serial/close':
                self.app.close_serial()
                return self.json_response(200, {'ok': True})
            if path == '/api/serial/send':
                text = body.get('text', '')
                if not isinstance(text, str) or len(text.encode('utf-8')) > 16384:
                    raise ValueError('发送内容过大')
                with self.app.serial_lock:
                    if not self.app.serial or not self.app.serial.is_open:
                        raise ValueError('请先打开串口')
                    self.app.serial.write(text.encode('utf-8'))
                return self.json_response(200, {'ok': True})
            if path == '/api/shutdown':
                self.json_response(200, {'ok': True})
                self.app.stop()
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            return self.json_response(404, {'error': '接口不存在'})
        except (ValueError, TypeError, serial.SerialException) as error:
            self.json_response(400, {'error': str(error)})
        except KeyError as error:
            self.json_response(404, {'error': str(error)})
        except RuntimeError as error:
            self.json_response(409, {'error': str(error)})


class LocalHTTPServer(ThreadingHTTPServer):
    # On Windows SO_REUSEADDR permits another process to bind the same port.
    # Use exclusive binding so multiple workspaces cannot share authorization.
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--token', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{64}', args.token):
        raise SystemExit('A launcher-generated token is required')
    app = Workspace(args.data.resolve(), args.token)
    settings_path = args.data / 'web-settings.json'
    try:
        preferred = int(json.loads(settings_path.read_text(encoding='utf-8'))['port'])
        if not 1024 <= preferred <= 65535:
            preferred = 8768
    except (OSError, ValueError, KeyError):
        preferred = 8768
    try:
        server = LocalHTTPServer(('127.0.0.1', preferred), Handler)
    except OSError:
        server = LocalHTTPServer(('127.0.0.1', 0), Handler)
    server.workspace = app
    settings_path.write_text(json.dumps({'port': server.server_port}), encoding='utf-8')
    running = args.data / 'mixly-running.json'
    running.write_text(json.dumps({'app': 'YuxuanMixlyWeb', 'pid': os.getpid(), 'port': server.server_port}), encoding='utf-8')
    try:
        server.serve_forever(poll_interval=.2)
    finally:
        app.stop()
        server.server_close()
        for _ in range(50):
            if not any(j['state'] == 'running' for j in app.jobs.values()):
                break
            time.sleep(.1)
        running.unlink(missing_ok=True)
        app.sdk_path.close()
        app.data_path.close()


if __name__ == '__main__':
    main()
