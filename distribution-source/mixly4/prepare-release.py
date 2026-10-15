from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NATIVE = ROOT / 'work/native'
RELEASE = ROOT / 'work/release-2.3'
(RELEASE / 'docs').mkdir(parents=True, exist_ok=True)
guide = (ROOT / 'outputs/使用说明.txt').read_text(encoding='utf-8-sig')
guide = guide.replace('2.2.0', '2.3.0')
start = guide.index('Mixly 硬件编程\n')
end = guide.index('退出与备份', start)
instructions = '''Mixly 网页编程
从启动器打开“Mixly 网页编程”，默认浏览器显示本机工作台，保留 AVR、Arduino ESP8266、Arduino ESP32、MicroPython ESP32 四类硬件环境。建议使用新版 Chrome 或 Edge。
Arduino 的编译在本机完成，上传前在工作台顶部选择 COM 端口。MicroPython 使用编辑器自带的浏览器串口和固件工具，连接时需授权访问设备。
通过编辑器“管理库”获取官方云端扩展库；下载新库需要网络，第三方库兼容性依各库版本而异。新版插件保存在浏览器本地站点存储，清理站点数据后需重新安装；原生编译库缓存在数据目录 mixly/cloud。
“仿真平台”打开 MixVM，保留 Arduino UNO、ESP32 Generic、电路和网络仿真等。仿真不替代实物测试。
“串口调试”支持端口刷新、波特率设置、文本收发及逐行数值绘图。上传会断开本机串口调试连接。
“驱动下载”提供 CH340/CH341、CH343/CH9102、CP210x、FT232/FT231 官方下载链接，按 USB 芯片型号自行安装。
切换环境或退出前，务必通过文件菜单保存 .mix 工程。旧版草稿及用户库保留，需自行导入保存的工程；浏览器插件与旧 Electron 数据不是同一套存储。
本次不增加 MixMO / Android App 网页入口；独立 App Inventor 功能继续保留。安装目录 mixly/web/RELEASE.md 提供迁移说明。

'''
guide = guide[:start] + instructions + guide[end:]
guide = guide.replace('启动器提供 App Inventor、Mixly 硬件编程、Python、C++', '启动器提供 App Inventor、Mixly 网页编程、Python、C++')
old = 'Mixly 集成基于 2.0-rc4，保留 Mixly 名称、Mixly Team@BNU, CHINA 作者信息及原许可证；所选环境的适配源码保存在安装目录 mixly\\src。'
guide = guide.replace(old, 'Mixly 集成基于 Mixly 4.2026.10.14，保留 Mixly Team@BNU, CHINA 作者信息及许可证，适配说明及来源记录位于 mixly\\web。')
guide = guide.replace('Mixly 数据：mixly\\src 内的用户扩展库、mixly\\drafts（恢复草稿）、mixly\\profile（界面状态）等。', 'Mixly 数据：mixly\\cloud（原生扩展库缓存）、mixly\\web-settings.json（本机端口）。编辑器插件、界面状态和草稿还位于当前浏览器的本地站点存储；旧版 mixly\\src、drafts、profile 数据保留。')
for dest in (RELEASE / 'docs/使用说明.txt', NATIVE / 'resources/使用说明.txt'):
    dest.write_text(guide, encoding='utf-8')
shutil.copy2(HERE / 'RELEASE.md', NATIVE / 'mixly/web/RELEASE.md')
shutil.copy2(HERE / 'RELEASE.md', RELEASE / 'docs/Mixly网页版迁移说明.md')
(NATIVE / 'resources/build-version.txt').write_text('2026.10.15-mixly4-web-2.3.0\n', encoding='utf-8')
for name in ('SuiteLauncher.cs', 'SuiteLicense.cs', 'Setup.iss'):
    shutil.copy2(ROOT / 'work' / name, NATIVE / 'resources/distribution-source' / name)
print(RELEASE)
