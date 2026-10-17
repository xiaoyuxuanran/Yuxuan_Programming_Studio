"""Isolated installed 2.3 checks. Uses an existing same-user grant; never activates."""
import argparse, contextlib, hashlib, http.cookiejar, json, os, pathlib, re, secrets, shutil, subprocess, time, urllib.parse, urllib.request, zipfile

HERE = pathlib.Path(__file__).resolve().parent
FLAGS = subprocess.CREATE_NO_WINDOW
CRITICAL = [
    'AppInventor.exe', 'AppInventorCore.exe', 'license/gate.py', 'license/license_client.py',
    'license/vendor/_cffi_backend.cp313-win_amd64.pyd', 'studio/server.py', 'studio/runtime_support.py',
    'studio/studio.js', 'studio/studio.css', 'studio/index.html', 'studio/vs/loader.js',
    'runtime/python3.8.9/python.exe', 'runtime/python3.13.16/python.exe',
    'runtime/python3.8.9/DLLs/_tkinter.pyd', 'runtime/python3.13.16/DLLs/_tkinter.pyd',
    'runtime/llvm-mingw/bin/clang++.exe', 'resources/使用说明.txt', 'resources/build-version.txt',
    'usb/server.py', 'usb/platform-tools/adb.exe', 'usb/platform-tools/AdbWinApi.dll',
    'usb/platform-tools/AdbWinUsbApi.dll', 'usb/platform-tools-lock.json',
    'server/war/WEB-INF/classes/com/google/appinventor/server/OfflineUsbServlet.class',
    'server/war/WEB-INF/web.xml', 'mixly/runtime/resources/app/suite-main.js', 'mixly/src/yuxuan-recovery.js',
    'mixly/src/boards.json', 'mixly/runtime/Mixly.exe', 'mixly/arduino-cli/arduino-cli.exe',
]
LONG_PATHS = [
    'mixly/arduino-cli/Arduino15/packages/arduino/hardware/avr/1.8.6/firmwares/wifishield/wifiHD/src/SOFTWARE_FRAMEWORK/COMPONENTS/WIFI/HD/v2.7.0/UCR1/GCC/lib_ucr1_hd_sdio_v2.7.0.a',
    'mixly/arduino-cli/Arduino15/packages/esp32/tools/xtensa-esp32s3-elf-gcc/esp-2021r2-patch5-8.4.0/xtensa-esp32s3-elf/include/c++/8.4.0/ext/pb_ds/detail/gp_hash_table_map_/constructor_destructor_no_store_hash_fn_imps.hpp',
]

