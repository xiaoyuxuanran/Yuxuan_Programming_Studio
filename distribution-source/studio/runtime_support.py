"""Fast offline environment seeding and verified HTTPS using Windows trust."""
from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path, PurePosixPath
import ssl
import threading
import time
import zipfile

_TLS_LOCK = threading.Lock()
_TLS_CONTEXT = None
_TLS_CREATED = 0.0
_CA_CREATED = {}


def seed_wheel(wheel: Path, target: Path, version: str):
    """Install our bundled wheels without starting pip or compiling bytecode.

    The private runtimes and wheels are shipped together. Wheel .data entries
    and RECORD paths follow the venv installation scheme so pip can later
    upgrade/uninstall the seeded package normally.
    """
    site = target / 'Lib/site-packages'
    major_minor = '.'.join(version.split('.')[:2])
    rows = []
    dist_info = None
    with zipfile.ZipFile(wheel) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            parts = PurePosixPath(member.filename).parts
            if not parts or any(part in {'..', '.'} or ':' in part or '\\' in part for part in parts):
                raise ValueError('内置环境包包含无效路径')
            if parts[0].endswith('.data'):
                if len(parts) < 3:
                    raise ValueError('内置环境包安装目录无效')
                scheme = parts[1]
                package = parts[0].split('-', 1)[0]
                folders = {'purelib': site, 'platlib': site, 'scripts': target / 'Scripts',
                           'data': target, 'headers': target / 'Include/site' / ('python' + major_minor) / package}
                if scheme not in folders:
                    raise ValueError('内置环境包安装目录不受支持')
                destination = folders[scheme].joinpath(*parts[2:])
            else:
                destination = site.joinpath(*parts)
                if parts[0].endswith('.dist-info'):
                    dist_info = site / parts[0]
            if not destination.resolve().is_relative_to(target.resolve()):
                raise ValueError('内置环境包路径超出项目环境')
            destination.parent.mkdir(parents=True, exist_ok=True)
            raw = archive.read(member)
            destination.write_bytes(raw)
            relative = os.path.relpath(destination, site).replace('\\', '/')
            if not relative.endswith('.dist-info/RECORD'):
                import base64
                digest = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b'=').decode('ascii')
                rows.append((relative, 'sha256=' + digest, str(len(raw))))
    if dist_info is None:
        raise ValueError('内置环境包缺少安装信息')
    for name, raw in [('INSTALLER', b'yuxuan-studio\n'), ('REQUESTED', b'')]:
        path = dist_info / name
        path.write_bytes(raw)
        rows.append((os.path.relpath(path, site).replace('\\', '/'), '', ''))
    record = dist_info / 'RECORD'
    rows.append((os.path.relpath(record, site).replace('\\', '/'), '', ''))
    with record.open('w', encoding='utf-8', newline='') as stream:
        csv.writer(stream).writerows(rows)


def seed_environment(root: Path, target: Path, version: str):
    site = target / 'Lib/site-packages'
    # Never replace packages that the user has installed in an existing venv.
    if not (site / 'pip/__main__.py').is_file():
        wheel = root / 'studio/pip-wheels/pip-24.3.1-py3-none-any.whl' if version == '3.8.9' else next(
            (root / ('runtime/python' + version) / 'Lib/ensurepip/_bundled').glob('pip-*.whl'))
        seed_wheel(wheel, target, version)
    if version == '3.8.9' and not (site / 'setuptools/__init__.py').is_file():
        wheel = next((root / 'runtime/python3.8.9/Lib/ensurepip/_bundled').glob('setuptools-*.whl'))
        seed_wheel(wheel, target, version)
    if not (site / 'pygame/__init__.py').is_file():
        tag = 'cp38' if version == '3.8.9' else 'cp313'
        wheel = root / 'studio/pip-wheels' / ('pygame-2.6.1-' + tag + '-' + tag + '-win_amd64.whl')
        seed_wheel(wheel, target, version)


def _mozilla_bundle():
    # The workspace server runs with the bundled Python 3.13 and pinned pip.
    from pip._vendor import certifi
    return Path(certifi.where())


def https_context():
    """Use CryptoAPI chain building plus Mozilla roots, keeping TLS validation."""
    global _TLS_CONTEXT, _TLS_CREATED
    with _TLS_LOCK:
        now = time.monotonic()
        if _TLS_CONTEXT is None or now - _TLS_CREATED > 300:
            from pip._vendor import truststore
            context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.load_verify_locations(cafile=str(_mozilla_bundle()))
            explicit = os.environ.get('SSL_CERT_FILE')
            if explicit and Path(explicit).is_file():
                context.load_verify_locations(cafile=explicit)
            _TLS_CONTEXT = context
            _TLS_CREATED = now
        return _TLS_CONTEXT


def ca_bundle(data: Path):
    """Give Python 3.8 pip the same Mozilla + Windows server-auth CA roots.

    truststore needs Python >= 3.10; exporting the trusted Windows certificates
    keeps old pip compatible with HTTPS proxies without --trusted-host.
    """
    target = data / 'certificates/https-ca.pem'
    with _TLS_LOCK:
        now = time.monotonic()
        if target.is_file() and now - _CA_CREATED.get(str(target), -1000) < 300:
            return target
        pem = _mozilla_bundle().read_text(encoding='ascii')
        seen = set()
        if os.name == 'nt':
            for store in ('ROOT', 'CA'):
                for certificate, encoding, trust in ssl.enum_certificates(store):
                    if encoding == 'x509_asn' and (trust is True or ssl.Purpose.SERVER_AUTH.oid in trust):
                        digest = hashlib.sha256(certificate).digest()
                        if digest not in seen:
                            pem += '\n' + ssl.DER_cert_to_PEM_cert(certificate)
                            seen.add(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.tmp')
        temporary.write_text(pem, encoding='ascii')
        temporary.replace(target)
        _CA_CREATED[str(target)] = now
    return target
