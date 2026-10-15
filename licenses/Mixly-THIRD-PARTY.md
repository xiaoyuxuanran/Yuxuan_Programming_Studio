# Mixly4Yuxuan 2.1.0

基于用户指定的 Mixly 2.0 源码，选用 2.0-rc4（a7d91f1e3c621a3132fb8ea38c92877bb0834830）。保留 Mixly 名称及 Mixly Team@BNU, CHINA 作者信息，遵循原 LICENSE 以及各依赖许可证。

仅在入口提供 Arduino AVR、Arduino ESP8266、Python ESP32、Arduino ESP32。使用原积木、代码生成、文件保存、云端库管理、上传和串口调试模块。Python ESP32 为开发板 MicroPython 环境，启动器的 Python 为桌面 Python 环境。

云端库使用官方 Mixly HTTPS 分类目录，已验证全部四类目录及 AVR 实际下载导入。串口保留原模块，已验证原生端口枚举和 115200 波特率模拟回显。没有连接真实开发板，因此不将烧录和真机串口收发记为已验证。

驱动下载入口链接到 WCH CH340/CH341、CH343/CH9102、Silicon Labs CP210x、FTDI 厂商页面，由用户下载安装。

内置 Arduino CLI 0.35.3，arduino:avr 1.8.6、esp8266:esp8266 3.1.2、esp32:esp32 2.0.17；包下载对照官方索引 SHA256 校验。三类 Arduino 编译通过原 UI 编译路径验证。官方 Windows Electron 19.0.6 及原生依赖与 Mixly Windows 发行版一致；ESP32 传输工具由内置 Python 3.8.9 执行。

Windows 长路径修复：compiler-paths.py 获取工具短路径，并使用位于用户数据目录的 esp32sdk 目录联接和 GCC response 文件缩短 ESP32 编译参数，保留具体内存类型的 sdkconfig.h 包含路径。联接只指向已安装 SDK，更新时仅更换联接，不删除目标 SDK。

suite-main.js 提供本机健康检查和受 token 保护的启动器控制接口，保持原生 USB/串口运行。页面只允许本地文件导航，外链使用系统浏览器。用户数据、云端扩展库、草稿及构建缓存存放在用户数据目录 mixly 下，升级只刷新程序文件。

prepare-mixly.py 为适配生成脚本，输入为同目录 upstream、desktop-upstream、arduino-libs；输出 work/native/mixly。不要在完成分发准备后重跑基础 App Inventor staging。

源代码链接：
- https://gitee.com/mixly2/mixly2.0_src
- https://gitee.com/mixly2/mixly2.0-win32-x64
- https://gitee.com/mixly2/arduino-libs
- https://github.com/arduino/arduino-cli/tree/v0.35.3
- https://github.com/arduino/ArduinoCore-avr/tree/1.8.6
- https://github.com/esp8266/Arduino/tree/3.1.2
- https://github.com/espressif/arduino-esp32/tree/2.0.17

安装目录 mixly/src 包含所选环境和共用模块的适配源码；resources/distribution-source/mixly-adaptation 保存生成脚本及启动适配。测试入口不会打包。
