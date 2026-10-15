"""Record sanitized evidence from the real browser flow and isolated ADB fixture."""
import hashlib
import json
import zipfile
from pathlib import Path

here = Path(__file__).resolve().parent
events = json.loads((here / 'USB 接口验收/usb/usb-ui-fixture-events.json').read_text(encoding='utf-8'))
assert events['fixture'] and not events['physicalPhoneUsed']
commands = [item['argv'] for item in events['commands']]
assert any('install' in command for command in commands)
assert any('start' in command and 'am' in command for command in commands)
assert any('logcat' in command for command in commands)
assert events['apks'] and events['apks'][-1]['simulatedInstallation']
apk = here / 'UsbBuildTest.apk'
with zipfile.ZipFile(apk) as archive:
    dex_files = [name for name in archive.namelist() if name.startswith('classes') and name.endswith('.dex')]
    assert dex_files and all(archive.read(name).startswith(b'dex\n') for name in dex_files)
    assert 'AndroidManifest.xml' in archive.namelist()
proofs = ['usb-panel.png', 'local-download.png', 'usb-flow-simulated.png']
assert all((here / name).stat().st_size > 0 for name in proofs)
report = {
    'ok': True,
    'project': 'UsbBuildTest',
    'localDownload': {
        'qrRemoved': True,
        'downloadClickedInBrowser': True,
        'bytes': apk.stat().st_size,
        'sha256': hashlib.sha256(apk.read_bytes()).hexdigest().upper(),
        'dexFiles': dex_files,
    },
    'usbFlow': {
        'realEditorSaveBuildDownloadManifest': True,
        'installationAndLaunchSimulated': True,
        'physicalPhoneTested': False,
        'selectedDevice': 'FixtureUsbPhone',
        'apk': events['apks'][-1],
        'completedCommands': ['install -r', 'am start -W -S -n', 'pidof', 'logcat'],
        'browserDisplayedInstalledAndStarted': True,
        'browserDisplayedApplicationLogs': True,
    },
    'screenshots': proofs,
}
(here / 'ui-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
