"""Run real, isolated local APK builds and preserve task timings, never user projects."""
import argparse, contextlib, ctypes, hashlib, io, json, os, pathlib, re, socket, subprocess, time, urllib.request, zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / 'native'

def fixture(min_api=14):
    with zipfile.ZipFile(ROOT / 'examples/HelloOfflineTest.aia') as src:
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            for name in src.namelist():
                content = src.read(name)
                if name == 'youngandroidproject/project.properties':
                    content = content.replace(b'androidminsdk=14', ('androidminsdk=' + str(min_api)).encode())
                z.writestr(name, content)
            z.writestr('src/appinventor/ai_offline/HelloOfflineTest/Screen1.yail', '''#| $Source $Yail |#
(define-form appinventor.ai_offline.HelloOfflineTest.Screen1 Screen1)
(require <com.google.youngandroid.runtime>)
(do-after-form-creation (set-and-coerce-property! 'Screen1 'AppName "HelloOfflineTest" 'text)
 (set-and-coerce-property! 'Screen1 'Title "APK speed test" 'text))
(init-runtime)
''')
        return out.getvalue()

def run(name, classes, seed, count, resource_seed=None, min_api=14):
    data = HERE / name
    data.mkdir(parents=True, exist_ok=False)
    for sub in ('temp', 'cache'):
        (data / sub).mkdir()
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    alias = None
    alias_target = '\\??\\' + str(data)
    for letter in 'ZYXWVUTSRQP':
        drive = letter + ':'
        found = ctypes.create_unicode_buffer(32768)
        if kernel.QueryDosDeviceW(drive, found, len(found)) == 0 and ctypes.get_last_error() == 2:
            if kernel.DefineDosDeviceW(0x1 | 0x8, drive, alias_target):
                alias = drive
                break
    if alias is None:
        raise RuntimeError('No unused private DOS drive for legacy Android tools')
    build_data = pathlib.Path(alias + '\\')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    token = os.urandom(32).hex()
    args = [str(ROOT / 'runtime/java11/bin/java.exe'), '-Xmx3g', '-Djava.net.preferIPv4Stack=true',
            '-Dfile.encoding=UTF-8', '-Dkeystore.pkcs12.legacy=true', '-Djava.awt.headless=true',
            '-Djava.io.tmpdir=' + str(build_data / 'temp')]
    if seed:
        args.append('-Dappinventor.dexSeedDir=' + str(pathlib.Path(seed).resolve()))
    if resource_seed:
        args.append('-Dappinventor.resourceSeedDir=' + str(pathlib.Path(resource_seed).resolve()))
    args += ['-cp', str(pathlib.Path(classes).resolve()) + ';' + str(ROOT / 'buildserver/lib/*'),
             'com.google.appinventor.buildserver.BuildServer', '--port', str(port), '--dexCacheDir',
             str(build_data / 'cache'), '--debug', '--buildserverPassword', token, '--requiredHosts', 'localhost']
    result = {'name': name, 'seed': bool(seed), 'minApi': min_api, 'builds': []}
    with (data / 'server.log').open('wb') as log:
        proc = subprocess.Popen(args, cwd=ROOT / 'buildserver/lib', stdout=log, stderr=log, creationflags=0x08000000)
        try:
            started = time.perf_counter()
            base = 'http://127.0.0.1:' + str(port) + '/buildserver/'
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            while time.perf_counter() - started < 90:
                if proc.poll() is not None:
                    raise RuntimeError('Build Server exited; see ' + str(data / 'server.log'))
                try:
                    with opener.open(base + 'health', timeout=1) as response:
                        if response.status == 200:
                            break
                except Exception:
                    time.sleep(0.2)
            else:
                raise TimeoutError('Build server health timeout')
            result['startupSeconds'] = round(time.perf_counter() - started, 3)
            for index in range(count):
                started = time.perf_counter()
                request = urllib.request.Request(base + 'build-all-from-zip?uname=speedtest&ext=apk',
                                                  data=fixture(min_api), headers={'Authorization': 'Password ' + token, 'Content-Type': 'application/zip'})
                with opener.open(request, timeout=1500) as response:
                    content = response.read()
                elapsed = round(time.perf_counter() - started, 3)
                (data / ('build-' + str(index) + '.zip')).write_bytes(content)
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    status = json.loads(z.read('build.out'))
                    apks = [x for x in z.namelist() if x.endswith('.apk')]
                    record = {'seconds': elapsed, 'status': status['result'], 'apks': apks,
                              'taskTimings': re.findall(r'\[([^]]+)\] Task succeeded in ([\d.]+) seconds', status['output']),
                              'seedHits': status['output'].count('Using bundled pre-dexed'),
                              'cacheHits': status['output'].count('Using pre-dexed')}
                    if apks:
                        apk = z.read(apks[0]); record['apkBytes'] = len(apk); record['apkSha256'] = hashlib.sha256(apk).hexdigest()
                        with zipfile.ZipFile(io.BytesIO(apk)) as a:
                            record['dexMembers'] = [x for x in a.namelist() if x.endswith('.dex')]
                    else:
                        record['error'] = status['error']; record['outputTail'] = status['output'][-2500:]
                result['builds'].append(record)
                (data / 'measurements.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
                print(json.dumps(record, ensure_ascii=False), flush=True)
        finally:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.wait(timeout=30)
            kernel.DefineDosDeviceW(0x1 | 0x2 | 0x4 | 0x8, alias, alias_target)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('name'); parser.add_argument('--classes', default=str(HERE / 'baseline-classes'))
    parser.add_argument('--native-root', type=pathlib.Path, default=ROOT)
    parser.add_argument('--seed'); parser.add_argument('--count', type=int, default=2)
    parser.add_argument('--resource-seed')
    parser.add_argument('--min-api', type=int, default=14)
    args = parser.parse_args()
    ROOT = args.native_root.resolve()
    run(args.name, args.classes, args.seed, args.count, args.resource_seed, args.min_api)
