"""Avoid old GCC's Windows MAX_PATH limit in its internally expanded include paths."""
import ctypes, json, pathlib, sys, subprocess
root = pathlib.Path(sys.argv[1])
data = pathlib.Path(sys.argv[2]);data.mkdir(parents=True,exist_ok=True)
def short_path(folder):
    buf = ctypes.create_unicode_buffer(32768)
    size = ctypes.windll.kernel32.GetShortPathNameW(str(folder),buf,len(buf))
    return (buf.value if size else str(folder)).replace('\\','/')
compilers = {'arduino:avr':('arduino','avr-gcc'), 'esp8266:esp8266':('esp8266','xtensa-lx106-elf-gcc'), 'esp32:esp32':('esp32','xtensa-esp32-elf-gcc')}
paths = {};properties={}
for key, (package, tool) in compilers.items():
    directory = root/'Arduino15/packages'/package/'tools'/tool
    if not directory.is_dir(): continue
    versions = sorted(directory.iterdir())
    if not versions: continue
    folder = str(versions[-1])
    paths[key] = short_path(folder)+'/bin/'
    properties[key]=[['compiler.path',paths[key]]]
# ESP32 2.x expands hundreds of SDK include paths beyond Windows' command-line limit.
# Put those flags in GCC's native response file instead of the process command line.
platforms=sorted((root/'Arduino15/packages/esp32/hardware/esp32').iterdir())
if platforms:
    platform=platforms[-1]
    flags=next(line.split('=',1)[1] for line in (platform/'platform.txt').read_text(encoding='utf-8').splitlines() if line.startswith('compiler.cpreprocessor.flags.esp32='))
    subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(pathlib.Path(__file__).with_name('sdk-junction.ps1')),'-DataRoot',str(data),'-TargetPath',str((platform/'tools/sdk/esp32').resolve())],check=True,capture_output=True)
    flags=flags.replace('{compiler.sdk.path}','esp32sdk')
    compiler=paths['esp32:esp32'][:-len('bin/')]
    backend=pathlib.Path(compiler)/'libexec/gcc/xtensa-esp32-elf/8.4.0'
    flags+=' -B'+short_path(backend)+'/'
    response=data/'esp32-sdk-flags.rsp';response.write_text(flags,encoding='utf-8')
    # The bridge executes GCC from data; avoid non-ASCII absolute response paths.
    response_path=response.name
    response_arg='@'+response_path
    if ' ' in response_path: response_arg='"'+response_arg+'"'
    # Preserve the outer property's board-specific memory-type include directory.
    properties['esp32:esp32'].append(['compiler.cpreprocessor.flags.esp32',response_arg])
    properties['esp32:esp32'].append(['compiler.sdk.path','esp32sdk'])
print(json.dumps({'paths':paths,'properties':properties}))
