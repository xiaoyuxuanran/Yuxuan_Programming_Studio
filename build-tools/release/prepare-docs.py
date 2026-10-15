"""Prepare 2.2.0 candidate documents without replacing the stable outputs."""
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
BASELINE = WORKSPACE / 'outputs'
TARGET = Path(__file__).resolve().parent / 'docs'
TARGET.mkdir(parents=True, exist_ok=True)

if '羽轩编程工作台 2.1.0' not in (BASELINE / '使用说明.txt').read_text(encoding='utf-8-sig')[:100]:
    raise RuntimeError('This migration renderer requires the stable 2.1.0 baseline; do not rerender finalized 2.2.0 documents')

usage = (BASELINE / '使用说明.txt').read_text(encoding='utf-8-sig').replace('羽轩编程工作台 2.1.0', '羽轩编程工作台 2.2.0', 1)
usage = usage.replace('首次运行会自动准备独立项目环境及内置 Pygame，不需要联网。', '首次运行从内置 wheel 快速准备独立项目环境及 Pygame，不需要联网。已有环境升级时保留用户安装的依赖。')
usage = usage.replace('编译失败不会运行旧程序。', '编译失败不会运行旧程序。C++ 再次运行会先检查代码及头文件变化，未变化时复用编译结果。', 1)
usage = usage.replace('搜索与安装新库需要网络；', '搜索与安装使用 Windows 系统信任及内置 CA 证书进行 HTTPS 校验；不会通过关闭证书校验规避错误。搜索与安装新库需要网络；', 1)
old = '在“项目”菜单新建项目，或导入 examples 中的 HelloOfflineTest.aia；在“组件设计”和“逻辑设计”中编辑，使用“打包 → 打包为.apk格式”生成 APK。'
new = '''在“项目”菜单新建项目，或导入 examples 中的 HelloOfflineTest.aia；在“组件设计”和“逻辑设计”中编辑，使用“打包 → 打包为.apk格式”生成 APK，然后下载到本地。APK 结果窗口已移除扫码下载。
APK 构建使用随包部署的预处理 DEX 与只读构建资源，缩短新电脑首次编译等待；本机最小样例首次构建由106.0秒降至17.9秒，实际耗时随项目和机器变化；含新第三方扩展的项目仍可能需要首次生成该扩展的缓存。构建等待保留有限超时，不会把失败状态当作编译成功。

App Inventor USB 运行与调试
在 Android 手机中打开开发者选项和 USB 调试，用支持数据传输的 USB 线连接电脑，并在手机上允许这台电脑。必要时安装手机厂商的 Android ADB 驱动；开发板 CH340 等串口驱动不能代替手机驱动。
点击 App Inventor 顶部“USB 调试”，在“运行设备”中选择已连接的手机，点击“运行”。软件会保存当前项目、构建 APK、通过 USB 更新安装，并启动应用；之后可点击“读取应用日志”查看运行结果。首次连接或部分品牌的“USB 安装”需要在手机上确认。
待手机授权、离线或断开的设备不能运行；点击“刷新”重新检查。此面板只列出 USB 手机，不使用无线设备或模拟器。
更新安装保留同签名应用的数据。签名不同、旧版本覆盖新版本或手机拒绝安装时，面板显示原因，不会自动卸载手机已有应用。按提示在手机上处理后再运行。
可反复运行当前或不同项目。意外退出后残留的过期临时安装文件会自动清理。手动下载保存的 APK 位于你选择的下载目录。
同时使用其他 Android 工具时，退出本工作台后，另一工具如显示设备离线，可刷新其设备列表，必要时重新连接手机。
此功能提供构建、安装、启动和应用日志；没有 Android Studio 的断点调试器。软件内置 ADB，不需要另外安装 Android Studio。'''
if old not in usage:
    raise RuntimeError('App Inventor baseline instruction changed')
usage = usage.replace(old, new)
usage = usage.replace('运行日志保存在 logs 中，用于排查故障；', 'App Inventor USB 临时安装文件和进程状态位于数据目录 usb，构建缓存位于 cache；它们不是项目备份。运行日志保存在 logs 中，用于排查故障；', 1)
usage += '\n本次 USB 功能已验证模拟安装、真实 APK 清单解析及本地接口；验收时未连接真实 Android USB 手机，手机端安装、启动和应用日志未做真机测试。\n'
(TARGET / '使用说明.txt').write_text(usage, encoding='utf-8')

