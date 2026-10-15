"""Pre-extract the immutable Windows build resources, with per-file SHA256 verification."""
import argparse, hashlib, json, pathlib, zipfile

HERE = pathlib.Path(__file__).resolve().parent
NATIVE = HERE.parent / 'native'
parser = argparse.ArgumentParser()
parser.add_argument('--native-root', type=pathlib.Path, default=NATIVE)
parser.add_argument('--output', type=pathlib.Path)
args = parser.parse_args()
NATIVE = args.native_root.resolve()
OUTPUT = args.output or NATIVE / 'buildserver/resource-seed'
OUTPUT.mkdir(parents=True, exist_ok=True)
entries = []
with zipfile.ZipFile(NATIVE / 'buildserver/lib/BuildServer.jar') as jar:
    for item in jar.infolist():
        if item.is_dir() or not item.filename.startswith(('files/', 'tools/')):
            continue
        if item.filename.startswith(('tools/mac/', 'tools/linux/')):
            continue
        content = jar.read(item)
        target = OUTPUT / item.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        entries.append({'resource': item.filename, 'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)})
(OUTPUT / 'manifest.properties').write_text('\n'.join(e['resource'] + '=' + e['sha256'] for e in entries) + '\n', encoding='ascii')
(OUTPUT / 'manifest.json').write_text(json.dumps({'sourceJarSha256': hashlib.sha256((NATIVE / 'buildserver/lib/BuildServer.jar').read_bytes()).hexdigest(), 'entries': entries}, indent=2), encoding='utf-8')
print('Prepared ' + str(len(entries)) + ' resource files, ' + str(sum(e['bytes'] for e in entries)) + ' bytes')
