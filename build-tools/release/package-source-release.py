"""Audit or build the explicitly scoped, versioned source delivery ZIP.

Default invocation audits inputs without changing files.  Use --build only after
the release owner confirms the final native sources and delivery documents.
Existing staging-only Studio acceptance scripts are preserved explicitly; stale
staging files are never added implicitly.  No source directory is deleted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import zipfile


WORKSPACE = Path(__file__).resolve().parents[2]
BASELINE_STAGING = WORKSPACE / "work/studio/source-delivery"
VERSION = "2.2.0"
STAGING = WORKSPACE / "work/release-2.2/source-delivery"
ZIP_TARGET = WORKSPACE / "work/mixly/source-release-2.2.0.zip"
MANIFEST_TARGET = WORKSPACE / "work/mixly/source-release-manifest-2.2.0.json"
NATIVE = WORKSPACE / "work/native"
OUTPUTS = WORKSPACE / "outputs"

DOC_NAMES = (
    "使用说明.txt", "工程交接.md", "验收记录.md", "项目进度-2026-10-02.md",
)
JSON_NAMES = (
    "验收-代码提示.json", "验收-激活授权.json", "验收-启动器布局.json",
    "验收-长路径安装.json", "验收-Mixly.json", "验收-安装版工具.json",
    "验收-安装版Mixly.json", "验收-升级安装.json", "验收-卸载保留数据.json",
    "验收-命令行授权监测.json",
)
PRESERVE_STUDIO = (
    "studio/install-suite-test.ps1", "studio/uninstall-suite-test.ps1",
    "studio/prepare-graphics.ps1", "studio/THIRD-PARTY.txt",
)
RUNTIME_SOURCE = (
    "main.js", "package.json", "suite-main.js", "preload.js",
    "compiler-paths.py", "sdk-junction.ps1",
)
EXTRA_SOURCE = {
    "work/studio/install-hint-fix-test.ps1": "validation/studio/install-hint-fix-test.ps1",
    "work/mixly/prepare-cores.ps1": "build-tools/mixly/prepare-cores.ps1",
    "work/mixly/cache-tools.ps1": "build-tools/mixly/cache-tools.ps1",
    "work/mixly/install-acceptance.ps1": "validation/mixly/install-acceptance.ps1",
    "work/mixly/installed-smoke.py": "validation/mixly/installed-smoke.py",
    "work/mixly/install-final-acceptance.ps1": "validation/mixly/install-final-acceptance.ps1",
    "work/mixly/final-installed-smoke.py": "validation/mixly/final-installed-smoke.py",
    "work/mixly/uninstall-acceptance.ps1": "validation/mixly/uninstall-acceptance.ps1",
    "work/mixly/run-acceptance.ps1": "validation/mixly/run-acceptance.ps1",
    "work/mixly/integration-test.js": "validation/mixly/integration-test.js",
    "work/activation/LayoutCheck.cs": "validation/launcher/LayoutCheck.cs",
    "work/activation/check-final-headless.py": "validation/activation/check-final-headless.py",
    "work/activation/headless-monitor/test_headless_monitor.py": "validation/activation/headless-monitor/test_headless_monitor.py",
    "work/activation/headless-monitor/FakeBridge.cs": "validation/activation/headless-monitor/FakeBridge.cs",
    "work/activation/headless-monitor/FakeCore.cs": "validation/activation/headless-monitor/FakeCore.cs",
    "work/activation/headless-monitor/NetworkFixture.cs": "validation/activation/headless-monitor/NetworkFixture.cs",
    "work/studio/test-runtime-optimization.py": "validation/studio/test-runtime-optimization.py",
    "work/studio/run-runtime-acceptance.py": "validation/studio/run-runtime-acceptance.py",
    "work/usb/prepare-platform-tools.ps1": "build-tools/usb/prepare-platform-tools.ps1",
    "work/usb/test_usb.py": "validation/usb/test_usb.py",
    "work/usb/test_frontend.mjs": "validation/usb/test_frontend.mjs",
    "work/usb/AdbJobLifecycle.cs": "validation/usb/AdbJobLifecycle.cs",
    "work/usb/test-adb-lifecycle.ps1": "validation/usb/test-adb-lifecycle.ps1",
    "work/usb/prepare-ui-fixture.ps1": "validation/usb/prepare-ui-fixture.ps1",
    "work/usb/ui-fixture-server.py": "validation/usb/ui-fixture-server.py",
    "work/appinventor-ui/test-api.py": "validation/appinventor-ui/test-api.py",
    "work/mixly/package-source-release.py": "build-tools/release/package-source-release.py",
    "work/release-2.2/prepare-docs.py": "build-tools/release/prepare-docs.py",
    "work/release-2.2/install-acceptance.ps1": "validation/release-2.2/install-acceptance.ps1",
    "work/release-2.2/installed-smoke.py": "validation/release-2.2/installed-smoke.py",
    "work/build-speed/prepare-overlays.py": "build-tools/build-speed/prepare-overlays.py",
    "work/build-speed/prepare-dex-seed.py": "build-tools/build-speed/prepare-dex-seed.py",
    "work/build-speed/prepare-resource-seed.py": "build-tools/build-speed/prepare-resource-seed.py",
    "work/build-speed/benchmark.py": "validation/build-speed/benchmark.py",
    "work/build-speed/validate-seeds.py": "validation/build-speed/validate-seeds.py",
    "work/build-speed/SeedValidation.java": "validation/build-speed/SeedValidation.java",
}
APPINVENTOR_UI_SOURCE = (
    "build-ui.py", "compile-native.ps1", "stage-web.py", "offline-usb.css", "offline-usb.js",
    "OfflineUsbAction.java", "OfflineUsbServlet.java", "ShowBarcodeCommand.java", "ShowBarcodeCommand.java.patch",
    "ShowProgressBarCommand.java", "ShowProgressBarCommand.java.patch", "TopToolbar.java", "TopToolbar.java.patch",
    "WaitForBuildResultCommand.java", "WaitForBuildResultCommand.java.patch",
    "sync-source.py", "record-ui-results.py",
)
USB_SOURCE = ("server.py", "README.md", "platform-tools-lock.json")
BUILD_PATCH_SOURCE = ("RunD8.java", "ProjectBuilder.java", "Execution.java", "Resources.java",
                      "RunD8-offline.patch", "ProjectBuilder-offline.patch", "Execution-offline.patch", "Resources-offline.patch")
BUILD_SPEED_SOURCE = ("prepare-overlays.py", "prepare-dex-seed.py", "prepare-resource-seed.py", "benchmark.py",
                      "validate-seeds.py", "SeedValidation.java", "README.md",
                      "dex-seed-manifest.json", "resource-seed-manifest.json")
EXTRA_RESULTS = {
    "work/studio/optimization-results.json": "validation-results/studio-optimization.json",
    "work/usb/acceptance.json": "validation-results/usb-acceptance.json",
    "work/usb/frontend-acceptance.json": "validation-results/usb-frontend.json",
    "work/appinventor-ui/api-results.json": "validation-results/appinventor-usb-api.json",
    "work/usb/adb-lifecycle-acceptance.json": "validation-results/usb-adb-lifecycle.json",
    "work/build-speed/acceptance.json": "validation-results/appinventor-build-speed.json",
    "work/appinventor-ui/ui-results.json": "validation-results/appinventor-usb-ui.json",
    "work/release-2.2/install-acceptance.json": "validation-results/release-2.2/install-acceptance.json",
    "work/release-2.2/installed-payload.json": "validation-results/release-2.2/installed-payload.json",
    "work/release-2.2/installed-smoke.json": "validation-results/release-2.2/installed-smoke.json",
    "work/release-2.2/installed-reinstall-smoke.json": "validation-results/release-2.2/installed-reinstall-smoke.json",
}
ACTIVATION_CODE = re.compile(rb"YX(?:-[A-Fa-f0-9]{8}){4}")
PRIVATE_KEY = re.compile(rb"-----BEGIN (?:[A-Z0-9 ]* )?PRIVATE KEY-----")
SELFTEST_HOOK = b"YUXUAN_MIXLY_SELFTEST"
IGNORED_PARTS = {".git", "__pycache__"}
FORBIDDEN_PARTS = {"storage", ".aws", "userdata", "ui-test-data", "authkey", "keystore", "appengine-generated", "dex-seed", "resource-seed", "adb-user", "actual-device-enumeration", "platform-tools-download"}


def require_path(path: Path, allowed_parent: Path) -> Path:
    """Reject computed paths, links, or destinations outside their fixed roots."""
    resolved = path.resolve()
    root = allowed_parent.resolve()
    if not resolved.is_relative_to(root):
        raise RuntimeError("Path escaped its explicitly allowed workspace root")
    cursor = path
    while cursor != allowed_parent and cursor != cursor.parent:
        if cursor.exists() and (cursor.is_symlink() or getattr(cursor, "is_junction", lambda: False)()):
            raise RuntimeError("A source or destination uses a directory link")
        cursor = cursor.parent
    return resolved


def audit_member(name: str, data: bytes) -> None:
    member = PurePosixPath(name)
    parts = {part.casefold() for part in member.parts}
    basename = member.name.casefold()
    if member.is_absolute() or ".." in member.parts or "\\" in name:
        raise RuntimeError(f"Unsafe archive member: {name}")
    if parts & FORBIDDEN_PARTS or parts & IGNORED_PARTS:
        raise RuntimeError(f"Forbidden data directory in archive member: {name}")
    if basename.endswith((".reg", ".log")) or basename in {
        "device-license.bin", "device-license.json", "registration-snapshot.json",
        "original-uninstall-registration.reg",
        "studio.json", "studio-running.json", "usb-running.json", "local_db.bin",
    } or (basename.endswith(".bin") and any(word in basename for word in ("license", "授权", "激活"))):
        raise RuntimeError(f"Forbidden personal state or log in archive member: {name}")
    if ACTIVATION_CODE.search(data):
        raise RuntimeError(f"Activation code detected in archive member: {name}")
    if PRIVATE_KEY.search(data):
        raise RuntimeError(f"Private key detected in archive member: {name}")
    # The developer-only runner documents its scoped try/finally injection.  Its
    # source is intentionally delivered in validation, never in the runtime.
    final_hook_assertion = (
        name in {"validation/mixly/final-installed-smoke.py", "validation/release-2.2/installed-smoke.py"}
        and data.count(SELFTEST_HOOK) == 1
        and b"assert 'YUXUAN_MIXLY_SELFTEST' not in main" in data
    )
    if SELFTEST_HOOK in data and not final_hook_assertion and name not in {
        "validation/mixly/run-acceptance.ps1",  # Scoped injection with restoration.
        "validation/mixly/install-acceptance.ps1",  # Assert the shipped main has no hook.
        "build-tools/release/package-source-release.py",  # Audit rule and named development-only sources.
    }:
        raise RuntimeError(f"Temporary Mixly test hook detected in archive member: {name}")


def enumerate_inputs(documents: Path) -> tuple[dict[str, Path | bytes], list[str], list[str]]:
    files: dict[str, Path | bytes] = {}
    missing: list[str] = []
    excluded_firmware: list[str] = []

    def add(source: Path, member: str) -> None:
        require_path(source, WORKSPACE)
        if not source.is_file():
            raise RuntimeError(f"Missing required source: {member}")
        if member in files:
            # Explicit runtime-source selections may also have been synchronized
            # by the release owner. Reject an outdated copy rather than silently
            # prefer one version.
            if content(files[member]) != source.read_bytes():
                raise RuntimeError(f"Conflicting synchronized archive member: {member}")
            return
        files[member] = source

    def tree(source: Path, prefix: str) -> None:
        require_path(source, WORKSPACE)
        if not source.is_dir():
            raise RuntimeError(f"Missing required source directory: {prefix}")
        for path in sorted(source.rglob("*")):
            relative = path.relative_to(source)
            if set(relative.parts) & IGNORED_PARTS:
                continue
            if path.is_file():
                if (prefix == "Mixly4Yuxuan-source" and relative.parts[:2] == ("boards", "default")
                        and "build" in relative.parts and path.suffix.casefold() == ".bin"):
                    # Precompiled upstream firmware is distributed by the normal
                    # installer. Keep the source archive free of TLS test keys
                    # embedded in those public MicroPython firmware images.
                    excluded_firmware.append(relative.as_posix())
                    continue
                add(path, (PurePosixPath(prefix) / relative.as_posix()).as_posix())

    tree(NATIVE / "resources/distribution-source", "distribution-source")
    for relative in PRESERVE_STUDIO:
        member = "distribution-source/" + relative
        if member not in files:
            add(BASELINE_STAGING / member, member)
    tree(NATIVE / "resources/licenses", "licenses")
    tree(NATIVE / "mixly/src", "Mixly4Yuxuan-source")
    for name in RUNTIME_SOURCE:
        add(NATIVE / "mixly/runtime/resources/app" / name, "Mixly4Yuxuan-runtime-source/" + name)
    for relative, member in EXTRA_SOURCE.items():
        add(WORKSPACE / relative, member)
    # validate-seeds.py imports this sibling; deliver a matching validation copy.
    add(WORKSPACE / "work/build-speed/prepare-dex-seed.py", "validation/build-speed/prepare-dex-seed.py")
    for name in APPINVENTOR_UI_SOURCE:
        add(WORKSPACE / "work/appinventor-ui" / name, "distribution-source/appinventor-ui/" + name)
    for name in USB_SOURCE:
        add(NATIVE / "usb" / name, "distribution-source/usb/" + name)
    for name in ("NOTICE.txt", "source.properties"):
        add(NATIVE / "usb/platform-tools" / name, "licenses/Android-Platform-Tools/" + name)
    for name in BUILD_PATCH_SOURCE:
        add(WORKSPACE / "work/native-patches" / name, "distribution-source/build-speed/" + name)
    # Keep the portable patch-native-build.py relative entry point runnable.
    for name in BUILD_SPEED_SOURCE:
        add(WORKSPACE / "work/build-speed" / name, "distribution-source/build-speed/" + name)
    for name in DOC_NAMES:
        add(documents / name, name)
    if VERSION not in (documents / DOC_NAMES[0]).read_text(encoding="utf-8-sig")[:200]:
        raise RuntimeError("User documentation does not match the requested suite version")
    extra_note = BASELINE_STAGING / "代码提示修复说明.md"
    if extra_note.is_file():
        add(extra_note, extra_note.name)
    for name in JSON_NAMES:
        source = OUTPUTS / name
        # The original Monaco acceptance is an explicitly retained baseline file.
        if name == "验收-代码提示.json" and not source.is_file():
            source = BASELINE_STAGING / name
        if source.is_file():
            json.loads(source.read_text(encoding="utf-8-sig"))
            add(source, name)
        else:
            missing.append(name)
    for relative, member in EXTRA_RESULTS.items():
        source = WORKSPACE / relative
        if source.is_file():
            json.loads(source.read_text(encoding="utf-8-sig"))
            add(source, member)
        else:
            missing.append(member)
    required = {
        "distribution-source/SuiteLauncher.cs", "distribution-source/SuiteLicense.cs",
        "distribution-source/Setup.iss", "distribution-source/BuildRelease.ps1",
        "distribution-source/license/license_client.py", "distribution-source/license/gate.py",
        "distribution-source/license/server/jihuo/api.php",
        "distribution-source/license/server/jihuo/core.php",
        "distribution-source/license/server/jihuo/offline-products.php",
        "distribution-source/mixly-adaptation/prepare-mixly.py",
        "Mixly4Yuxuan-source/boards.json", "Mixly4Yuxuan-runtime-source/main.js",
        "distribution-source/studio/runtime_support.py",
        "distribution-source/appinventor-ui/OfflineUsbServlet.java",
        "distribution-source/appinventor-ui/ShowBarcodeCommand.java.patch",
        "distribution-source/usb/server.py", "licenses/Android-Platform-Tools/NOTICE.txt",
        "build-tools/build-speed/prepare-dex-seed.py", "build-tools/build-speed/prepare-resource-seed.py",
    }
    if required - files.keys():
        raise RuntimeError("Required delivery source members are missing: " + ", ".join(sorted(required - files.keys())))
    lock = {
        "suiteVersion": VERSION,
        "mixly": {
            "source": "https://gitee.com/mixly2/mixly2.0_src",
            "tag": "2.0-rc4", "commit": "a7d91f1e3c621a3132fb8ea38c92877bb0834830",
        },
        "desktop": {
            "source": "https://gitee.com/mixly2/mixly2.0-win32-x64",
            "commit": "d1bb6950c91f3b8f68d571188393b3d6b6603eb7", "electron": "19.0.6",
        },
        "arduinoLibraries": {
            "source": "https://gitee.com/mixly2/arduino-libs",
            "commit": "2b7ca7d23afec725d23f80b3d995d4cf5fa57a01",
        },
        "arduinoCli": "0.35.3",
        "cores": {"arduino:avr": "1.8.6", "esp8266:esp8266": "3.1.2", "esp32:esp32": "2.0.17"},
        "python": ["3.8.9", "3.13.16"], "pygame": "2.6.1", "clang": "23.1.2",
        "llvmMinGW": "20260922", "monaco": "0.57.0", "pip": {"python3.8": "24.3.1", "python3.13": "26.2.1"},
        "innoSetup": "7.1.0", "setupArchitecture": "x64",
        "licenseBridge": {"cryptography": "50.0.2", "cffi": "2.1.1", "pycparser": "3.0"},
        "esp32TransferTools": {"esptool": "4.6.2", "adafruit-ampy": "1.1.0"},
        "appInventor": {"source": "https://github.com/mit-cml/appinventor-sources", "commit": "c76a58ce7d8b9723107ea980046ca95e1ddf936e"},
        "androidPlatformTools": json.loads((NATIVE / "usb/platform-tools-lock.json").read_text(encoding="utf-8-sig")),
    }
    files["UPSTREAM-LOCK.json"] = (json.dumps(lock, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    files["源码归档说明.md"] = ("# 羽轩编程工作台 " + VERSION + " 源码与补丁\n" + """

