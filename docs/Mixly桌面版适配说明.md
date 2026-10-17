# Mixly 桌面版适配与重建

2.3.2 使用 [Mixly 2.0 源码](https://gitee.com/mixly2/mixly2.0_src) 的 `2.0-rc4`，提交 `a7d91f1e3c621a3132fb8ea38c92877bb0834830`。官方 Windows Electron 19.0.6 及原生依赖来自 `mixly2.0-win32-x64` 提交 `d1bb6950c91f3b8f68d571188393b3d6b6603eb7`；Arduino 库基线提交 `2b7ca7d23afec725d23f80b3d995d4cf5fa57a01`。详细记录见 `distribution-source/mixly-adaptation/UPSTREAM.json`。

准备原开发目录 `work/mixly/{upstream,desktop-upstream,arduino-libs}`，将 `distribution-source/mixly-adaptation` 中的适配文件放回 `work/mixly`。`prepare-mixly.py` 输出 `work/native/mixly` 并调用 `fix-desktop.py`；后者应用单次草稿恢复、串口关闭按钮、官方 HTTPS 云库备用源和经典 ESP32 蓝牙修复。`upstream-overlays/mixly2` 保存修改后的上游文件，供审阅和核对。

`workspace-recovery.js` 阻止上游 localStorage 与文件草稿重复追加，原积木和手写代码分别恢复。`compiler-paths.py` 使用当前用户本地缓存中的编译器目录联接，绕开旧 GCC 展开私有头文件路径时的长度限制；ESP32 SDK 仍通过 response 文件传入。目录联接仅指向已安装工具，不删除目标 SDK，不修改系统 PATH。

平台运行环境、App Inventor 源码与构建准备沿用 2.2.0 / 2.3.0 发布附件；本仓库不包含全部预构建依赖。启动器代码位于 `distribution-source/Suite*.cs`，按原 `BuildRelease.ps1` 使用 .NET Framework 编译器编译。`prepare-package.py` 需要原版实际安装的 `base-2.2.0.json` 和 `base-2.3.1.json` 清单，再与 `work/native` 比较，生成两种更新包；`snapshot-installed.py` 可生成基线快照。Inno 脚本的绝对开发路径需按本机调整；2.3.1 包使用 LZMA2 256 MiB 字典压缩，构建约需 3 GB 内存。

2.3.0 / 2.3.1 的 `distribution-source/mixly4` 与 `upstream-overlays/mixly4` 留作历史源码；2.3.2 运行入口使用桌面适配，不提供仿真。App Inventor 的 2.3.1 扩展和 Blockly 修改继续沿用，未回滚。

验收脚本位于 `validation/release-2.3.2`，使用临时安装目录及已有测试授权；运行前按本机路径配置，不能在个人正式安装目录运行。安装验收保存并恢复卸载注册和快捷方式，检查增量覆盖、重复覆盖、数据保留和合并卸载。测试授权与日志不随公开源码发布。