handoff = '''# 羽轩编程工作台 2.2.0 工程交接（发布准备）

当前工作版本 2.2.0 在 2.1.0 上增加 App Inventor USB 运行、删除 APK 扫码下载、优化首次 APK/代码环境准备，以及修复第三方库搜索 HTTPS 证书校验。2.1.0 稳定交付保留在 outputs；2.2.0 安装器和最终发布哈希尚待验证，以下历史安装检查不代表新包通过。

## 本次源码与构建

原 App Inventor 基线仍为 c76a58ce7d8b9723107ea980046ca95e1ddf936e。work/appinventor-ui 保存 TopToolbar、ShowBarcodeCommand、ShowProgressBarCommand、WaitForBuildResultCommand 的完整 GWT 源码和逐文件 patch，以及 OfflineUsbAction/OfflineUsbServlet、本地 USB 面板 CSS/JS、GWT/Java 编译与 WAR staging 脚本。更改 WAR 后同步 resources/build-version.txt；现有 authkey、keystore、数据库仍须保留。

work/native/usb/server.py 使用内置 Python 3.13 启动，只监听回环地址；浏览器经已登录、同源 Java servlet 调用。随机控制令牌只存在服务器进程环境，网页不直接获取令牌、路径或任意 ADB 命令。仅允许当前本机 App Inventor project-output APK，限制包大小、拒绝跳转，标准库读取二进制 AndroidManifest.xml。安装用 adb install -r；按 APK 中已校验的包名及启动 Activity 启动。应用日志限于本次服务已部署的应用。

Google 官方 Platform Tools 37.0.1 / ADB 37.0.1-15733141 部署在 usb/platform-tools，完整 NOTICE、source.properties、ZIP 与6个分发文件的 SHA256 锁保留。work/usb/prepare-platform-tools.ps1 从官方地址获取，最新 ZIP 与锁不符时拒绝继续。工作台不自动安装手机系统驱动。USB任务仅限制同时活跃任务，已结束任务按64条历史容量回收，不再有累计64次运行上限；受管临时APK在任务结束清理；后续启动仅按24小时阈值清理精确命名deploy-32hex.apk的过期文件，保护近期文件、链接、目录及被占用文件。清理只处理本服务管理的临时安装文件。

ADB共存：平台不执行全局kill-server，已有daemon可复用。如果5037 daemon由本平台首次建立并加入本平台Windows Job，后来其他工具共享它，本平台退出关闭Job时该daemon也可能结束；其他工具需重新刷新/连接。不能承诺所有共存情况下退出均不中断其它工具。

work/build-speed/prepare-overlays.py 生成 ProjectBuilder、Execution、Resources、RunD8 覆盖源码；prepare-dex-seed.py 与 prepare-resource-seed.py 生成安装包所用的静态种子，benchmark.py 在独立数据目录生成真实 APK 与各阶段耗时。缓存按编译环境及内容建立键，采用临时目录和原子发布，避免未完成 DEX 被后续构建复用。实际生成的 DEX/资源种子进入安装包，源码 ZIP 仅交付生成和验证脚本。

work/native/studio/runtime_support.py 直接安装内置 wheel 并生成符合 pip 规则的 RECORD；venv 用 --without-pip，避免 ensurepip/升级 pip/安装 Pygame 的额外进程和扫描。3.8 使用 pip24.3.1，3.13 使用 pip26.2.1；不同项目和版本的依赖保持隔离，迁移旧环境仍保留用户依赖。marker 由 gui-1 升为 gui-2。

C++ 默认 C++17 -O0 -Wall -Wextra，不再生成未使用的 -g 调试信息。每次运行先完整预处理，用源代码、所有实际头文件、__has_include 和编译宏形成内容键；编译该快照，避免外部编辑竞态。匹配缓存才运行已有 exe；编译失败不运行旧 exe。Clang23 对中文 #line 文件名的八进制转义兼容问题，仅在行标记路径内规范化为 UTF-8，保留程序字符串语义。

PyPI 搜索使用 pip 内置 truststore 的 Windows CryptoAPI 证书链校验并加载 Mozilla CA。Python3.8 pip 通过 Windows server-auth 根证书与 Mozilla CA 合并文件进行 HTTPS 验证；保留明确的用户 CA/代理配置。证书与主机名校验均启用，未使用 --trusted-host 或不安全 SSLContext。参考：https://pip.pypa.io/en/stable/topics/https-certificates/ 、https://pypi.org/project/truststore/ 。

## 本次验证与边界

Studio 46 项检查已通过，证据 work/studio/optimization-results.json：17项优化/TLS、20项API与真实清华源 pip、6项两版本图形窗口、3项旧环境/搬迁保留依赖及播种 wheel 卸载重装。单独环境准备基线3.8=13.995秒、3.13=6.906秒；优化后分别1.918秒、1.894秒。C++ 在并行验收期间的样例首次1.753秒、重复0.524秒；实际速度随项目、磁盘和机器负载变化。

USB helper 16项模拟用例及真实生产JS在DOM/network stub下12项状态/竞态回归通过，官方 ADB 实际枚举0台设备。私有端口的真实ADB在Windows Job中启动并随Job退出验证通过；首次启动自动准备daemon，避免将localhost误标为remote。真实APK清单解析和12项已登录servlet本地API检查通过；手机端安装、启动和日志仍未真机测试。新增功能不承诺完整 Android Studio 断点调试。真实开发板烧录/串口、物理断网和 Windows10 实机限制仍沿用。

真实APK最小样例冷构建106.023→17.944秒，缩短83.08%；第二次19.453秒；min-api19另一个真实签名APK18.591秒，命中35个内置DEX种子。135份资源（124306658字节）和156份DEX（41827724字节）的来源/缓存键/完整性验证及10项损坏回退与取消检查通过；污染DEX种子后的两轮真实APK构建均成功，第一轮回退生成，第二轮复用私有缓存。15分钟预算到时取消compiler、结束子进程并关闭executor；Kawa warning本身不等于编译失败。原5分钟冷构建超时不再提前结束正常慢项目。

完整浏览器开发集成已通过：真实项目编辑/保存、YAIL生成、APK构建与本地下载；结果窗口没有二维码。通过模拟USB手机完成真实APK下载及清单解析、install -r、am start、pidof和logcat，页面显示已安装并启动与应用日志。此流程仅ADB设备命令模拟，项目/构建/下载/清单是真实服务；无真机。

新安装包升级/卸载和新包哈希等待 release owner 完成；不能复用2.1记录填成2.2通过。

源码打包脚本 work/mixly/package-source-release.py 支持 --version（默认2.2.0）与 --documents。候选文档在 work/release-2.2/docs；源码 staging 按版本隔离在 work/release-2.2.0/source-delivery，临时ZIP在 work/mixly/source-release-2.2.0.zip。未完成安装器前不要覆盖 outputs 稳定发布。归档逐文件 SHA256/CRC、UTF-8 文件名、真实激活码/私钥/用户状态/日志审查；许可与上游锁保留。

## 2.1.0 历史交接原文

以下完整保留上一版记录，其中“当前”“本次”和安装哈希均指2.1.0时期。

'''
handoff += (BASELINE / '工程交接.md').read_text(encoding='utf-8-sig')
(TARGET / '工程交接.md').write_text(handoff, encoding='utf-8')

