# 羽轩编程工作台 · Yuxuan Programming Studio

Windows x64 本地编程平台，集成 App Inventor、Mixly 桌面编程、Python 和 C++。当前版本 **2.3.4**。

## 下载与升级

[Gitee分版本发布页](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/tag/v2.3.4) · [GitHub完整附件](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.4)

| 当前版本 | 使用的更新包 |
| --- | --- |
| 2.2.0 | [2.2.0 → 2.3.4](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/download/v2.3.4/Yuxuan-Programming-Studio-Update-2.2.0-to-2.3.4.exe) |
| 2.3.1 | [2.3.1 → 2.3.4](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/download/v2.3.4/Yuxuan-Programming-Studio-Update-2.3.1-to-2.3.4.exe) |
| 2.3.2 | [2.3.2 → 2.3.4](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/download/v2.3.4/Yuxuan-Programming-Studio-Update-2.3.2-to-2.3.4.exe) |
| 2.3.3 | [2.3.3 → 2.3.4](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/download/v2.3.4/Yuxuan-Programming-Studio-Update-2.3.3-to-2.3.4.exe) |
| 2.3.0 | 先升级至2.3.1，再使用本版对应包 |
| 首次安装 | 安装[完整2.2.0](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.2.0)，再使用2.2.0直升包 |

本次更新包含全部56课本地资料，体积较大。保存工程并退出软件，运行匹配的更新包并选择原安装目录；保留项目、依赖和激活信息。已安装教学预览的2.3.3也可更新。[详细升级说明](docs/UPGRADE-2.3.4.md)。

更新清单优先从Gitee读取，只登记上传成功的镜像；超出Gitee附件限制的大文件使用GitHub完整附件。安装包校验大小和SHA256。

## 56课教学项目

- 8阶段、56课，每课90分钟，共84小时。创意表达、编程基础、动画游戏、声音传感器、数据工具、网络应用、ESP32物联网、毕业项目依次推进。
- 168个工程：每课含完整答案、课堂支架、纯界面起始版，可直接打开到个人工作区。
- 56份可编辑PPT及备注、教案、学生任务单、素材、真实积木参考图和答案APK。网络课程附Python课堂服务；硬件课程附串口、经典蓝牙、BLE及Wi-Fi TCP固件与接线说明。
- 教学首页右侧课程路线占半屏；个人项目表格、切换按钮、文件夹和资料入口统一蓝白布局，适配窄窗口。中文课程文件夹可用；内部工程标识采用英文数字以兼容编译链。
- 修复Windows本地项目存储长键名与NTFS流问题，兼容旧文件迁移、删除。

![教学项目与课程路线](docs/images/2.3.4-teaching.png)

[课次内的工程与资料入口](docs/images/2.3.4-lesson.png) · [个人项目布局](docs/images/2.3.4-projects.png)

课程资料已随更新安装，可在App Inventor“我的项目 → 教学项目”中使用；也可单独下载发布附件中的8个阶段资料包。下载后解压，先阅读各课“先读我”。

168个AIA通过平台导入与积木检查，56份答案APK编译完成；56份PPT共1347页经过逐页渲染检查。课堂API在Python3.8.9及3.13.16验证；六份ESP32固件在2.0.17核心编译。**未进行Android真机或实物开发板联调**，权限、传感器和通信功能请按教案在设备上验收。

## 功能与文档

App Inventor 默认经典布局、蓝白主题，支持本机 APK 构建下载、USB 安装运行及应用日志。Python 支持 3.8.9 / 3.13.16、项目环境隔离、Tkinter / Turtle / Pygame、第三方库搜索及清华源安装；C++ 使用内置 Clang++、C++17 和编译缓存。代码编辑器提供文件树、运行结果、基础提示以及 Light / Dark 主题。

主页面提供更新日志、检查更新；优先 Gitee，失败回退 GitHub，下载校验大小和 SHA256。

- [使用说明](docs/使用说明.txt)、[更新日志](CHANGELOG.txt)
- [Mixly 桌面版适配与构建](docs/Mixly桌面版适配说明.md)
- `distribution-source/`：平台源码与适配脚本；`upstream-overlays/`：上游修改；`validation/`：验收脚本。
- [历史 Mixly 网页版说明](docs/Mixly网页版迁移说明.md)，仅对应 2.3.0 / 2.3.1。

本仓库不包含全部预构建依赖。2.3.4 的 `Source-and-Patches.zip` 提供本次源码与补丁；完整上游源码基线沿用 2.2.0 / 2.3.0 发布附件，目录准备见构建说明。

## 许可与验证范围

各上游项目及适配文件沿用原版权声明与许可证，见 `licenses/` 和文件头；Mixly 作者为 Mixly Team@BNU, CHINA，源码与固定提交见适配说明。历史网页源码保留以供追溯。品牌图片不代表上游官方背书。

已验证四类编辑器、草稿反复恢复及进程重启、串口关闭、云库获取及导入、Arduino 本机编译和经典 ESP32 蓝牙生成编译。升级包验证原版安装后的覆盖、重复覆盖、数据保留和合并卸载；未连接真实开发板或 Android 手机。
