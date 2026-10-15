"""Combine the audited 2.2 source delivery with the reproducible Mixly4 migration."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RELEASE = ROOT / 'work/release-2.3'
TARGET = RELEASE / '适配源码与补丁.zip'
BASELINE = ROOT / 'work/release-2.2/package/适配源码与补丁.zip'
if not BASELINE.is_file():
    BASELINE = ROOT / 'outputs/适配源码与补丁.zip'
assert hashlib.file_digest(BASELINE.open('rb'), 'sha256').hexdigest().upper() == '77D523685D3B71602042A3B21F4AB83DE8B9047F86C57A15C029ECE5F42A1F01'
OWN = ('arduino-shell.js', 'cloud.py', 'server.py', 'compiler-paths.py', 'toolchain_paths.py', 'sdk-junction.ps1', 'editor-theme.css', 'index.html', 'workbench.css', 'workbench.js', 'prepare-build.py', 'stage-web.py', 'build-web.ps1', 'build-installer.ps1', 'prepare-release.py', 'package-source.py', 'publish-release.py', 'UPSTREAM.json', 'RELEASE.md')
TESTS = ('verify-web.cjs', 'verify-native.py', 'verify-interactions.cjs', 'verify-layout.cjs', 'verify-serial.cjs', 'serial-fixture.py', 'verify-paths.py', 'LauncherCheck.cs')
TESTS += ('verify-physical-paths.py',)
REPORTS = ('web-verification.json', 'native-verification.json', 'default-options-verification.json', 'interaction-verification.json', 'cloud-compile-verification.json', 'layout-verification.json', 'serial-verification.json', 'path-verification.json', 'stage-result.json')
REPORTS += ('physical-path-verification.json',)
inputs = {}
inputs['validation-results/mixly4/launcher-layout.json'] = HERE / 'launcher-layout/layout.json'
inputs['validation-results/mixly4/launcher-service.json'] = HERE / '启动器 验收/launcher-result.json'
for name in OWN:
    inputs['distribution-source/mixly4/' + name] = HERE / name
for name in ('SuiteLauncher.cs', 'SuiteLicense.cs', 'Setup.iss'):
    inputs['distribution-source/' + name] = ROOT / 'work' / name
for name in TESTS:
    inputs['validation/mixly4/' + name] = HERE / name
for name in REPORTS:
    inputs['validation-results/mixly4/' + name] = HERE / name
for name in ('install-acceptance.ps1', 'installed-smoke.py', 'install-acceptance.json', 'installed-payload.json', 'installed-smoke.json', 'installed-reinstall-smoke.json'):
    inputs['validation/release-2.3/' + name] = RELEASE / name
for path in (HERE / 'upstream').rglob('*'):
    relative = path.relative_to(HERE / 'upstream')
    if not path.is_file() or any(part in ('.git', 'node_modules', '__pycache__') for part in relative.parts):
        continue
    if relative.parts[:2] == ('static-server', 'certs') or path.suffix in ('.log', '.key', '.pem'):
        continue
    # Board output is reproducible from default_src and is shipped in the installer.
    if relative.parts[:2] == ('boards', 'default'):
        continue
    inputs['Mixly4-web-upstream/' + relative.as_posix()] = path
inputs['使用说明.txt'] = RELEASE / 'docs/使用说明.txt'
inputs['Mixly网页版迁移说明.md'] = HERE / 'RELEASE.md'
for name, path in inputs.items():
    assert path.is_file(), 'Missing final source/evidence: ' + name

manifest = {'version': '2.3.0', 'upstream': json.loads((HERE / 'UPSTREAM.json').read_text()), 'files': [], 'verifiedUpstreamFirmware': [], 'baselineSHA256': '77D523685D3B71602042A3B21F4AB83DE8B9047F86C57A15C029ECE5F42A1F01'}
with zipfile.ZipFile(BASELINE) as baseline, zipfile.ZipFile(TARGET, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for member in baseline.infolist():
        if member.is_dir():
            continue
        name = member.filename
        if name in inputs:
            continue
        # Keep prior audit results and instructions as an explicitly historical baseline.
        if '/' not in name:
            name = 'legacy-2.2/' + name
        archive.writestr(name, baseline.read(member))
    for name, path in sorted(inputs.items()):
        assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts
        raw = path.read_bytes()
        assert not re.search(rb'YX-[0-9A-F]{8}(?:-[0-9A-F]{8}){3}', raw), 'Activation code in ' + name
        if re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]+[A-Za-z0-9+/\r\n]{64,}', raw):
            # Official firmware embeds TLS test material. Accept only an exact,
            # immutable upstream firmware blob; never accept generated key files.
            assert name.startswith('Mixly4-web-upstream/') and path.suffix == '.bin', 'Private key in ' + name
            relative = path.relative_to(HERE / 'upstream').as_posix()
            pin = '7241435d8bd50543f884e8ff9cb67956cf8e3652' if relative.startswith(('boards/default_src/arduino_esp32/', 'boards/default_src/arduino_esp8266/')) else 'd1141e0fd73255f8705983d2252e8b049119dac1'
            assert raw == subprocess.check_output(['git', '-C', str(HERE / 'upstream'), 'show', pin + ':' + relative]), 'Modified firmware key material: ' + name
            manifest['verifiedUpstreamFirmware'].append(name)
        archive.writestr(name, raw)
        manifest['files'].append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest()})
    archive.writestr('SOURCE-MANIFEST-2.3.json', json.dumps(manifest, ensure_ascii=False, indent=2))
with zipfile.ZipFile(TARGET) as archive:
    assert archive.testzip() is None
    for entry in manifest['files']:
        assert hashlib.sha256(archive.read(entry['path'])).hexdigest() == entry['sha256']
report = {'ok': True, 'version': '2.3.0', 'auditedNewFiles': len(inputs), 'bytes': TARGET.stat().st_size,
          'sha256': hashlib.file_digest(TARGET.open('rb'), 'sha256').hexdigest().upper()}
(RELEASE / 'source-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