def digest(path):
    value = str(path.absolute())
    if os.name == 'nt' and not value.startswith('\\\\?\\'):
        value = '\\\\?\\UNC\\' + value[2:] if value.startswith('\\\\') else '\\\\?\\' + value
    with open(value, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()

def payload(root, native):
    relative = CRITICAL + LONG_PATHS
    manifest_version = os.environ.get('YUXUAN_ACCEPTANCE_MANIFEST', '2.2.0')
    assert manifest_version in ('2.2.0', '2.3.1')
    relative += [f['path'] for f in json.loads((HERE / ('update-manifest-' + manifest_version + '.json')).read_text(encoding='utf-8'))['files']]
    relative += [p.relative_to(native).as_posix() for p in (native / 'mixly/src').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    relative += [p.relative_to(native).as_posix() for p in (native / 'buildserver/classes').rglob('*.class')]
    relative += ['buildserver/dex-seed/manifest.json', 'buildserver/resource-seed/manifest.json', 'buildserver/resource-seed/manifest.properties']
    dmanifest = json.loads((native / 'buildserver/dex-seed/manifest.json').read_text())
    rmanifest = json.loads((native / 'buildserver/resource-seed/manifest.json').read_text())
    relative += ['buildserver/dex-seed/' + e['file'] for e in dmanifest['entries']]
    relative += ['buildserver/resource-seed/' + e['resource'] for e in rmanifest['entries']]
    files = []
    for name in dict.fromkeys(relative):
        actual = digest(root / name); assert actual == digest(native / name), 'Installed payload differs: ' + name
        files.append({'relative': name, 'sha256': actual, 'characters': len(str(root / name))})
    for name in LONG_PATHS:
        assert len(str(root / name)) > 260, 'Long-path fixture too short'
    assert (root / 'mixly/runtime/Mixly.exe').exists(), 'Desktop runtime missing'
    boards = read_json(root / 'mixly/src/boards.json')
    assert {b['boardIndex'].split('/')[3] for b in boards} == {'arduino_avr', 'arduino_esp32', 'arduino_esp8266', 'micropython_esp32'}
    assert not list(root.glob('AppInventor-*-test.exe')) and not (root / 'LayoutCheck.exe').exists()
    print('PASS installed payload/seeds/class hashes and SDK long paths', flush=True)
    return {'ok': True, 'verifiedFiles': len(files), 'files': files, 'dexSeeds': len(dmanifest['entries']), 'resourceSeeds': len(rmanifest['entries']), 'testExecutablesExcluded': True}

def process_env():
    env = dict(os.environ); env.pop('PYTHONHOME', None); env.pop('PYTHONPATH', None)
    env['PYTHONUTF8'] = '1'; return env

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def core_smoke(root, data):
    result = []; env = process_env()
    unauthorized = data / 'unactivated'
    denied = subprocess.run([str(root / 'AppInventor.exe'), '--headless', '--no-browser', '--data-dir', str(unauthorized)],
                            env=env, capture_output=True, timeout=65, creationflags=FLAGS)
    assert denied.returncode == 4 and not (unauthorized / 'running.ini').exists(), 'Unactivated installed launcher did not reject startup'
    result.append({'test': 'unactivated installed executable', 'ok': True, 'exitCode': denied.returncode})
    print('PASS installed unactivated launcher exits 4', flush=True)
    started = time.monotonic()
    with (HERE / 'installed-core.log').open('wb') as log:
        proc = subprocess.Popen([str(root / 'AppInventor.exe'), '--headless', '--no-browser', '--data-dir', str(data)],
                                env=env, stdout=log, stderr=log, creationflags=FLAGS)
        try:
            browser = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            base = None; deadline = time.monotonic() + 240
            while time.monotonic() < deadline:
                assert proc.poll() is None, 'Installed activated launcher exited before readiness'
                try:
                    config = dict(line.split('=', 1) for line in (data / 'running.ini').read_text(encoding='utf-8-sig').splitlines())
                    address = config['url']
                    with browser.open(address + 'login/_health', timeout=2) as response:
                        if 'AppInventorOffline/1' in response.read().decode():
                            base = address; break
                except (OSError, ValueError, KeyError):
                    time.sleep(.3)
            assert base, 'Installed App Inventor readiness timeout'
            result.append({'test': 'activated Core/AppEngine health', 'ok': True, 'startupSeconds': round(time.monotonic() - started, 3)})
            with browser.open(base + 'login', timeout=5) as response: page = response.read().decode()
            csrf = re.search(r"name='csrf' value='([^']+)'", page)[1]
            request = urllib.request.Request(base + 'login', data=urllib.parse.urlencode({'username': 'Installed220', 'csrf': csrf}).encode())
            with browser.open(request, timeout=10) as response: response.read()
            request = urllib.request.Request(base + 'ode/usb/devices', headers={'X-Offline-Usb': '1'})
            with browser.open(request, timeout=35) as response: devices = json.load(response)
            assert isinstance(devices.get('devices'), list), devices
            result.append({'test': 'installed same-origin authenticated USB enumeration', 'ok': True, 'deviceCount': len(devices['devices']), 'realDeviceInstallTested': False})
            with browser.open('http://127.0.0.1:' + config['buildPort'] + '/buildserver/health', timeout=5) as response:
                assert response.status == 200
            result.append({'test': 'installed managed BuildServer health', 'ok': True})
            print('PASS installed Core/BuildServer/USB health and authenticated device enumeration', flush=True)
        finally:
            deadline = time.monotonic() + 90
            while proc.poll() is None and time.monotonic() < deadline:
                (data / 'stop.request').write_text('')
                with contextlib.suppress(subprocess.TimeoutExpired): proc.wait(timeout=1)
            if proc.poll() is None:
                # Kill only this owned launcher tree, preserving other installed applications.
                subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, creationflags=FLAGS)
                proc.wait(timeout=15); raise AssertionError('Installed launcher did not shut down gracefully')
    assert proc.returncode == 0 and not (data / 'running.ini').exists(), 'Installed Core shutdown failed'
    result.append({'test': 'installed activated launcher graceful stop', 'ok': True, 'exitCode': proc.returncode})
    return result

def studio_smoke(root, data, preservation=False):
    folder = data / 'studio'; token = secrets.token_urlsafe(32); env = process_env(); tests = []
    with (HERE / ('installed-studio-preservation.log' if preservation else 'installed-studio.log')).open('wb') as log:
        proc = subprocess.Popen([str(root / 'runtime/python3.13.16/python.exe'), '-X', 'utf8', str(root / 'studio/server.py'),
                                 '--data', str(folder), '--token', token], env=env, stdout=log, stderr=log, creationflags=FLAGS)
        api = None
        try:
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline:
                assert proc.poll() is None, 'Installed Studio server exited'
                try:
                    port = read_json(folder / 'studio-running.json')['port']; break
                except (OSError, ValueError): time.sleep(.2)
            else: raise AssertionError('Installed Studio startup timeout')
            http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            def api(route, body=None):
                req = urllib.request.Request('http://127.0.0.1:' + str(port) + '/api/' + route,
                                             data=json.dumps(body).encode() if body is not None else None,
                                             headers={'X-Studio-Token': token, 'Content-Type': 'application/json'})
                with http.open(req, timeout=35) as response: return json.load(response)
            def job(body, route='run', timeout=120):
                jid = api(route, body)['id']; started = time.monotonic()
                while time.monotonic() - started < timeout:
                    status = api('job?id=' + jid)
                    if not status['running']:
                        assert status['code'] == 0, status['output']; return status, round(time.monotonic() - started, 3)
                    time.sleep(.05)
                api('stop', {'id': jid}); raise AssertionError('Installed Studio job timed out')
            state = api('state'); py = next(p for p in state['projects'] if p['mode'] == 'python'); cpp = next(p for p in state['projects'] if p['mode'] == 'cpp')
            if preservation:
                status, seconds = job({'project': py['id'], 'path': 'preserved.py', 'version': '3.8.9'})
                assert 'PRESERVED 0.4.6 custom dependency' in status['output']
                tests.append({'test': 'reinstalled 3.8 project/custom dependencies still import', 'ok': True, 'seconds': seconds})
                return tests
            for version in ('3.8.9', '3.13.16'):
                for run in range(2):
                    status, seconds = job({'project': py['id'], 'path': 'main.py', 'version': version})
                    assert version in status['output']
                    tests.append({'test': 'fresh environment/run ' + version if run == 0 else 'repeated run ' + version, 'ok': True, 'seconds': seconds})
                source = '''import tkinter as tk
import turtle
import pygame
r=tk.Tk();r.title("安装验收");r.update();print("TK_VISIBLE",r.winfo_viewable());r.destroy()
s=turtle.Screen();t=turtle.Turtle();t.forward(20);s.update();print("TURTLE_VISIBLE",s.getcanvas().winfo_viewable());turtle.bye()
pygame.init();pygame.display.set_mode((200,120));pygame.display.flip();pygame.event.pump();print("PYGAME_VISIBLE",int(pygame.display.get_init()));pygame.quit()
'''
                path = 'graphics-' + version + '.py'
                api('file/save', {'project': py['id'], 'path': path, 'text': source})
                status, seconds = job({'project': py['id'], 'path': path, 'version': version})
                assert all(text in status['output'] for text in ('TK_VISIBLE 1', 'TURTLE_VISIBLE 1', 'PYGAME_VISIBLE 1'))
                tests.append({'test': 'installed Tkinter/Turtle/Pygame native windows ' + version, 'ok': True, 'seconds': seconds})
            for run in range(2):
                status, seconds = job({'project': cpp['id'], 'path': 'main.cpp'})
                assert 'Hello, Yuxuan' in status['output']
                if run: assert '使用已编译程序' in status['output']
                tests.append({'test': 'fresh C++ compile/run' if run == 0 else 'C++ unchanged dependency cache run', 'ok': True, 'seconds': seconds})
            package = api('package?name=colorama'); assert package['name'].lower() == 'colorama'
            tests.append({'test': 'installed verified HTTPS package search', 'ok': True})
            status, seconds = job({'project': py['id'], 'version': '3.8.9', 'package': 'colorama==0.4.6'}, 'package/install', 180)
            assert 'pypi.tuna.tsinghua.edu.cn' in status['output']
            tests.append({'test': 'installed Python3.8 pip HTTPS via Tsinghua', 'ok': True, 'seconds': seconds})
            status, seconds = job({'project': py['id'], 'version': '3.13.16', 'package': 'colorama==0.4.6'}, 'package/install', 180)
            assert 'pypi.tuna.tsinghua.edu.cn' in status['output']
            tests.append({'test': 'installed Python3.13 pip HTTPS via Tsinghua', 'ok': True, 'seconds': seconds})
            site = folder / 'environments' / py['id'] / '3.8.9/Lib/site-packages'
            (site / 'acceptance_custom.py').write_text('VALUE="custom dependency"\n', encoding='utf-8')
            api('file/save', {'project': py['id'], 'path': 'preserved.py', 'text': 'import colorama,acceptance_custom\nprint("PRESERVED",colorama.__version__,acceptance_custom.VALUE)\n'})
            status, seconds = job({'project': py['id'], 'path': 'preserved.py', 'version': '3.8.9'})
            assert 'PRESERVED 0.4.6 custom dependency' in status['output']
            tests.append({'test': 'project dependency prepared for reinstall preservation', 'ok': True})
            for relative in ('mixly/projects/retained-marker.txt', 'mixly/custom-libraries/retained-marker.txt'):
                target = data / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_text('retained offline project/library', encoding='utf-8')
            print('PASS installed Python/C++ speed, six GUI libraries and verified HTTPS pip', flush=True)
        finally:
            if api is not None:
                with contextlib.suppress(Exception): api('shutdown', {})
            with contextlib.suppress(subprocess.TimeoutExpired): proc.wait(timeout=20)
            if proc.poll() is None:
                subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, creationflags=FLAGS)
                proc.wait(timeout=10); raise AssertionError('Installed Studio shutdown failed')
    assert proc.returncode == 0
    return tests