distribution-source 保存启动器、授权桥接、服务端补丁、App Inventor 改动和桌面 Python/C++ 工作区源码。Mixly4Yuxuan-source 保存四个硬件环境和共用模块的实际适配源码，Mixly4Yuxuan-runtime-source 保存最终 Electron 入口及辅助源码，distribution-source/mixly-adaptation 保存生成脚本。UPSTREAM-LOCK.json 记录本次上游提交和工具版本。

build-tools 和 validation 仅交付构建与验收源码，不属于安装程序运行入口。源码中的目录引用保持原工程布局；执行前需要恢复 work/native、work/mixly、work/studio 等目录，并具备相应上游工具下载文件。安装验收需要使用用户自己在同一电脑、同一 Windows 用户下已经激活的授权状态。归档不含设备凭证、注册表备份、服务端 storage、私钥、日志或真实激活码。

validation/activation/headless-monitor 的四个文件应放回原始 work/activation/headless-monitor 路径后运行。FakeBridge、FakeCore、NetworkFixture 是纯源码开发夹具，使用合成授权结果和网络状态；归档不含任何 run-* 测试数据目录。

Mixly 开发验收 runner 仅在受控测试期间临时加入钩子，并在 try/finally 中恢复原入口字节；安装运行时 main.js 无此钩子。普通用户不需要执行验收脚本。

