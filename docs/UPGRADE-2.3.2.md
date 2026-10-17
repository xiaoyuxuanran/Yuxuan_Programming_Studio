# 升级到 2.3.2

保存所有工程并退出工作台、Mixly 和代码运行窗口，再运行与当前版本对应的更新包，选择原安装目录。

| 当前版本 | 升级方式 |
| --- | --- |
| 2.2.0 | 直接运行 `Yuxuan-Programming-Studio-Update-2.2.0-to-2.3.2.exe`，无需中间版本 |
| 2.3.1 | 运行 `Yuxuan-Programming-Studio-Update-2.3.1-to-2.3.2.exe` |
| 2.3.0 | 先应用 2.3.0 → 2.3.1 增量包，再应用 2.3.1 → 2.3.2 更新包 |
| 首次安装 | 先安装完整 2.2.0，再使用 2.2.0 → 2.3.2 直升包 |

更新包检查基础文件，拒绝空目录或不匹配的版本；可重复运行修复本版本。项目、激活信息、Python 依赖和用户扩展库保留，卸载记录与原安装合并。升级前建议备份 `%LOCALAPPDATA%\AppInventorOffline` 及外部保存的工程。

Mixly 切回 2.2.0 同款 2.0-rc4 桌面客户端，本版不提供仿真。**从 2.3.x 网页版升级前，请先将工程另存为 `.mix` 文件，升级后在桌面版打开。** 浏览器草稿和扩展数据保留，但网页扩展与旧桌面扩展格式不同，需要兼容的桌面版本。2.2.0 的桌面草稿、ThirdParty 和 myLib 继续保留。

App Inventor 的优质扩展、积木拖拽删除、USB 调试，以及 Python / C++ 工作区继续保留。

下载优先使用 [Gitee 2.3.2](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/tag/v2.3.2)，也可使用 [GitHub 备用](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.2)。下载后可与 `SHA256SUMS.txt` 核对文件；软件内更新也会检查大小和 SHA256。
