# 羽轩编程工作台 2.3.0：Mixly 网页版

Mixly 入口改为在本机浏览器中运行的 Mixly 4，页面及编译服务由安装包提供。启动器须保持运行，退出启动器会停止编译和串口服务。建议使用新版 Chrome 或 Edge；MicroPython 的浏览器串口连接需授权设备访问。

保留 Arduino AVR、Arduino ESP8266、Arduino ESP32、MicroPython ESP32 四类硬件环境，以及 MixVM 仿真平台。本次不加入 MixMO / Android App 制作入口；原有 App Inventor 继续使用。

在启动器选择“Mixly 网页编程”，再选择开发环境。Arduino 编译使用随包部署的 Arduino CLI 和本机核心。上传前在工作台顶部选择实际 COM 端口；上传会断开本机串口调试连接。MicroPython 使用编辑器自带的浏览器串口、固件及文件工具。没有连接真实开发板的测试环境下，不能确认具体设备的烧录及通信结果。

安装路径含中文时，本机服务会为旧版 GCC 临时创建一个空闲盘符映射，确保它能找到标准库；正常退出时自动释放，不占用已有盘符。编译所用的 ESP32 响应文件通过相对路径读取，因此用户数据目录可以包含中文和空格。

“管理库”保留官方云端扩展库获取功能。当前 Mixly 4 官方库目录为空，因此对接原官方目录，并将库包适配为新版插件格式。新下载需要网络，第三方库的兼容性取决于各库版本；库作者信息保持原样。目录和原生编译所需库缓存在数据目录 `mixly/cloud`，编辑器插件保存在浏览器的本地站点存储中。清理浏览器站点数据会移除编辑器插件，需重新安装。

“串口调试”支持端口刷新、波特率选择、终端收发和逐行数值绘图。请使用与固件相同的波特率。“驱动下载”提供 CH340/CH341、CH343/CH9102、CP210x、FTDI 厂商链接，需自行下载并安装对应驱动。

仿真平台保留上游 MixVM，包括 Arduino UNO、ESP32 Generic、电路与网络仿真等入口。仿真与真实硬件行为可能存在差异。

切换环境或退出前，使用编辑器文件菜单显式保存 `.mix` 项目。新版浏览器存储与旧版 Electron 的草稿和扩展库不是同一套数据；升级不会删除旧 `mixly/src`、`mixly/drafts` 或 `mixly/profile` 数据，但不会自动导入它们。旧 `.mix` 文件可通过文件菜单打开，建议保留原件。

App Inventor、Python、C++、首次联网激活及后续离线授权规则沿用 2.2.0。本次不要求重新激活，也不更改 Python 或 C++ 项目数据。

上游：Mixly Team@BNU, CHINA，<https://gitee.com/bnu_mixly/mixly4>，基线 `d1141e0fd73255f8705983d2252e8b049119dac1`（4.2026.10.14）。Arduino ESP32 与 ESP8266 模块从同一官方仓库的 `7241435d8bd50543f884e8ff9cb67956cf8e3652` 恢复，并接入本机编译服务。上游 LICENSE 与依赖许可随包保留。

## 构建

使用 Node.js 及 Python，检出上述固定基线和恢复提交到 `work/mixly4/upstream`。在根目录、`common/modules/mixly-modules-es6`、`boards/default_src/python_pyodide` 执行 `npm ci --ignore-scripts`。根构建依赖还需要 `d3@7.9.0`；交付源码中的锁文件已固定该依赖。

运行 `prepare-build.py`，在 core 目录执行 `node ../../../node_modules/webpack/bin/webpack.js --config webpack.prod.js --no-optimization-minimize`，随后执行 `build-web.ps1`、`stage-web.py`。本机桥接依赖安装包原有 Arduino CLI、三个核心、Python 3.13、pyserial 和 `studio/runtime_support.py`。编译 `SuiteLauncher.cs` 与 `SuiteLicense.cs`，最后用 Inno Setup 7 编译 `work/Setup.iss`。

`verify-native.py`、`verify-web.cjs`、`verify-interactions.cjs` 使用隔离测试数据与固定测试令牌，只供本机验收，不使用真实激活码。默认测试端口 8768；正式启动由启动器生成随机令牌。
