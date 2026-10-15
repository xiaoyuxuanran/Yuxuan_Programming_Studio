"""Final installed payload/launcher acceptance. No activation requests or project edits.

The launch checks copy the existing same-machine DPAPI grant into a fresh workspace
fixture. The earlier 203 retained license/project/library files stay unchanged.
"""
import argparse
import ctypes
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import time
import urllib.request
import uuid

HERE = pathlib.Path(__file__).resolve().parent
CRITICAL = [
    'AppInventor.exe', 'AppInventorCore.exe', 'license/gate.py', 'license/license_client.py',
    'license/vendor/_cffi_backend.cp313-win_amd64.pyd', 'studio/server.py', 'studio/studio.js',
    'studio/studio.css', 'studio/index.html', 'studio/vs/loader.js',
    'runtime/python3.8.9/python.exe', 'runtime/python3.13.16/python.exe',
    'runtime/python3.8.9/DLLs/_tkinter.pyd', 'runtime/python3.13.16/DLLs/_tkinter.pyd',
    'runtime/llvm-mingw/bin/clang++.exe', 'resources/使用说明.txt', 'mixly/runtime/Mixly.exe',
    'mixly/runtime/resources/app/main.js', 'mixly/runtime/resources/app/suite-main.js',
    'mixly/runtime/resources/app/compiler-paths.py', 'mixly/src/boards.json',
    'mixly/src/yuxuan-recovery.js', 'mixly/src/yuxuan-home.js', 'mixly/arduino-cli/arduino-cli.exe',
]
LONG_PATHS = [
    'mixly/arduino-cli/Arduino15/packages/arduino/hardware/avr/1.8.6/firmwares/wifishield/wifiHD/src/SOFTWARE_FRAMEWORK/COMPONENTS/WIFI/HD/v2.7.0/UCR1/GCC/lib_ucr1_hd_sdio_v2.7.0.a',
    'mixly/arduino-cli/Arduino15/packages/esp32/tools/xtensa-esp32s3-elf-gcc/esp-2021r2-patch5-8.4.0/xtensa-esp32s3-elf/include/c++/8.4.0/ext/pb_ds/detail/gp_hash_table_map_/constructor_destructor_no_store_hash_fn_imps.hpp',
]


def digest(path):
    # Explicit Win32 extended paths also work when the host has LongPathsEnabled disabled.
    value = str(path.absolute())
    if os.name == 'nt' and not value.startswith('\\\\?\\'):
        value = '\\\\?\\UNC\\' + value[2:] if value.startswith('\\\\') else '\\\\?\\' + value
    with open(value, 'rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest().upper()


def payload(root, native):
    files = []
    for relative in CRITICAL + LONG_PATHS:
        installed = root / relative
        expected = digest(native / relative)
        actual = digest(installed)
        assert actual == expected, f'Final installed file mismatch: {relative}'
        long_path = relative in LONG_PATHS
        if long_path:
            assert len(str(installed)) > 260, f'Long-path fixture too short: {installed}'
        files.append({'relative': relative, 'ok': True, 'sha256': actual, 'characters': len(str(installed)), 'longPath': long_path})
    for base in (root, native):
        main = (base / 'mixly/runtime/resources/app/main.js').read_text(encoding='utf-8-sig')
        assert 'YUXUAN_MIXLY_SELFTEST' not in main and 'integration-test.js' not in main, f'Test hook present: {base}'
    excluded = list(root.glob('AppInventor-2.1-*.exe')) + list(root.glob('LayoutCheck.exe'))
    assert not excluded, f'Development executable shipped: {excluded}'
    print('PASS 24 critical installed hashes, two paths above 260 characters and no test entry', flush=True)
    return {'ok': True, 'criticalFileCount': len(CRITICAL), 'longPathCount': len(LONG_PATHS), 'files': files,
            'nativeAndInstalledMainHaveNoTestHook': True, 'developmentExecutablesExcluded': True}


def terminate_owned_core(root, data):
    """Failure cleanup only: kill Core only when the fresh fixture's PID and image match."""
    try:
        pid = next(int(line[12:]) for line in (data / 'running.ini').read_text(encoding='utf-8-sig').splitlines() if line.startswith('launcherPid='))
    except (OSError, ValueError, StopIteration):
        return False
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_uint]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint)]
    kernel.QueryFullProcessImageNameW.restype = ctypes.c_int
    kernel.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    kernel.TerminateProcess.restype = ctypes.c_int
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = ctypes.c_int
    handle = kernel.OpenProcess(0x1000 | 0x0001, 0, pid)
    if not handle:
        return False
    try:
        size = ctypes.c_uint(32768)
        image = ctypes.create_unicode_buffer(size.value)
        if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
            return False
        if os.path.normcase(os.path.abspath(image.value)) != os.path.normcase(str(root / 'AppInventorCore.exe')):
            return False
        return bool(kernel.TerminateProcess(handle, 1))
    finally:
        kernel.CloseHandle(handle)


