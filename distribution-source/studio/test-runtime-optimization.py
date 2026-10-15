"""Real fast-environment, cache-invalidation and TLS-negative acceptance checks."""
from pathlib import Path
import datetime
import json
import os
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1] / 'native'
sys.path.insert(0, str(ROOT / 'studio'))
import server
import runtime_support

DATA = Path(sys.argv[1]).resolve()
DATA.mkdir(parents=True, exist_ok=True)
server.DATA = DATA
server.STATE = {'theme': 'light', 'projects': []}
results = []
timings = {}


def check(name, success):
    if not success:
        raise AssertionError(name)
    results.append(name)
    print('PASS', name, flush=True)


def run(project, name, version='3.13.16'):
    start = time.perf_counter()
    job = server.run(project, name, version, [])
    deadline = time.monotonic() + 90
    while job.running and time.monotonic() < deadline:
        time.sleep(.02)
    if job.running:
        job.stop()
        raise AssertionError('run timeout')
    return job, round(time.perf_counter() - start, 3)


py = server.add_project('Python fresh', 'python')
for version in server.VERSIONS:
    job, elapsed = run(py, 'main.py', version)
    timings['python_first_' + version] = elapsed
    check('fresh isolated Python ' + version, job.code == 0 and version in job.output)
    job, elapsed = run(py, 'main.py', version)
    timings['python_repeat_' + version] = elapsed
    check('repeat avoids environment setup ' + version, job.code == 0 and '正在准备' not in job.output)
    exe = DATA / 'environments' / py['id'] / version / 'Scripts/python.exe'
    probe = subprocess.run([str(exe), '-m', 'pip', 'check'], capture_output=True, env=server.process_env(exe), creationflags=0x08000000)
    check('seeded wheel metadata accepted by pip ' + version, probe.returncode == 0)

cpp = server.add_project('C++ headers', 'cpp')
folder = Path(cpp['path'])
(folder / 'value.h').write_text('#define VALUE 11\n')
(folder / 'main.cpp').write_text('#include <iostream>\n#include "value.h"\n#if __has_include("optional.h")\n#include "optional.h"\n#else\n#define EXTRA 0\n#endif\nint main(){std::cout << "RESULT=" << VALUE+EXTRA << std::endl;}\n')
job, elapsed = run(cpp, 'main.cpp')
timings['cpp_first'] = elapsed
check('C++ initial compilation', job.code == 0 and 'RESULT=11' in job.output)
job, elapsed = run(cpp, 'main.cpp')
timings['cpp_repeat'] = elapsed
check('C++ unchanged build reused', job.code == 0 and 'RESULT=11' in job.output and '使用已编译' in job.output)
(folder / 'value.h').write_text('#define VALUE 22\n')
job, _ = run(cpp, 'main.cpp')
check('changed included header rebuilds', job.code == 0 and 'RESULT=22' in job.output and '使用已编译' not in job.output)
(folder / 'optional.h').write_text('#define EXTRA 3\n')
job, _ = run(cpp, 'main.cpp')
check('new __has_include header rebuilds', job.code == 0 and 'RESULT=25' in job.output and '使用已编译' not in job.output)
(folder / 'main.cpp').write_text('int main(){this is invalid C++;}\n')
job, _ = run(cpp, 'main.cpp')
check('failed compile never runs cached executable', job.code != 0 and 'RESULT=' not in job.output and '▶ 运行' not in job.output)

context = runtime_support.https_context()
check('HTTPS requires certificate and hostname validation', context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname)
for label, url in [('PyPI search', 'https://pypi.org/pypi/colorama/json'), ('Tsinghua index', 'https://pypi.tuna.tsinghua.edu.cn/simple/colorama/')]:
    with urllib.request.urlopen(url, context=context, timeout=25) as response:
        check(label + ' verified HTTPS', response.status == 200)

# Generate throwaway test credentials locally; no key is distributed with source.
sys.path.insert(0, str(ROOT / 'license/vendor'))
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
now = datetime.datetime.now(datetime.timezone.utc)
certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
               .serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=1))
               .not_valid_after(now+datetime.timedelta(hours=1))
               .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]), critical=False)
               .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True).sign(key, hashes.SHA256()))
cert_file = DATA / 'tls-fixture.pem'
key_file = DATA / 'tls-fixture-key.pem'
cert_file.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
key_file.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))


class Fixture(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'fixture')


class FixtureServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # Native chain/hostname validation closes a rejected TLS connection.
        if not isinstance(sys.exc_info()[1], ConnectionResetError):
            super().handle_error(request, client_address)


http = FixtureServer(('127.0.0.1', 0), Fixture)
fixture_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
fixture_context.load_cert_chain(cert_file, key_file)
http.socket = fixture_context.wrap_socket(http.socket, server_side=True)
threading.Thread(target=http.serve_forever, daemon=True).start()
# Bypass proxy only for this explicit loopback test endpoint.
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=context))
try:
    rejected = False
    try:
        opener.open('https://localhost:' + str(http.server_port), timeout=10)
    except urllib.error.URLError as error:
        rejected = isinstance(error.reason, ssl.SSLError)
    check('untrusted TLS certificate rejected', rejected)
    from pip._vendor import truststore
    trusted = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    trusted.load_verify_locations(cafile=str(cert_file))
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=trusted))
    with opener.open('https://localhost:' + str(http.server_port), timeout=10) as response:
        check('explicit trusted TLS fixture works', response.status == 200)
    rejected = False
    try:
        opener.open('https://127.0.0.1:' + str(http.server_port), timeout=10)
    except urllib.error.URLError as error:
        rejected = isinstance(error.reason, ssl.SSLError)
    check('trusted certificate with wrong hostname rejected', rejected)
finally:
    http.shutdown()
    http.server_close()
    key_file.unlink()
    cert_file.unlink()

(DATA / 'optimization-acceptance.json').write_text(json.dumps({'passed': results, 'seconds': timings}, ensure_ascii=False, indent=2), encoding='utf-8')
print('TIMINGS', json.dumps(timings), flush=True)
print('ALL', len(results), 'CHECKS PASSED', flush=True)