acceptance = '''# 2.2.0 验收记录（发布准备，2026-10-04）

以下为新功能开发输入的已完成检查；新安装包尚未完成构建/安装验收，不记为成品交付。2.1.0 历史记录保留在后半部分。

## Python / C++ / HTTPS

- 17项专门验收通过：双版本首次与重复运行、pip元数据、C++首次/复用、修改头文件、新增__has_include头文件重编译、失败不运行旧exe、PyPI与清华真实HTTPS、未信任证书拒绝、可信证书错误主机名拒绝。
- 现有20项API验收全部通过，包括双版本真实运行、输入/停止、C++错误、主题、代码提示、路径约束、真实清华源colorama安装和版本依赖隔离。
- Python3.8.9/3.13.16的Tkinter、Turtle、Pygame六个真实Windows窗口通过；3项旧环境/搬迁保留用户依赖、wheel正常pip卸载重装通过。
- 顺序单独测量：旧3.8项目准备13.995秒→1.918秒，旧3.13为6.906秒→1.894秒；优化后的普通Python重复运行约0.08秒。C++在并行验收期间的样例首次1.753秒、重复0.524秒。并行完整验收因负载更高，耗时保留在原始JSON；这些是本机样例，不是任意项目的固定耗时。

证据：work/studio/optimization-results.json；脚本test-runtime-optimization.py、run-runtime-acceptance.py。

## USB 与 App Inventor

USB helper的16项模拟测试和前端生产JS的12项DOM/network stub回归通过，实际官方ADB枚举列表为空。设备授权/断线、命令约束、同源控制、APK清单和安装异常均有检查。模拟安装与真实APK清单/本地API验证不能代替真实手机；未进行真实AndroidUSB安装、启动或日志验证。

12项真实servlet API检查通过：会话/同源约束、实际ADB枚举、输入大小与格式、任意APK地址拒绝、无真机时拒绝安装等。本次GWT删除扫码结果并增加USB运行。真实APK冷构建106.023秒→17.944秒，第二次19.453秒；min-api19真实签名APK18.591秒并命中35个内置DEX种子。旧基线106秒中RunD8约95.7秒，优化后约9.4秒。10项资源/DEX缓存完整性、内容键及取消检查通过；损坏种子回退的两轮APK也签名成功。种子覆盖min-api14/19，其他版本/扩展首次仍需生成各自缓存；实际速度因机器和项目变化。构建最大预算5分钟调整至15分钟，到期取消编译器并结束子进程。真实浏览器完成项目保存、YAIL生成、APK打包及本地下载，二维码已移除。下载APK为3765790字节、SHA256 690A5C3F0179E2944B24281D24DCFBFB2325DF0FBC3AD107A5D49C3F56857C9D，包含classes.dex/classes2.dex。另经模拟手机完成真实AppEngine APK下载和二进制清单解析，再模拟安装、启动及应用日志，页面显示done并可读取日志；没有真实手机。还修复已结束USB任务累计64次造成后续429及强制退出遗留临时APK；反复运行不受累计历史次数限制，过期受管APK自动清理。真实ADB共存不执行kill-server、复用已运行daemon；本平台先创建5037 daemon后被其它工具共享时，平台Job退出可能使其结束，另一工具需重连。两项新增边界回归通过：超过64次（71次）运行仍可继续，以及精确受管APK清理边界。安装器结果仍待同步。

证据：work/usb/acceptance.json（physicalInstallationTested=false，mockTests=16）、work/usb/frontend-acceptance.json、work/appinventor-ui/api-results.json、work/usb/adb-lifecycle-acceptance.json及相应测试源码；work/build-speed/acceptance.json；work/appinventor-ui/ui-results.json以及usb-panel.png/local-download.png/usb-flow-simulated.png。安装器证据发布前补全。

## 发布门槛

安装器、升级用户数据保留、新安装文件哈希、服务启动退出和源码ZIP一致性待验证。新包体积/SHA256待生成。以下2.1.0升级、长路径、安装、授权和卸载检查仅为历史基线。

## 2.1.0 历史验收原文

'''
acceptance += (BASELINE / '验收记录.md').read_text(encoding='utf-8-sig')
(TARGET / '验收记录.md').write_text(acceptance, encoding='utf-8')

