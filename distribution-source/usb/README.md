# Android USB 运行桥

App Inventor 可以将当前项目构建成 APK 后，通过 USB 安装到选定手机并启动。请在 Android 手机中打开开发者选项、USB 调试，连接具有数据传输能力的 USB 线，并在手机上允许这台计算机。部分品牌还要求打开“USB 安装”并确认安装提示。电脑无法识别手机时，需要手机厂商的 Android ADB 驱动；CH340 等串口驱动适用于开发板，不能代替手机 ADB 驱动。

安装使用 `adb install -r`，保留同签名应用已有的数据。签名不同或版本号降低时给出明确说明，不自动卸载原应用。应用启动后可查看其进程日志。手机未授权、断开或离线时，运行被阻止并提示修复方法。

任务历史最多保留 64 条，达到上限时淘汰最旧的已完成记录，不限制累计运行次数，也不淘汰正在运行的任务。部署临时 APK 在任务结束时删除；异常退出留下的文件在下次启动时按 24 小时阈值清理，仅处理本目录中精确命名为 `deploy-32位小写十六进制.apk` 的普通文件，跳过最近文件、目录、链接和暂时被占用的文件。

ADB 使用本机默认 5037 服务。已有其它工具启动的 ADB 服务会被复用，本工作台不会发出全局 `kill-server`。如果 ADB 服务由本工作台首次创建，它属于工作台的 Windows 进程组，退出时会停止；其它工具后来共享这个服务时，共享连接可能需要重新建立。

后端由 Core 使用内置 Python 3.13 启动，绑定 127.0.0.1。启动参数是 `--port USB端口 --app-port AppInventor端口 --data 用户目录/usb`；随机令牌通过进程环境 `YX_USB_TOKEN` 传入，启动后从子进程环境移除。令牌不会进入网页或命令行。

App Inventor 的同源、已登录 Java servlet 代理 `/ode/usb/*` 到 `/api/*`，带上 `X-Offline-Control` 与服务端读取的 App Inventor 会话 Cookie。浏览器不能选择文件路径、下载地址或任意 ADB 命令。唯一允许的 APK 来源是当前本机服务的 `/ode/download/project-output/数字/Android`，下载不使用代理且拒绝跳转。APK 中的二进制清单由标准库解析，启动的应用与 Activity 必须通过标识校验。

- `GET /health`：本机健康检查 `YuxuanUsb/1`。
- `GET /api/devices`：USB 设备、状态、型号与提示。无线设备与模拟器不在列表中。
- `POST /api/install`：`{"serial":"设备序列号","downloadPath":"/ode/download/project-output/123/Android","cookie":"由Java服务端加入"}`，返回任务 ID。
- `GET /api/job?id=任务ID`：状态 `running`、`done` 或 `failed`，阶段和运行输出。
- `GET /api/logcat?serial=设备序列号&package=包名`：只允许本次服务已经部署的应用，返回最多 250 行、64 KiB 的进程日志。旧 Android 不支持 `--pid` 时，结果仍按目标进程过滤。

内置 Google 官方 Platform Tools 37.0.1 / ADB 37.0.1-15733141，仅分发 ADB 所需文件，保留完整 `platform-tools/NOTICE.txt`。原 ZIP 与每个交付文件的 SHA256 记录在 `platform-tools-lock.json`。使用 `work/usb/prepare-platform-tools.ps1` 可从 Google 官方地址获取并校验；官方 latest 更新后脚本会停止，等待新版审核。测试：`work/native/runtime/python3.13.16/python.exe work/usb/test_usb.py`。

官方参考：[ADB](https://developer.android.com/tools/adb)、[Platform Tools](https://developer.android.com/tools/releases/platform-tools)、[Logcat](https://developer.android.com/tools/logcat)。
