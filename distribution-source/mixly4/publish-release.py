"""Publish only after installed acceptance and source integrity checks succeed."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RELEASE = ROOT / 'work/release-2.3'
OUT = ROOT / 'outputs'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()

install = read(RELEASE / 'install-acceptance.json')
source = read(RELEASE / 'source-audit.json')
build = read(RELEASE / 'installer-build-result.json')
assert install['ok'] and install['userStateRestored'] and not install.get('cleanupFailure')
assert source['ok'] and build['ok']
installer = RELEASE / 'package/AppInventor-Offline-Setup-x64.exe'
assert digest(installer) == install['installerSHA256'] == build['sha256']
assert digest(RELEASE / '适配源码与补丁.zip') == source['sha256']
assert digest(ROOT / 'work/release-2.2/package/AppInventor-Offline-Setup-x64.exe') == '6D7358461F129E575CB42C3943DD14EDFAE442E77C77C98BD515C032FC97328D'
assert digest(ROOT / 'work/release-2.2/package/适配源码与补丁.zip') == '77D523685D3B71602042A3B21F4AB83DE8B9047F86C57A15C029ECE5F42A1F01'
web = read(HERE / 'web-verification.json')
interaction = read(HERE / 'interaction-verification.json')
native = read(HERE / 'native-verification.json')
defaults = read(HERE / 'default-options-verification.json')
serial = read(HERE / 'serial-verification.json')
layout = read(HERE / 'layout-verification.json')
cloud = read(HERE / 'cloud-compile-verification.json')
launcher = read(HERE / '启动器 验收/launcher-result.json')
paths = read(HERE / 'path-verification.json')
assert not web['errors'] and not web['failed'] and len(web['boards']) == 4
assert all(item['ok'] for item in (interaction, native, serial, layout, launcher, paths))
assert cloud['exitCode'] == 0
assert len(defaults) == 2 and all(board['exitCode'] == 0 for board in defaults)
summary = {'version': '2.3.0', 'ok': True, 'publishedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'androidAppIncluded': False, 'hardwareEnvironments': [b['board'] for b in web['boards']],
           'nativeArduinoCompile': native, 'defaultBoardOptions': defaults, 'cloudPackageCompile': cloud,
           'browser': web, 'interaction': interaction, 'layout': layout, 'serial': serial,
           'launcher': launcher, 'compilerPaths': paths, 'installation': install, 'source': source,
           'physicalBoardUploadTested': False, 'physicalSerialDeviceTested': False}
(RELEASE / 'acceptance.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
note = '''# 2.3.0 更新：Mixly 4 网页版（2026-10-15）

Mixly 启动入口已接入本机浏览器工作台，保留 Arduino AVR、Arduino ESP8266、Arduino ESP32、MicroPython ESP32，以及 MixVM 仿真。按用户最新要求不增加 Android App / MixMO。App Inventor、Python、C++ 及授权机制沿用原实现。

已通过四类编辑器加载与代码生成、三类 Arduino 核心真实编译、云端目录获取、PS2 手柄库安装及编译、UNO 闪灯仿真、ESP32 控制台输出、电路仿真、不同宽度布局及串口长流模拟检查。启动器重复打开复用服务，退出关闭服务；使用独占端口防止多个工作区互相干扰。

正式候选安装包已在含中文和空格的独立目录完成安装、重装与卸载检查，安装后编译及原有工具冒烟通过，用户数据与原注册信息已恢复。实物开发板上传及真实串口收发未测试。

新版云端库与草稿使用浏览器站点存储；原生编译库缓存在用户数据目录 mixly/cloud。旧 Electron 数据保留但不自动迁移，切换或退出前应保存 .mix。安装包不再安装旧 Electron 运行时。详见《Mixly网页版迁移说明.md》和《2.3-Mixly网页版验收.json》。下方保留 2.2.0 的历史交接与验收记录。

---

'''
for name in ('工程交接.md', '验收记录.md', '项目进度-2026-10-02.md'):
    old = (OUT / name).read_text(encoding='utf-8-sig')
    (RELEASE / 'docs' / name).write_text(note + old, encoding='utf-8')
files = {'AppInventor-Offline-Setup-x64.exe': installer,
         '适配源码与补丁.zip': RELEASE / '适配源码与补丁.zip',
         '使用说明.txt': RELEASE / 'docs/使用说明.txt',
         'Mixly网页版迁移说明.md': HERE / 'RELEASE.md',
         '2.3-Mixly网页版验收.json': RELEASE / 'acceptance.json',
         '2.3-安装验收.json': RELEASE / 'install-acceptance.json',
         '2.3-Mixly网页首页.png': HERE / 'web-home.png',
         '2.3-Mixly云端库.png': HERE / 'web-cloud-libraries.png',
         '2.3-Mixly本机编译.png': HERE / 'web-compile.png',
         '2.3-ESP32仿真.png': HERE / 'sim-esp32_design.png',
         '2.3-电路仿真.png': HERE / 'sim-mixck_design.png'}
for name in ('工程交接.md', '验收记录.md', '项目进度-2026-10-02.md'):
    files[name] = RELEASE / 'docs' / name
for name, path in files.items():
    temporary = OUT / (name + '.2.3-new')
    shutil.copy2(path, temporary)
    assert digest(temporary) == digest(path)
    temporary.replace(OUT / name)
hashes = [digest(path) + '  ' + path.name for path in sorted(OUT.iterdir()) if path.is_file() and path.name != 'SHA256SUMS.txt']
(OUT / 'SHA256SUMS.txt').write_text('\n'.join(hashes) + '\n', encoding='utf-8')
(RELEASE / 'publish-result.json').write_text(json.dumps({'ok': True, 'files': list(files), 'installerSHA256': build['sha256'], 'sourceSHA256': source['sha256']}, ensure_ascii=False, indent=2), encoding='utf-8')
print('Published verified 2.3.0 installer, source, instructions and evidence.')