progress = '''# 项目进度（2.2.0发布准备，2026-10-04）

本次在2.1.0上完成四项优化：App Inventor本地APK下载与USB运行、Python/C++启动和复用速度、安全HTTPS库搜索、APK首次构建优化。2.2.0安装器尚待构建验收，outputs仍为已完成的2.1.0稳定发布。

Python/C++/TLS 46项检查通过，USB helper16项模拟检查及前端12项状态/竞态回归通过，实际ADB枚举0台手机。12项真实servlet API检查通过；真实APK冷构建106.023→17.944秒（83.08%），第二次19.453秒，min-api19真实签名APK18.591秒；10项缓存完整性/损坏回退/取消检查及污染种子两轮APK构建通过。完整GWT浏览器的本地APK下载和真实构建/下载/清单加模拟手机安装启动日志流程通过。安装器升级/退出/源码归档校验待同步。未连接Android真机，手机实际安装、启动和日志未验证；实物开发板与物理断网限制保留。

候选说明在work/release-2.2/docs；发布成功前不会覆盖原稳定安装器或其说明与哈希。源码ZIP使用2.2.0独立staging并排除私钥、真实激活码、用户项目/授权/日志和生成缓存。

## 2.1.0历史进度原文

'''
progress += (BASELINE / '项目进度-2026-10-02.md').read_text(encoding='utf-8-sig')
(TARGET / '项目进度-2026-10-02.md').write_text(progress, encoding='utf-8')
print('Prepared four candidate documents in', TARGET)
