"""Private JSON-lines bridge for the desktop launcher. No license-code logging."""
import sys, pathlib, json, urllib.request, urllib.error
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'vendor'))
from license_client import LicenseClient, LicenseError

URL = 'https://www.yuxuan-blog.top/jihuo'
PRODUCT = 'my_computer'
PUBLIC_KEY = 'JXoGP5v9+E3w8MwYfHnPRT/Pg1TpH+/wb8Bh3GautdM='

def internet_probe():
    try:
        with urllib.request.urlopen(URL+'/api.php?action=capabilities', timeout=2) as response:
            response.read(4096)
            return True
    except urllib.error.HTTPError:
        # An HTTP reply still proves a working route to the authorization service.
        return True
    except (OSError, ValueError):
        return False

def check(client, online=False):
    if not client.license_id:
        raise LicenseError('首次使用必须联网激活，请输入激活码')
    connected = bool(online) or internet_probe()
    unavailable = False
    if connected:
        try:
            client.validate()
        except LicenseError as error:
            if getattr(error, 'http_status', None) in (403, 404, 409):
                raise
            # A service outage is not a revocation. A valid signed offline grant remains usable.
            unavailable = True
    payload = client.validate_offline()
    return {'ok': True, 'activated': True, 'online': connected,
            'expires': payload['expires'], 'lastOnline': client.last_online,
            'message': '离线授权有效 · 在线验证暂不可用' if unavailable else ('在线授权验证通过' if connected else '离线授权验证通过')}

def main():
    state = pathlib.Path(sys.argv[sys.argv.index('--state')+1]).resolve()
    client = None
    for line in sys.stdin:
        try:
            if len(line) > 4096:
                raise LicenseError('请求内容过大')
            request = json.loads(line)
            action = request.get('action')
            if action == 'exit':
                break
            if client is None:
                client = LicenseClient(URL, PRODUCT, PUBLIC_KEY, state)
            if action == 'activate':
                code = request.get('code', '').strip().upper()
                import re
                if not re.fullmatch(r'YX(?:-[A-F0-9]{8}){4}', code):
                    raise LicenseError('请输入正确格式的激活码')
                client.activate(code)
                result = check(client, False)
            elif action == 'check':
                result = check(client, request.get('online', False))
            elif action == 'status':
                result = {'ok':True, 'activated':bool(client.license_id), 'offlineCertificate':bool(client.offline)}
            else:
                raise LicenseError('未知授权操作')
        except LicenseError as error:
            result = {'ok':False, 'message':str(error), 'activated':bool(client and client.license_id),
                      'httpStatus':getattr(error,'http_status',None)}
        except Exception:
            result = {'ok':False, 'message':'授权校验无法完成，请重新启动软件后重试'}
        print(json.dumps(result, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
