"""Verify original library provenance, content cache keys, corrupt-file fallback and cancellation."""
import argparse, hashlib, importlib.util, json, os, pathlib, re, shutil, subprocess, zipfile

HERE = pathlib.Path(__file__).resolve().parent
NATIVE = HERE.parent / 'native'
parser = argparse.ArgumentParser()
parser.add_argument('--native-root', type=pathlib.Path, default=NATIVE)
args = parser.parse_args(); NATIVE = args.native_root.resolve()
loader = importlib.util.spec_from_file_location('dex_seed', HERE / 'prepare-dex-seed.py')
seed = importlib.util.module_from_spec(loader); loader.loader.exec_module(seed)
fixture = HERE / 'seed-validation'; fixture.mkdir(exist_ok=True)
resource_root = NATIVE / 'buildserver/resource-seed'
resource_manifest = json.loads((resource_root / 'manifest.json').read_text())
dex_root = NATIVE / 'buildserver/dex-seed'
dex_manifest = json.loads((dex_root / 'manifest.json').read_text())
with zipfile.ZipFile(NATIVE / 'buildserver/lib/BuildServer.jar') as jar:
    assert hashlib.sha256((NATIVE / 'buildserver/lib/BuildServer.jar').read_bytes()).hexdigest() == resource_manifest['sourceJarSha256']
    for entry in resource_manifest['entries']:
        original = jar.read(entry['resource'])
        assert (resource_root / entry['resource']).read_bytes() == original
        assert hashlib.sha256(original).hexdigest() == entry['sha256']
    d8 = jar.read('tools/d8.jar'); android = jar.read('files/android.jar')
    assert hashlib.sha256(d8).hexdigest() == dex_manifest['d8Sha256']
    assert hashlib.sha256(android).hexdigest() == dex_manifest['androidSha256']
    for entry in dex_manifest['entries']:
        original = jar.read(entry['resource'])
        input_hash = hashlib.sha256(original).hexdigest()
        assert input_hash == entry['inputSha256']
        fingerprint = hashlib.sha256(('yuxuan-d8-intermediate-v2\n' + dex_manifest['d8Sha256'] + '\n'
                                     + dex_manifest['androidSha256'] + '\n' + str(entry['minApi']) + '\n').encode()).hexdigest()
        expected_name = 'dex-v2-' + hashlib.sha256((fingerprint + '\n' + input_hash).encode()).hexdigest() + '.dex'
        assert entry['file'] == expected_name
        content = (dex_root / entry['file']).read_bytes()
        assert seed.valid_dex(content) and hashlib.sha256(content).hexdigest() == entry['dexSha256']
bad_resources = fixture / 'bad-resource-seed'; (bad_resources / 'files').mkdir(parents=True, exist_ok=True)
shutil.copy2(resource_root / 'manifest.properties', bad_resources / 'manifest.properties')
bad = bytearray((resource_root / 'files/annotation.jar').read_bytes()); bad[-1] ^= 1
(bad_resources / 'files/annotation.jar').write_bytes(bad)
classes = fixture / 'classes'; classes.mkdir(exist_ok=True)
classpath = str(NATIVE / 'buildserver/classes') + os.pathsep + str(NATIVE / 'buildserver/lib/*')
subprocess.run([str(NATIVE / 'runtime/java11/bin/javac.exe'), '-encoding', 'UTF-8', '-cp', classpath,
                '-d', str(classes), str(HERE / 'SeedValidation.java')], check=True)
proc = subprocess.run([str(NATIVE / 'runtime/java11/bin/java.exe'), '-Dfile.encoding=UTF-8',
                       '-Djava.io.tmpdir=' + str(fixture), '-Dappinventor.resourceSeedDir=' + str(resource_root),
                       '-cp', str(classes) + os.pathsep + classpath, 'SeedValidation', str(fixture),
                       str(dex_root / dex_manifest['entries'][0]['file']), str(bad_resources),
                       str(NATIVE / 'runtime/python3.13.16/python.exe')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if proc.returncode:
    raise RuntimeError(proc.stdout.decode('utf-8', 'replace') + proc.stderr.decode('utf-8', 'replace'))
checks = [s.strip() for s in re.findall(r'^PASS (.+)$', proc.stdout.decode('utf-8', 'replace'), re.M)]
assert len(checks) == 10, proc.stdout.decode('utf-8', 'replace') + proc.stderr.decode('utf-8', 'replace')
result = {'resourceEntries': len(resource_manifest['entries']), 'resourceBytes': sum(e['bytes'] for e in resource_manifest['entries']),
          'dexEntries': len(dex_manifest['entries']), 'dexBytes': sum(e['bytes'] for e in dex_manifest['entries']),
          'checks': checks, 'status': 'passed'}
(HERE / 'seed-validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
