"""Windows Python client: activate online once, verify signed expiry offline.
The launcher checks online when reachable and checks local expiry every 60 seconds.
Dependency: cryptography. A LicenseError must stop the protected functionality.
"""
import base64, ctypes, hashlib, json, os, re, subprocess, time, uuid
import urllib.request, urllib.error
from pathlib import Path
from urllib.parse import urlsplit
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

class LicenseError(RuntimeError):
    pass

def device_fingerprint():
    if os.name != 'nt':
        raise LicenseError('此设备识别示例适用于 Windows')
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Cryptography',
                            0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            machine = str(winreg.QueryValueEx(key, 'MachineGuid')[0]).strip().lower()
        board = subprocess.check_output(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
             '(Get-CimInstance Win32_ComputerSystemProduct).UUID'],
            timeout=10, creationflags=subprocess.CREATE_NO_WINDOW,
        ).decode('utf-8', errors='replace').strip().lower()
        if not machine or uuid.UUID(board).int in (0, (1 << 128) - 1):
            raise LicenseError('设备标识不可用，请联系管理员')
        return hashlib.sha256(('yuxuan-device-v1|' + machine + '|' + board).encode()).hexdigest()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise LicenseError('无法读取设备标识，请联系管理员') from exc

def _dpapi(raw, entropy, decrypt=False):
    if os.name != 'nt':
        raise LicenseError('设备密钥保护需要 Windows DPAPI')
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    def blob(value):
        buffer = ctypes.create_string_buffer(value)
        return Blob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer
    source, source_buf = blob(raw)
    extra, extra_buf = blob(entropy)
    output = Blob()
    dll = ctypes.WinDLL('crypt32', use_last_error=True)
    fn = dll.CryptUnprotectData if decrypt else dll.CryptProtectData
    fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob),
                   ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    fn.restype = wintypes.BOOL
    if not fn(ctypes.byref(source), None, ctypes.byref(extra), None, None, 1, ctypes.byref(output)):
        raise LicenseError('设备密钥无法读取，请联系管理员移除绑定后重新激活')
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        kernel.LocalFree(output.data)