def mixly_smoke(root, data, preservation=False):
    if preservation:
        assert (data / 'mixly/projects/retained.mix').is_file()
        for relative,expected in read_json(data/'desktop-library-hashes.json').items():assert digest(data/relative)==expected,'Installed cloud library changed: '+relative
        return [{'test':'desktop user data retained after repeat update','ok':True}]
    output = data / 'mixly-functional'; output.mkdir(parents=True,exist_ok=True)
    command=['powershell.exe','-NoProfile','-File',str(HERE/'run-desktop-smoke.ps1'),'-NativeRoot',str(root),'-DataRoot',str(data/'mixly'),'-OutputRoot',str(output)]
    run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=900,creationflags=FLAGS)
    (HERE/'installed-desktop.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    assert run.returncode==0,'Installed desktop checks failed: '+run.stderr[-1000:]
    result=read_json(output/'desktop-smoke.json');assert result['ok']
    regression=data/'mixly-regression'
    command=['powershell.exe','-NoProfile','-File',str(HERE/'run-desktop-regression.ps1'),'-NativeRoot',str(root),'-OutputRoot',str(regression)]
    check=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300,creationflags=FLAGS)
    (HERE/'installed-desktop-regression.log').write_text(check.stdout+'\n'+check.stderr,encoding='utf-8')
    assert check.returncode==0,'Installed desktop persistence or close button regression failed'
    assert read_json(regression/'result.json')['ok'] and read_json(regression/'restart-result.json')['ok']

    for relative in ('mixly/projects/retained.mix','mixly/custom-libraries/retained/library.txt'):
        target=data/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('User data retained by the desktop upgrade',encoding='utf-8')
    hashes={p.relative_to(data).as_posix():digest(p) for p in (data/'mixly/src/boards/default/arduino_avr/libraries/ThirdParty').rglob('*') if p.is_file()}
    assert hashes,'Cloud installation produced no library files'
    (data/'desktop-library-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print('PASS installed desktop four boards/cloud catalogs/native compile/Bluetooth/serial',flush=True)
    return [{'test':'desktop functional acceptance','ok':True,'report':result}]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=('payload', 'smoke', 'preservation'))
    parser.add_argument('--installed', type=pathlib.Path, required=True); parser.add_argument('--native', type=pathlib.Path, required=True)
    parser.add_argument('--data', type=pathlib.Path, required=True); parser.add_argument('--report', type=pathlib.Path, required=True)
    options = parser.parse_args(); result = {'ok': False}
    try:
        root = options.installed.absolute(); data = options.data.absolute()
        if options.mode == 'payload': result = payload(root, options.native.resolve())
        else:
            tests = [] if options.mode == 'preservation' else core_smoke(root, data)
            tests.extend(studio_smoke(root, data, options.mode == 'preservation'))
            tests.extend(mixly_smoke(root, data, options.mode == 'preservation'))
            result = {'ok': True, 'existingGrantCopiedWithoutActivation': True, 'tests': tests}
    except Exception as error:
        result = {'ok': False, 'failure': str(error)}; raise
    finally:
        options.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
