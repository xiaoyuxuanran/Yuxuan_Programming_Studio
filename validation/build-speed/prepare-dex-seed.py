"""Pre-dex immutable bundled libraries at release time, keeping first app build fast.

Cache keys must match RunD8.java: input contents + D8 + Android library + min API.
No application, extension, user signing key or user source is included in this cache.
"""
import argparse, hashlib, json, pathlib, shutil, struct, subprocess, time, zipfile, zlib

HERE = pathlib.Path(__file__).resolve().parent
NATIVE = HERE.parent / 'native'

def sha256(content):
    return hashlib.sha256(content).hexdigest()

def valid_dex(content):
    return len(content) >= 112 and content[:4] == b'dex\n' and content[7] == 0 \
        and struct.unpack_from('<I', content, 32)[0] == len(content) \
        and hashlib.sha1(content[32:]).digest() == content[12:32] \
        and zlib.adler32(content[12:]) == struct.unpack_from('<I', content, 8)[0]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-api', nargs='+', type=int, default=[14, 19])
    parser.add_argument('--native-root', type=pathlib.Path, default=NATIVE)
    parser.add_argument('--output', type=pathlib.Path)
    args = parser.parse_args()
    native = args.native_root.resolve()
    args.output = args.output or native / 'buildserver/dex-seed'
    args.output.mkdir(parents=True, exist_ok=True)
    inputs = HERE / 'seed-inputs'; inputs.mkdir(exist_ok=True)
    with zipfile.ZipFile(native / 'buildserver/lib/BuildServer.jar') as jar:
        d8 = jar.read('tools/d8.jar'); android = jar.read('files/android.jar')
        (inputs / 'd8.jar').write_bytes(d8); (inputs / 'android.jar').write_bytes(android)
        libraries = {name: jar.read(name) for name in jar.namelist()
                     if name.startswith('files/') and name.endswith('.jar') and name != 'files/android.jar'}
        # Most AARs are optimized and contain no class JAR. Cover any that do.
        for name in jar.namelist():
            if name.startswith('files/') and name.endswith('.aar'):
                import io
                with zipfile.ZipFile(io.BytesIO(jar.read(name))) as aar:
                    if 'classes.jar' in aar.namelist() and aar.getinfo('classes.jar').file_size > 22:
                        libraries[name + '!classes.jar'] = aar.read('classes.jar')
    manifest = {'format': 'yuxuan-d8-intermediate-v2', 'd8Sha256': sha256(d8),
                'androidSha256': sha256(android), 'minApis': args.min_api, 'entries': []}
    for min_api in args.min_api:
        environment = sha256(('yuxuan-d8-intermediate-v2\n' + sha256(d8) + '\n'
                              + sha256(android) + '\n' + str(min_api) + '\n').encode())
        for index, (resource, content) in enumerate(libraries.items()):
            filename = 'dex-v2-' + sha256((environment + '\n' + sha256(content)).encode()) + '.dex'
            output = args.output / filename
            started = time.perf_counter()
            if output.is_file() and valid_dex(output.read_bytes()):
                method = 'already-prepared'
            else:
                name = pathlib.Path(resource.split('!')[0]).name + '.jar'
                source = inputs / name; source.write_bytes(content)
                scratch = inputs / 'dex-output'; scratch.mkdir(exist_ok=True)
                params = ['-Xmx2048M', '-Xss8m', '-cp', str(inputs / 'd8.jar'), 'com.android.tools.r8.D8',
                          '--intermediate', '--lib', str(inputs / 'android.jar'), '--output', str(scratch),
                          '--min-api', str(min_api), str(source)]
                argfile = inputs / 'arguments.txt'
                argfile.write_text('\n'.join('"' + p.replace('\\', '\\\\').replace('"', '\\"') + '"'
                                              for p in params) + '\n', encoding='utf-8')
                proc = subprocess.run([str(native / 'runtime/java11/bin/java.exe'), '@' + str(argfile)],
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180,
                                      creationflags=0x08000000)
                generated = scratch / 'classes.dex'
                if proc.returncode or not generated.is_file() or not valid_dex(generated.read_bytes()):
                    raise RuntimeError('Could not pre-dex ' + resource + '\n' + proc.stdout.decode('utf-8', 'replace')[-4000:])
                generated.replace(output); method = 'd8'
            manifest['entries'].append({'resource': resource, 'inputSha256': sha256(content),
                                        'minApi': min_api, 'file': filename,
                                        'dexSha256': sha256(output.read_bytes()), 'bytes': output.stat().st_size})
            print(str(min_api) + ' ' + str(index + 1) + '/' + str(len(libraries)) + ' ' + resource
                  + ' ' + method + ' ' + str(round(time.perf_counter() - started, 2)) + 's', flush=True)
        (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Prepared ' + str(len(manifest['entries'])) + ' immutable library entries', flush=True)

if __name__ == '__main__':
    main()
