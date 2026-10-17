"""Stage reviewed 2.3.2 source and documentation; no credentials or user data."""
from pathlib import Path
import shutil, json, re, zipfile, hashlib, runpy
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
REPO=ROOT/'work/github-publish/Yuxuan_Programming_Studio';NATIVE=ROOT/'work/native'
shutil.copytree(NATIVE/'resources/distribution-source',REPO/'distribution-source',dirs_exist_ok=True)
shutil.copy2(HERE/'使用说明.txt',REPO/'docs/使用说明.txt')
shutil.copy2(HERE/'UPGRADE.md',REPO/'docs/UPGRADE-2.3.2.md')
shutil.copy2(HERE/'CHANGELOG.txt',REPO/'CHANGELOG.txt')
test=REPO/'validation/release-2.3.2';test.mkdir(parents=True,exist_ok=True)
for name in ['desktop-regression.cjs','desktop-smoke.cjs','run-desktop-regression.ps1','run-desktop-smoke.ps1','installed-smoke.py','acceptance-2.2-final.ps1','acceptance-2.3.1-final.ps1','SuiteIntegrationCheck.cs','UpdateCheck.cs','UpdateCompatibilityCheck.cs','UpdateNetworkCheck.cs']:
    shutil.copy2(HERE/name,test/name)
own=REPO/'distribution-source/release-2.3.2'
for name in ['Update-2.2.0.iss','Update-2.3.1-ultra256.iss','update-manifest-2.2.0.json','update-manifest-2.3.1.json','prepare-github.py']:
    shutil.copy2(HERE/name,own/name)
overlay=REPO/'upstream-overlays/mixly2'
relatives=['common/js/blockly_helper.js','common/template/serial-tool.html','common/modules/mixly-modules/common/dom-operator.js','common/modules/mixly-modules/electron/cloud-download.js','boards/default/arduino_esp32/blocks/communicate.js','boards/default/arduino_esp32/generators/communicate.js','boards/default/arduino_esp32/xml/esp32.xml']
for relative in relatives:
    p=overlay/relative;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(NATIVE/'mixly/src'/relative,p)
