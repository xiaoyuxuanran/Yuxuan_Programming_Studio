from pathlib import Path
import json,shutil,zipfile,re,hashlib,runpy,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REPO=ROOT/'work/github-publish/Yuxuan_Programming_Studio';NATIVE=ROOT/'work/native'
shutil.copytree(NATIVE/'resources/distribution-source',REPO/'distribution-source',dirs_exist_ok=True)
shutil.copy2(NATIVE/'mixly/UPSTREAM.json',REPO/'distribution-source/mixly-adaptation/UPSTREAM.json')
for source,target in [('使用说明.txt','docs/使用说明.txt'),('UPGRADE.md','docs/UPGRADE-2.3.3.md'),('CHANGELOG.txt','CHANGELOG.txt')]:shutil.copy2(HERE/source,REPO/target)
folder=REPO/'validation/release-2.3.3';folder.mkdir(parents=True,exist_ok=True)
for name in ['studio-view-check.cjs','installed-smoke.py','acceptance-final.ps1','UpdateCompatibilityCheck.cs','UpdateNetworkCheck.cs']:
 shutil.copy2(HERE/name,folder/name)
folder=REPO/'distribution-source/release-2.3.3'
for name in ['prepare-github.py','Update-2.2.0.iss','Update-2.3.1-ultra256.iss','Update-2.3.2.iss','update-manifest-2.2.0.json','update-manifest-2.3.1.json','update-manifest-2.3.2.json']:
 shutil.copy2(HERE/name,folder/name)
for name in ['python-light.png','cpp-dark.png']:shutil.copy2(HERE/'studio-ui'/name,REPO/'docs/images'/('2.3.3-'+name))
readme=subprocess.run(['git','show','v2.3.2:README.md'],cwd=REPO,capture_output=True,text=True,encoding='utf-8',check=True).stdout.replace('2.3.2','2.3.3')
readme=readme.replace('| 2.3.0 |','| 2.3.2 | [2.3.2 → 2.3.3 小型更新包](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/download/v2.3.3/Yuxuan-Programming-Studio-Update-2.3.2-to-2.3.3.exe) |\n| 2.3.0 |')
readme=readme.replace('## 本次修改\n','## 本次修改\n\n- Python / C++ 新增 A− / A+ 字号按钮、中间字号恢复默认，以及 Ctrl++ / Ctrl+-、Ctrl+0、Ctrl+滚轮。范围 10–32 px，运行输出同步调整。\n- 左侧新增侧栏隐藏/显示按钮与 Ctrl+B；文件/库图标也可收起/展开。字号和侧栏设置保存在工作区，重启和切换语言后保留。\n')
readme=readme.replace('## 功能与文档','![Python 字号与侧栏控制](docs/images/2.3.3-python-light.png)\n\n[C++ 深色主题预览](docs/images/2.3.3-cpp-dark.png)\n\n## 功能与文档')
(REPO/'README.md').write_text(readme,encoding='utf-8')
notes='''羽轩编程工作台 **2.3.3**，Windows x64。

### 新增操作

- **字体缩放**：Python / C++ 顶部新增 A−、A+ 和字号恢复默认。支持 Ctrl++ / Ctrl+-、Ctrl+0、代码区 Ctrl+鼠标滚轮，范围 10–32 px；运行输出字号同步调整。
- **侧栏开关**：左侧最上方按钮及 Ctrl+B 隐藏/显示侧栏，点击当前文件/第三方库图标也可收起、展开。隐藏时编辑区自动填满。
- 字号和侧栏显示状态保存到工作区，重新启动及切换 Python / C++ 后保留；工具栏适配较窄窗口，Light / Dark 均可使用。

包含 2.3.2 的全部修改：Mixly 回到 2.2.0 同款桌面版，无仿真；修复积木重复恢复、代码视图恢复和串口关闭按钮；保留四类硬件、云端库与官方 Gitee 备用源、驱动入口和经典 ESP32 蓝牙修复。App Inventor 的优质扩展、积木拖拽删除和 USB 调试继续保留。

### 更新包

- **2.2.0 → 2.3.3**：直接升级，无需中间版本。
- **2.3.1 → 2.3.3**：补齐切回桌面 Mixly 所需文件。
- **2.3.2 → 2.3.3**：仅包含本次新增操作的小型更新包。
- 2.3.0 先升级到 2.3.1；首次安装先安装完整 2.2.0，再使用直升包。

保存工程并退出，选择原安装目录。更新保留项目、依赖和激活信息，支持重复覆盖及合并卸载。**从 Mixly 网页版切回前先另存 `.mix` 工程**，桌面扩展需使用兼容格式。

[Gitee 下载](https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases/tag/v2.3.3) · [GitHub 备用](https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/tag/v2.3.3)。软件检查和下载更新优先 Gitee，失败回退 GitHub，均检查大小和 SHA256。

附件提供三个对应更新包、源码与补丁、使用/升级说明、更新日志、SHA256 校验值及公开更新清单。完整上游源码基线沿用此前 2.2.0 / 2.3.0 发布附件。

已验证 Python / C++ 实际运行、明暗主题及多种窗口宽度、按钮和快捷键、侧栏收起/展开、字号边界、无代码内容变化，以及服务和浏览器重启后的设置保留。已在原版 2.2.0 安装基础上验证更新与数据保留；Mixly 组件与通过两条原版升级路径完整验收的 2.3.2 一致。未连接实物开发板或 Android 手机。
'''
(HERE/'release-notes.md').write_text(notes,encoding='utf-8')
for source,target in [('使用说明.txt','User-Guide.txt'),('UPGRADE.md','UPGRADE.md'),('CHANGELOG.txt','CHANGELOG.txt')]:shutil.copy2(HERE/source,HERE/'package'/target)
secret=runpy.run_path(str(ROOT/'work/release-2.3.1/gitee-publish.py'))['token']().encode()
report={'files':0,'bytes':0};bundle=HERE/'package/Source-and-Patches.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(REPO.rglob('*')):
  if not p.is_file() or '.git' in p.relative_to(REPO).parts:continue
  rel=p.relative_to(REPO).as_posix()
  if rel=='update.json':continue
  raw=p.read_bytes();assert secret not in raw,rel
  assert not re.search(rb'YX-[0-9A-F]{8}(?:-[0-9A-F]{8}){3}',raw),rel
  assert not re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]+[A-Za-z0-9+/\r\n]{64,}',raw),rel
  assert not re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})',raw),rel
  z.writestr(rel,raw);report['files']+=1;report['bytes']+=len(raw)
with zipfile.ZipFile(bundle) as z:assert z.testzip() is None
report.update(sha256=hashlib.file_digest(bundle.open('rb'),'sha256').hexdigest(),zipBytes=bundle.stat().st_size)
(HERE/'source-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
