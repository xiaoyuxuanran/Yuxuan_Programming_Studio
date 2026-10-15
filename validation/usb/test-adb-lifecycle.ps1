param([string]$Workspace = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent))
$ErrorActionPreference = 'Stop'
$usbFixtureDirectory = [IO.Path]::GetFullPath((Join-Path $Workspace 'work\usb'))
$usbFixtureSource = Join-Path $usbFixtureDirectory 'AdbJobLifecycle.cs'
$usbFixtureExecutable = Join-Path $usbFixtureDirectory 'AdbJobLifecycle.exe'
$usbCompiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $usbCompiler /nologo /target:exe /platform:x64 ('/out:' + $usbFixtureExecutable) $usbFixtureSource
if ($LASTEXITCODE -ne 0) { throw 'ADB 生命周期测试编译失败。' }
$usbFixtureAdb = [IO.Path]::GetFullPath((Join-Path $Workspace 'work\native\usb\platform-tools\adb.exe'))
& $usbFixtureExecutable $usbFixtureAdb (Join-Path $usbFixtureDirectory 'adb-lifecycle-acceptance.json')
if ($LASTEXITCODE -ne 0) { throw 'ADB 生命周期测试失败；专用随机端口已清理，现有 5037 服务不受影响。' }
