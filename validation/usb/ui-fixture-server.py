"""Development-only USB phone fixture; production fetch/manifest and UI stay real.

Installed only into an isolated clone by prepare-ui-fixture.ps1. No ADB
subprocess is ever invoked. The real activation gate is not replaced.
"""
import sys
sys.dont_write_bytecode = True

import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import threading

PHONE = 'FixtureUsbPhone'
PID = '8172'
CONFIG = Path(__file__).resolve().parent.parent / 'ui-fixture.json'


def configuration():
    settings = json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    if settings.get('kind') != 'development-usb-ui-fixture':
        raise SystemExit('UI fixture configuration missing or invalid.')
    native = Path(settings['productionRoot']).resolve()
    clone = CONFIG.parent.resolve()
    if clone == native or native in clone.parents:
        raise SystemExit('UI fixture must live outside the production payload.')
    return settings, native


def license_main(native):
    # Run exactly the production gate and vendor modules, with source imports
    # unable to create bytecode files through the shared native directories.
    sys.path.insert(0, str(native / 'license'))
    runpy.run_path(str(native / 'license/gate.py'), run_name='__main__')


class FixtureRunner:
    def __init__(self, module, data):
        self.module = module
        self.data = Path(data).resolve()
        self.target = self.data / 'usb-ui-fixture-events.json'
        self.lock = threading.RLock()
        self.installed = {}
        self.events = {'fixture': True, 'physicalPhoneUsed': False,
                       'description': '模拟手机：真实 AppEngine APK 下载与清单解析，ADB 操作使用开发 fixture。',
                       'commands': [], 'apks': []}
        self.persist()

    def persist(self):
        temporary = self.target.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.events, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temporary.replace(self.target)

    def __call__(self, argv, timeout=15):
        argv = list(argv)
        with self.lock:
            self.events['commands'].append({'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                            'argv': argv, 'timeout': timeout})
            self.events['commands'] = self.events['commands'][-500:]
            try:
                if argv == ['devices', '-l']:
                    return ('List of devices attached\n' + PHONE
                            + ' device usb:fixture model:模拟手机_仅用于界面验收 transport_id:1')
                if argv[:2] != ['-s', PHONE]:
                    raise self.module.BridgeError('模拟 USB 设备拒绝未知设备。', 400)
                if len(argv) == 5 and argv[2:4] == ['install', '-r']:
                    apk = Path(argv[4]).resolve()
                    if not apk.is_relative_to(self.data) or not apk.name.startswith('deploy-') or apk.suffix != '.apk':
                        raise self.module.BridgeError('模拟 USB 安装只接受真实下载的受管 APK。', 400)
                    package, activity = self.module.apk_identity(apk)
                    self.installed[package] = activity
                    self.events['apks'].append({'file': apk.name, 'bytes': apk.stat().st_size,
                                               'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
                                               'package': package, 'activity': activity,
                                               'source': 'Real local AppEngine project-output APK',
                                               'simulatedInstallation': True})
                    return 'Performing simulated USB install (development fixture only)\nSuccess'
                if len(argv) == 9 and argv[2:8] == ['shell', 'am', 'start', '-W', '-S', '-n']:
                    component = argv[8]
                    if '/' not in component:
                        raise self.module.BridgeError('模拟启动缺少 APK Activity。', 400)
                    package, activity = component.split('/', 1)
                    if self.installed.get(package) != activity:
                        raise self.module.BridgeError('模拟启动目标与真实下载的 APK 不一致。', 400)
                    return ('Starting: Intent { cmp=' + component + ' }\n'
                            'Status: ok\nActivity: ' + component + '\nTotalTime: 120\nComplete')
                if len(argv) == 5 and argv[2:4] == ['shell', 'pidof'] and argv[4] in self.installed:
                    return PID
                if argv[2:] == ['logcat', '--pid=' + PID, '-d', '-t', '250', '-v', 'threadtime']:
                    return ('10-04 18:00:00.000  8172  8172 I FixtureApp: 模拟 USB 设备应用已启动\n'
                            '10-04 18:00:00.100  8172  8172 I FixtureApp: 真实 APK 构建、下载、清单解析通过；本行来自开发 fixture')
                raise self.module.BridgeError('模拟 USB 设备不支持此操作，不会调用真实 ADB。', 400)
            finally:
                # No request object, Cookie, startup token or license data enters this file.
                self.persist()


def usb_main(native):
    specification = importlib.util.spec_from_file_location('yuxuan_production_usb', native / 'usb/server.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    production_bridge = module.Bridge

    class FixtureBridge(production_bridge):
        def __init__(self, data, app_port, runner=None, fetcher=None, adb=None):
            if runner is not None or fetcher is not None:
                raise RuntimeError('UI fixture expects untouched production fetch and its own runner.')
            # Production main creates the userdata directory in Bridge.__init__.
            Path(data).mkdir(parents=True, exist_ok=True)
            fixture_runner = FixtureRunner(module, data)
            super().__init__(data, app_port, runner=fixture_runner, adb=adb)
    module.Bridge = FixtureBridge
    print('Development USB UI fixture: simulated phone; real local APK download/manifest.', flush=True)
    module.main()


if __name__ == '__main__':
    settings, native = configuration()
    if '--fixture-license-gate' in sys.argv:
        sys.argv.remove('--fixture-license-gate')
        license_main(native)
    else:
        usb_main(native)
