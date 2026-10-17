# 升级到 2.3.3

保存工程并退出工作台、Mixly 及运行中的代码窗口，选择与当前版本匹配的更新包，安装到原目录。

| 当前版本 | 更新包 |
| --- | --- |
| 2.2.0 | `Yuxuan-Programming-Studio-Update-2.2.0-to-2.3.3.exe`，直接升级，无需中间版本 |
| 2.3.1 | `Yuxuan-Programming-Studio-Update-2.3.1-to-2.3.3.exe` |
| 2.3.2 | `Yuxuan-Programming-Studio-Update-2.3.2-to-2.3.3.exe`，小型更新包 |
| 2.3.0 | 先升级至 2.3.1，再使用对应更新包 |
| 首次安装 | 先安装完整 2.2.0，再使用 2.2.0 → 2.3.3 直升包 |

2.3.3 包含 2.3.2 的 Mixly 桌面回退、积木重复恢复、串口关闭按钮、云端库备用源和 ESP32 蓝牙修复，并新增 Python / C++ 字号缩放和侧栏开关。

代码区上方的 **A− / A+** 调整字号，点击中间字号恢复 14 px；支持 **Ctrl+-、Ctrl++、Ctrl+0、Ctrl+滚轮**，范围 10–32 px，运行输出随之调整。左侧最上方按钮或 **Ctrl+B** 隐藏/显示侧栏，点击当前文件/库图标也可收起。设置保存到 `studio\studio.json`，关闭重开和切换语言后保留。

项目、依赖及激活信息保留，允许重复更新，卸载记录合并。升级前建议备份 `%LOCALAPPDATA%\AppInventorOffline` 及外部工程。**从 Mixly 网页版切回前先另存 `.mix`，再在桌面版打开。** 网页草稿和插件数据保留，但需要兼容的桌面扩展。

下载优先使用 [Gitee 2.3.3](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/tag/v2.3.3)，备用为 [GitHub](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.3)。`SHA256SUMS.txt` 提供附件校验值；软件内更新也检查大小及 SHA256。