源码归档排除 boards/default/*/build/*.bin 中的上游预编译固件和二进制字库；正式安装包照常包含它们，也可从 UPSTREAM-LOCK.json 固定的 Mixly 上游发行源码取得。本归档保留全部适配 JavaScript、Python、C/C++ 源文件。

SOURCE-MANIFEST.json 逐文件记录长度和 SHA256，可用于检查归档与源码一致性。第三方许可证位于 licenses，Mixly 原 LICENSE 和署名保留在源码中。

2.2.0 的 App Inventor GWT 完整改动和逐文件补丁位于 distribution-source/appinventor-ui；USB helper、协议说明和官方工具锁文件位于 distribution-source/usb。ADB 二进制由安装包部署；本源码归档交付完整官方 NOTICE 及获取校验脚本。

APK 构建优化 Java 源码/补丁位于 distribution-source/build-speed，离线 DEX 和资源种子生成脚本位于 build-tools/build-speed；已生成的 DEX、资源缓存、编译临时目录和签名密钥均不进入源码归档。Python 快速隔离环境与安全 HTTPS 辅助模块位于 distribution-source/studio/runtime_support.py。

validation-results 保存不含凭证的验收结果，其中 release-2.2 保存本版实际安装、负载文件校验、运行及重装保留依赖的结果。根目录验收-*.json 为明确保留的历史检查，2.1.0 安装/升级/卸载结果不能替代本版检查。USB 模拟测试不代表真实手机已安装；验收时未连接真实 Android USB 手机。新安装包的验证以对应 2.2.0 发布记录为准。
""").encode("utf-8")
    return files, missing, excluded_firmware


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def content(source: Path | bytes) -> bytes:
    return source.read_bytes() if isinstance(source, Path) else source


def main() -> None:
    global VERSION, STAGING, ZIP_TARGET, MANIFEST_TARGET
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="Copy named sources and generate the audited temporary ZIP")
    parser.add_argument("--version", default="2.2.0", help="Suite version recorded in the temporary archive (default: 2.2.0)")
    parser.add_argument("--documents", type=Path, default=OUTPUTS, help="Matching release documents; candidate documents can stay outside outputs")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version):
        raise ValueError("Version must contain three numeric components")
    VERSION = args.version
    STAGING = WORKSPACE / ("work/release-" + VERSION) / "source-delivery"
    ZIP_TARGET = WORKSPACE / "work/mixly" / ("source-release-" + VERSION + ".zip")
    MANIFEST_TARGET = WORKSPACE / "work/mixly" / ("source-release-manifest-" + VERSION + ".json")
    documents = require_path(args.documents.resolve(), WORKSPACE)
    require_path(STAGING, WORKSPACE / "work")
    require_path(ZIP_TARGET, WORKSPACE / "work/mixly")
    require_path(MANIFEST_TARGET, WORKSPACE / "work/mixly")
    files, missing, excluded_firmware = enumerate_inputs(documents)
    hashes = {}
    total_bytes = 0
    for member, source in sorted(files.items()):
        data = content(source)
        audit_member(member, data)
        hashes[member] = {"size": len(data), "sha256": sha256(data)}
        total_bytes += len(data)
    report = {
        "suiteVersion": VERSION, "audited": True, "built": False, "files": len(files),
        "sourceBytes": total_bytes, "missingAcceptanceJson": missing,
        "excludedPrecompiledFirmware": excluded_firmware,
        "zip": str(ZIP_TARGET), "staging": str(STAGING),
    }
    if args.build:
        if missing:
            raise RuntimeError("Final acceptance JSON files are not all ready; use audit mode until complete")
        setup = content(files["distribution-source/Setup.iss"]).decode("utf-8-sig")
        if not re.search(r"(?m)^AppVersion=" + re.escape(VERSION) + r"\s*$", setup):
            raise RuntimeError("Synchronized installer source does not match the requested suite version")
        for member, source in sorted(files.items()):
            target = STAGING / Path(member)
            require_path(target, STAGING)
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(source, bytes):
                target.write_bytes(source)
            elif source.resolve() != target.resolve():
                shutil.copy2(source, target)
            # Verify the synchronized file against the input audit, detecting races.
            data = target.read_bytes()
            audit_member(member, data)
            if sha256(data) != hashes[member]["sha256"]:
                raise RuntimeError(f"Source changed during packaging: {member}")
        manifest = json.dumps({"suiteVersion": VERSION, "files": hashes,
                               "excludedPrecompiledFirmware": excluded_firmware}, ensure_ascii=False, indent=2).encode("utf-8")
        manifest_path = STAGING / "SOURCE-MANIFEST.json"
        require_path(manifest_path, STAGING)
        manifest_path.write_bytes(manifest + b"\n")
        zip_tmp = ZIP_TARGET.with_suffix(".zip.pending")
        require_path(zip_tmp, WORKSPACE / "work/mixly")
        with zipfile.ZipFile(zip_tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
            for member in sorted(files):
                archive.write(STAGING / Path(member), member)
            archive.write(manifest_path, manifest_path.name)
        with zipfile.ZipFile(zip_tmp) as archive:
            if archive.testzip() is not None:
                raise RuntimeError("ZIP CRC validation failed")
            if len(archive.infolist()) != len(files) + 1:
                raise RuntimeError("ZIP member count mismatch")
            for item in archive.infolist():
                data = archive.read(item)
                audit_member(item.filename, data)
                if item.filename in hashes and sha256(data) != hashes[item.filename]["sha256"]:
                    raise RuntimeError(f"ZIP source hash mismatch: {item.filename}")
                if not item.filename.isascii() and not item.flag_bits & 0x800:
                    raise RuntimeError("A non-ASCII ZIP filename is missing the UTF-8 flag")
        os.replace(zip_tmp, ZIP_TARGET)
        report.update({
            "built": True, "zipFiles": len(files) + 1,
            "zipBytes": ZIP_TARGET.stat().st_size, "zipSha256": sha256(ZIP_TARGET.read_bytes()),
            "allMembersAudited": True,
        })
        MANIFEST_TARGET.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