shutil.copy2(NATIVE/'mixly/UPSTREAM.json',REPO/'distribution-source/mixly-adaptation/UPSTREAM.json')
build='''# Mixly 桌面版适配与重建

2.3.2 使用 [Mixly 2.0 源码](https://gitee.com/mixly2/mixly2.0_src) 的 `2.0-rc4`，提交 `a7d91f1e3c621a3132fb8ea38c92877bb0834830`。官方 Windows Electron 19.0.6 及原生依赖来自 `mixly2.0-win32-x64` 提交 `d1bb6950c91f3b8f68d571188393b3d6b6603eb7`；Arduino 库基线提交 `2b7ca7d23afec725d23f80b3d995d4cf5fa57a01`。详细记录见 `distribution-source/mixly-adaptation/UPSTREAM.json`。

准备原开发目录 `work/mixly/{upstream,desktop-upstream,arduino-libs}`，将 `distribution-source/mixly-adaptation` 中的适配文件放回 `work/mixly`。`prepare-mixly.py` 输出 `work/native/mixly` 并调用 `fix-desktop.py`；后者应用单次草稿恢复、串口关闭按钮、官方 HTTPS 云库备用源和经典 ESP32 蓝牙修复。`upstream-overlays/mixly2` 保存修改后的上游文件，供审阅和核对。

`workspace-recovery.js` 阻止上游 localStorage 与文件草稿重复追加，原积木和手写代码分别恢复。`compiler-paths.py` 使用当前用户本地缓存中的编译器目录联接，绕开旧 GCC 展开私有头文件路径时的长度限制；ESP32 SDK 仍通过 response 文件传入。目录联接仅指向已安装工具，不删除目标 SDK，不修改系统 PATH。

平台运行环境、App Inventor 源码与构建准备沿用 2.2.0 / 2.3.0 发布附件；本仓库不包含全部预构建依赖。启动器代码位于 `distribution-source/Suite*.cs`，按原 `BuildRelease.ps1` 使用 .NET Framework 编译器编译。`prepare-package.py` 需要原版实际安装的 `base-2.2.0.json` 和 `base-2.3.1.json` 清单，再与 `work/native` 比较，生成两种更新包；`snapshot-installed.py` 可生成基线快照。Inno 脚本的绝对开发路径需按本机调整；2.3.1 包使用 LZMA2 256 MiB 字典压缩，构建约需 3 GB 内存。

2.3.0 / 2.3.1 的 `distribution-source/mixly4` 与 `upstream-overlays/mixly4` 留作历史源码；2.3.2 运行入口使用桌面适配，不提供仿真。App Inventor 的 2.3.1 扩展和 Blockly 修改继续沿用，未回滚。

验收脚本位于 `validation/release-2.3.2`，使用临时安装目录及已有测试授权；运行前按本机路径配置，不能在个人正式安装目录运行。安装验收保存并恢复卸载注册和快捷方式，检查增量覆盖、重复覆盖、数据保留和合并卸载。测试授权与日志不随公开源码发布。
'''
(REPO/'docs/Mixly桌面版适配说明.md').write_text(build,encoding='utf-8')
readme='''# 羽轩编程工作台 · Yuxuan Programming Studio

Windows x64 本地编程平台，集成 App Inventor、Mixly 桌面编程、Python 和 C++。当前版本 **2.3.2**。

## 下载与升级

[Gitee 分版本下载](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/tag/v2.3.2) · [GitHub 备用](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.2)

| 当前版本 | 使用的更新包 |
| --- | --- |
| **2.2.0** | **[直接升级到 2.3.2](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/download/v2.3.2/Yuxuan-Programming-Studio-Update-2.2.0-to-2.3.2.exe)**，无需中间版本 |
| 2.3.1 | [2.3.1 → 2.3.2](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/download/v2.3.2/Yuxuan-Programming-Studio-Update-2.3.1-to-2.3.2.exe) |
| 2.3.0 | 先应用 [2.3.1 增量包](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/tag/v2.3.1)，再应用本版对应更新包 |
| 首次安装 | 安装 [完整 2.2.0](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.2.0)，再使用 2.2.0 直升包 |

保存工程并退出软件，运行匹配的更新包，选择原安装目录。项目、依赖与激活信息保留。**从 Mixly 网页版切回前，请先将工程另存为 `.mix`，再在桌面版打开。** [详细升级说明](docs/UPGRADE-2.3.2.md)。

安装包包含运行环境，无需另装 WSL、Python、C++ 编译器或 Java。首次使用必须联网激活，之后可在授权有效期内离线使用；联网时校验授权状态。公开附件不包含激活码或已激活凭证。

## 本次修改

- Mixly 切回 2.2.0 同款 2.0-rc4 桌面客户端，保留 Arduino AVR、Arduino ESP8266、Python ESP32、Arduino ESP32，无仿真入口。
- 修复关闭后重开、刷新时积木被重复复制；同时恢复原积木和手写代码。
- 串口调试弹窗增加可点击、可键盘聚焦的“关闭 ×”按钮。
- 保留云端库和驱动下载，官方主站不可用时使用官方 HTTPS Gitee 云库备用源。
- 保留经典 ESP32 蓝牙串口修复；缩短旧 GCC 内部路径，避免长安装目录下缺少标准库头文件。
- 保留 2.3.1 的 App Inventor 优质扩展 MqttTCP、BluetoothLE、ClientSocketAI2Ext、积木拖拽删除与撤销，以及更新入口。

## 功能与文档

App Inventor 默认经典布局、蓝白主题，支持本机 APK 构建下载、USB 安装运行及应用日志。Python 支持 3.8.9 / 3.13.16、项目环境隔离、Tkinter / Turtle / Pygame、第三方库搜索及清华源安装；C++ 使用内置 Clang++、C++17 和编译缓存。代码编辑器提供文件树、运行结果、基础提示以及 Light / Dark 主题。

主页面提供更新日志、检查更新；优先 Gitee，失败回退 GitHub，下载校验大小和 SHA256。

- [使用说明](docs/使用说明.txt)、[更新日志](CHANGELOG.txt)
- [Mixly 桌面版适配与构建](docs/Mixly桌面版适配说明.md)
- `distribution-source/`：平台源码与适配脚本；`upstream-overlays/`：上游修改；`validation/`：验收脚本。
- [历史 Mixly 网页版说明](docs/Mixly网页版迁移说明.md)，仅对应 2.3.0 / 2.3.1。

本仓库不包含全部预构建依赖。2.3.2 的 `Source-and-Patches.zip` 提供本次源码与补丁；完整上游源码基线沿用 2.2.0 / 2.3.0 发布附件，目录准备见构建说明。

## 许可与验证范围

各上游项目及适配文件沿用原版权声明与许可证，见 `licenses/` 和文件头；Mixly 作者为 Mixly Team@BNU, CHINA，源码与固定提交见适配说明。历史网页源码保留以供追溯。品牌图片不代表上游官方背书。

已验证四类编辑器、草稿反复恢复及进程重启、串口关闭、云库获取及导入、Arduino 本机编译和经典 ESP32 蓝牙生成编译。升级包验证原版安装后的覆盖、重复覆盖、数据保留和合并卸载；未连接真实开发板或 Android 手机。
'''
(REPO/'README.md').write_text(readme,encoding='utf-8')
notes='''羽轩编程工作台 **2.3.2**，Windows x64。

### 本次更新

1. Mixly 恢复为 2.2.0 同款 **2.0-rc4 桌面客户端**，无仿真入口；保留 AVR、ESP8266、Python ESP32、Arduino ESP32。
2. 修复退出重开或刷新时积木被复制并隐藏到后方；代码视图也会同时保留积木、手写代码及文件路径。
3. 串口调试弹窗新增明显的 **关闭 ×** 按钮，支持键盘聚焦，保留原收发与绘图模块。
4. 保留云端库与驱动下载；官方主站不可用时使用米思齐官方 HTTPS Gitee 云库备用源。
5. 保留 2.3.1 的经典 ESP32 蓝牙修复，以及 App Inventor 优质扩展、积木拖拽删除和主页面更新入口。修复旧 GCC 在较长安装目录下缺少标准库头文件的问题。

### 选择匹配的更新包

- **2.2.0 → 2.3.2**：`Yuxuan-Programming-Studio-Update-2.2.0-to-2.3.2.exe`，直接升级，无需中间版本。
- **2.3.1 → 2.3.2**：`Yuxuan-Programming-Studio-Update-2.3.1-to-2.3.2.exe`，包含切回桌面版需要补齐的客户端文件。
- 2.3.0 先升级到 2.3.1，再使用对应更新包。首次安装先安装完整 2.2.0，再使用本版直升包。
- 保存工程并退出，选择原安装目录。更新包检查基础文件；项目、第三方依赖和激活信息保留，可重复安装修复本版，卸载记录合并。

**从 Mixly 网页版切回前，请先另存 `.mix`，升级后在桌面版打开。** 浏览器草稿及扩展数据保留，但网页扩展需要使用兼容的桌面版本。

### 下载与附件

[Gitee 下载](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/tag/v2.3.2) · [GitHub 备用](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.2)。软件检查及下载更新优先 Gitee，失败回退 GitHub；均校验 SHA256。

除两个更新包外，附件提供 `Source-and-Patches.zip`、`User-Guide.txt`、`UPGRADE.md`、`CHANGELOG.txt`、`SHA256SUMS.txt` 和 `update.json`。完整上游源码基线沿用 2.2.0 / 2.3.0 的发布附件。

已验证重复恢复与进程重启、四类编辑器及云库目录、AVR 实际库导入、AVR / ESP8266 / ESP32 本机编译、经典 ESP32 蓝牙编译、串口模拟回显和弹窗关闭。两个升级路径均以原版实际安装为基础，核对程序文件、重复更新、用户数据保留及合并卸载。未连接实体开发板或 Android 手机。
'''
(HERE/'release-notes.md').write_text(notes,encoding='utf-8')
for name,target in [('使用说明.txt','User-Guide.txt'),('UPGRADE.md','UPGRADE.md'),('CHANGELOG.txt','CHANGELOG.txt')]:shutil.copy2(HERE/name,HERE/'package'/target)
if __name__=='__main__':
    secret=runpy.run_path(str(ROOT/'work/release-2.3.1/gitee-publish.py'))['token']().encode()
    report={'files':0,'bytes':0};bundle=HERE/'package/Source-and-Patches.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(REPO.rglob('*')):
            if not p.is_file() or '.git' in p.relative_to(REPO).parts:continue
            rel=p.relative_to(REPO).as_posix()
            if rel=='update.json':continue
            raw=p.read_bytes()
            assert secret not in raw,rel
            assert not re.search(rb'YX-[0-9A-F]{8}(?:-[0-9A-F]{8}){3}',raw),rel
            assert not re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]+[A-Za-z0-9+/\r\n]{64,}',raw),rel
            assert not re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})',raw),rel
            z.writestr(rel,raw);report['files']+=1;report['bytes']+=len(raw)
    with zipfile.ZipFile(bundle) as z:assert z.testzip() is None
    report.update(sha256=hashlib.file_digest(bundle.open('rb'),'sha256').hexdigest(),zipBytes=bundle.stat().st_size)
    (HERE/'source-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