def smoke(root, existing_data):
    fixture = HERE / ('final-smoke-' + uuid.uuid4().hex[:8])
    unauthorized = fixture / 'unactivated'
    authorized = fixture / 'activated'
    unauthorized.mkdir(parents=True)
    (authorized / 'license').mkdir(parents=True)
    shutil.copyfile(existing_data / 'license/device-license.bin', authorized / 'license/device-license.bin')
    env = dict(os.environ)
    env.pop('PYTHONHOME', None)
    env.pop('PYTHONPATH', None)
    flags = subprocess.CREATE_NO_WINDOW
    tests = []
    http = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    denied = subprocess.run([str(root / 'AppInventor.exe'), '--headless', '--no-browser', '--data-dir', str(unauthorized)],
                            env=env, capture_output=True, timeout=65, creationflags=flags)
    assert denied.returncode == 4, f'Unactivated final installation exit code: {denied.returncode}'
    assert not (unauthorized / 'running.ini').exists(), 'Unactivated launcher started Core'
    tests.append({'test': 'unactivated installed executable rejects startup', 'ok': True, 'exitCode': denied.returncode})
    print('PASS actual unactivated installed AppInventor.exe exits 4', flush=True)

    # New fixture prevents stale running.ini from making a dead Core look healthy.
    ready_url = None
    started = time.monotonic()
    with (fixture / 'launcher.log').open('wb') as log:
        process = subprocess.Popen([str(root / 'AppInventor.exe'), '--headless', '--no-browser', '--data-dir', str(authorized)],
                                   env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        try:
            deadline = time.monotonic() + 240
            while time.monotonic() < deadline:
                code = process.poll()
                if code is not None:
                    raise AssertionError(f'Authorized installed launcher exited before readiness: {code}')
                try:
                    lines = (authorized / 'running.ini').read_text(encoding='utf-8-sig').splitlines()
                    url = next(line[4:] for line in lines if line.startswith('url='))
                    with http.open(url.rstrip('/') + '/login/_health', timeout=3) as response:
                        body = response.read(4096).decode('utf-8')
                    if 'AppInventorOffline/1' in body:
                        ready_url = url
                        break
                except (OSError, StopIteration, ValueError):
                    pass
                time.sleep(0.3)
            if not ready_url:
                raise AssertionError('Authorized installed App Inventor did not become healthy within 240 seconds')
            tests.append({'test': 'activated installed executable starts healthy App Inventor', 'ok': True,
                          'url': ready_url, 'startupSeconds': round(time.monotonic() - started, 3)})
            print('PASS actual activated installed App Inventor health endpoint', flush=True)
        finally:
            # Repeat the request because Core clears stale requests during its initialization.
            deadline = time.monotonic() + 90
            while process.poll() is None and time.monotonic() < deadline:
                (authorized / 'stop.request').write_text('', encoding='utf-8')
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
            if process.poll() is None:
                terminate_owned_core(root, authorized)
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=8)
                raise AssertionError('Authorized installed launcher failed to shut down gracefully')
    assert process.returncode == 0, f'Authorized installed launcher shutdown code: {process.returncode}'
    assert not (authorized / 'running.ini').exists(), 'Core running state was not cleared after shutdown'
    tests.append({'test': 'activated installed executable saves and stops', 'ok': True, 'exitCode': process.returncode})
    print('PASS installed App Inventor graceful shutdown exits 0', flush=True)
    return {'ok': True, 'fixture': str(fixture), 'existingGrantCopiedWithoutActivation': True, 'tests': tests}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['payload', 'smoke'])
    parser.add_argument('--installed', required=True, type=pathlib.Path)
    parser.add_argument('--native', type=pathlib.Path)
    parser.add_argument('--data', type=pathlib.Path)
    parser.add_argument('--report', required=True, type=pathlib.Path)
    args = parser.parse_args()
    result = {'ok': False}
    try:
        root = args.installed.resolve()
        if args.mode == 'payload':
            assert args.native is not None, '--native is required for payload checks'
            result = payload(root, args.native.resolve())
        else:
            assert args.data is not None, '--data is required for launcher checks'
            result = smoke(root, args.data.resolve())
    except Exception as error:
        result = {'ok': False, 'failure': str(error)}
        raise
    finally:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