class LicenseClient:
    def __init__(self, base_url, product, server_public_key, state_dir=None, *, allow_local_test=False):
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}', product):
            raise LicenseError('软件标识无效')
        url = urlsplit(base_url)
        local = allow_local_test and url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost')
        if (url.scheme != 'https' and not local) or not url.netloc or url.username or url.password:
            raise LicenseError('激活服务必须使用 HTTPS')
        try:
            self.server_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(server_public_key, validate=True))
        except (ValueError, TypeError) as exc:
            raise LicenseError('请填入管理界面中的服务器签名公钥') from exc
        self.url = base_url.rstrip('/') + '/api.php?action='
        self.product, self.device = product, device_fingerprint()
        folder = Path(state_dir) if state_dir else Path(os.environ['LOCALAPPDATA']) / 'YuxuanLicense' / product
        folder.mkdir(parents=True, exist_ok=True)
        self.file, self.entropy = folder / 'device-license.bin', ('yuxuan-license-v1|' + product).encode()
        self.offline, self.last_seen, self.last_online, self.revoked = None, 0, 0, False
        if self.file.exists():
            try:
                state = json.loads(_dpapi(self.file.read_bytes(), self.entropy, decrypt=True))
                self.key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(state['privateKey'], validate=True))
                self.license_id = state.get('licenseId')
                self.offline = state.get('offline')
                self.last_seen = state.get('lastSeen', 0)
                self.last_online = state.get('lastOnline', 0)
                self.revoked = state.get('revoked', False)
            except LicenseError:
                raise
            except (KeyError, ValueError, TypeError) as exc:
                raise LicenseError('本地授权数据损坏，请联系管理员') from exc
        else:
            self.key, self.license_id = Ed25519PrivateKey.generate(), None
            self._save()
        self.public = base64.b64encode(self.key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()

    def _save(self):
        private = self.key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                         serialization.NoEncryption())
        raw = json.dumps({'privateKey': base64.b64encode(private).decode(), 'licenseId': self.license_id,
                          'offline': self.offline, 'lastSeen': self.last_seen,
                          'lastOnline': self.last_online, 'revoked': self.revoked}).encode()
        temp = self.file.with_suffix('.tmp')
        temp.write_bytes(_dpapi(raw, self.entropy))
        os.replace(temp, self.file)

    def _post(self, action, body):
        request = urllib.request.Request(self.url + action, data=json.dumps(body).encode(),
                                         headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                result = json.loads(response.read(65536))
            if not isinstance(result, dict):
                raise ValueError('JSON object required')
            return result
        except urllib.error.HTTPError as exc:
            try:
                reason = json.loads(exc.read(65536)).get('error', '授权校验失败')
            except (ValueError, AttributeError):
                reason = '授权服务未正常响应'
            error = LicenseError(reason)
            error.http_status = exc.code
            raise error from exc
        except (OSError, ValueError) as exc:
            raise LicenseError('无法连接授权服务，请检查网络后重试') from exc

    def _exchange(self, purpose, code=None):
        body = {'purpose': purpose, 'product': self.product, 'device': self.device,
                'publicKey': self.public, 'deviceName': os.environ.get('COMPUTERNAME', 'Windows device')}
        if purpose == 'activate':
            code = code.strip().upper()
            body['code'] = code
            target = hashlib.sha256(code.encode()).hexdigest()
        else:
            body['licenseId'], target = self.license_id, self.license_id
        challenge = self._post('challenge', body)
        try:
            message = base64.b64decode(challenge['message'], validate=True)
            details = json.loads(message)
            expected = {'protocol': 'yuxuan-license-v1', 'purpose': purpose, 'product': self.product,
                        'device': self.device, 'publicKey': self.public, 'target': target,
                        'challenge': challenge['challenge']}
            if any(details.get(k) != v for k, v in expected.items()) or details['until'] <= time.time():
                raise LicenseError('激活请求不匹配或已过期')
            result = self._post(purpose, {'challenge': challenge['challenge'],
                                'signature': base64.b64encode(self.key.sign(message)).decode()})
            raw = base64.b64decode(result['payload'], validate=True)
            self.server_key.verify(base64.b64decode(result['signature'], validate=True), raw)
            payload = json.loads(raw)
            expected = {'protocol': 'yuxuan-license-v1', 'product': self.product, 'device': self.device,
                        'publicKey': self.public, 'challenge': challenge['challenge']}
            if any(payload.get(k) != v for k, v in expected.items()):
                raise LicenseError('授权回复中的设备信息不匹配')
            if (payload['until'] <= time.time() or payload['issued'] > time.time() + 60
                    or payload['until'] - payload['issued'] > 180):
                raise LicenseError('授权回复已过期，请检查系统时间')
            if purpose == 'verify' and payload['licenseId'] != self.license_id:
                raise LicenseError('许可证编号不匹配')
            if 'offlinePayload' in result and 'offlineSignature' in result:
                candidate = {'payload': result['offlinePayload'], 'signature': result['offlineSignature']}
                certificate = self._offline_payload(candidate, payload['licenseId'])
                if certificate.get('challenge') != challenge['challenge'] or certificate.get('expires') != payload.get('expires'):
                    raise LicenseError('离线授权回复不匹配')
                self.offline = candidate
            self.revoked = False
            self.last_online = payload['issued']
            self.last_seen = max(time.time(), self.last_seen)
            return payload
        except LicenseError:
            raise
        except (KeyError, ValueError, TypeError, InvalidSignature) as exc:
            raise LicenseError('授权签名无法验证，请联系管理员') from exc

    def activate(self, code):
        payload = self._exchange('activate', code)
        self.license_id = payload['licenseId']
        self._save()
        return payload

    def validate(self):
        if not self.license_id:
            raise LicenseError('请先输入激活码')
        try:
            payload = self._exchange('verify')
        except LicenseError as error:
            if getattr(error, 'http_status', None) in (403, 404, 409):
                self.revoked, self.offline = True, None
                self._save()
            raise
        self._save()
        return payload

    def _offline_payload(self, certificate, license_id):
        try:
            raw = base64.b64decode(certificate['payload'], validate=True)
            self.server_key.verify(base64.b64decode(certificate['signature'], validate=True), raw)
            payload = json.loads(raw)
            expected = {'protocol': 'yuxuan-offline-license-v1', 'product': self.product,
                        'device': self.device, 'publicKey': self.public, 'licenseId': license_id}
            if any(payload.get(k) != v for k, v in expected.items()):
                raise LicenseError('离线授权不属于此软件或当前设备')
            issued, expires = payload['issued'], payload['expires']
            if type(issued) is not int or issued > time.time() + 60:
                raise LicenseError('授权签发时间无效，请检查系统时间')
            if expires is not None and (type(expires) is not int or expires <= issued):
                raise LicenseError('离线授权有效期无效')
            return payload
        except LicenseError:
            raise
        except (KeyError, ValueError, TypeError, InvalidSignature) as error:
            raise LicenseError('离线授权签名无法验证，请重新联网激活') from error

    def validate_offline(self):
        if self.revoked:
            raise LicenseError('此授权已失效，请联网重新验证或使用新的激活码')
        if not self.license_id or not self.offline:
            raise LicenseError('首次使用必须联网激活，当前没有有效的离线授权')
        payload = self._offline_payload(self.offline, self.license_id)
        now = time.time()
        if not isinstance(self.last_seen, (int, float)) or now < self.last_seen - 300:
            raise LicenseError('检测到系统时间回退，请校正时间后重试')
        effective_time = max(now, self.last_seen)
        if payload['expires'] is not None and effective_time >= payload['expires']:
            raise LicenseError('授权已到期，请使用新的激活码')
        self.last_seen = effective_time
        self._save()
        return payload
