# 2.3.0 → 2.3.1 增量升级

保存项目并退出工作台，运行 `Yuxuan-Programming-Studio-Update-2.3.0-to-2.3.1.exe`，选择原安装目录。

这是实际文件差异包，不包含整套运行环境。只支持完整 2.3.0，也可重装以修复同一 2.3.1。安装前检查基础文件及 SHA256；不匹配时不会继续。项目、Python 依赖和激活状态保留，卸载记录与原安装合并。

首次安装或当前为 2.2.0：先运行 [2.3.0 完整安装包](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.0)，再应用本增量包。2.2.0 本次不修改。

升级后主页面可查看日志、优先检查 Gitee 最新正式版，失败时回退 GitHub。将来发布适用的增量包时优先下载增量包，否则使用该版本提供的完整安装包。

请使用 `SHA256SUMS.txt` 校验附件。此版本新增内容见 `CHANGELOG.txt`；真实手机与硬件蓝牙通信未测试。

Gitee 版本页面：https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases 。单附件限制 100 MB，本增量包可直接下载；2.2.0 / 2.3.0 完整包使用对应页面中的 GitHub 链接。
