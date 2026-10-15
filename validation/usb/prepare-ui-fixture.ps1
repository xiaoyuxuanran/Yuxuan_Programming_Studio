param(
  [string]$Workspace = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
  [string]$DataDirectory = ''
)
$ErrorActionPreference = 'Stop'
$usbWorkspace = [IO.Path]::GetFullPath($Workspace)
$usbProduction = [IO.Path]::GetFullPath((Join-Path $usbWorkspace 'work\native'))
$usbClone = [IO.Path]::GetFullPath((Join-Path $usbWorkspace 'work\appinventor-ui\ui-fixture-root'))
if (!$DataDirectory) { $DataDirectory = Join-Path $usbWorkspace 'work\appinventor-ui\USB 接口验收' }
$usbUserdata = [IO.Path]::GetFullPath($DataDirectory)
foreach ($usbResolved in @($usbClone, $usbUserdata)) {
  if (!$usbResolved.StartsWith($usbWorkspace + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw '验收 fixture 及用户数据必须位于当前工作区内。'
  }
  if ($usbResolved.Equals($usbProduction, [StringComparison]::OrdinalIgnoreCase) -or $usbResolved.StartsWith($usbProduction + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw '验收 fixture 及数据不得写入 native 生产目录。'
  }
}
if (!(Test-Path -LiteralPath (Join-Path $usbUserdata 'license\device-license.bin') -PathType Leaf)) {
  throw '验收数据目录没有既有授权证书。此 fixture 不跳过或伪造真实激活检查。'
}
if ((Test-Path -LiteralPath $usbClone) -and ((Get-Item -LiteralPath $usbClone -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
  throw 'fixture 根目录必须是独立实体目录，不能使用链接。'
}
New-Item -ItemType Directory -Force -Path $usbClone | Out-Null
foreach ($usbExecutable in @('AppInventor.exe', 'AppInventorCore.exe')) {
  $usbSourceExecutable = Join-Path $usbProduction $usbExecutable
  $usbTargetExecutable = Join-Path $usbClone $usbExecutable
  if ((Test-Path -LiteralPath $usbTargetExecutable) -and ((Get-Item -LiteralPath $usbTargetExecutable -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'fixture EXE 必须是独立副本，不能通过链接覆盖生产文件。'
  }
  if ((Test-Path -LiteralPath $usbTargetExecutable) -and (Get-FileHash -LiteralPath $usbTargetExecutable).Hash -eq (Get-FileHash -LiteralPath $usbSourceExecutable).Hash) { continue }
  Copy-Item -LiteralPath $usbSourceExecutable -Destination $usbTargetExecutable -Force
}
foreach ($usbSharedDirectory in @('runtime','server','buildserver','resources')) {
  $usbJunctionPath = Join-Path $usbClone $usbSharedDirectory
  $usbJunctionTarget = Join-Path $usbProduction $usbSharedDirectory
  if (Test-Path -LiteralPath $usbJunctionPath) {
    $usbExisting = Get-Item -LiteralPath $usbJunctionPath -Force
    if ($usbExisting.LinkType -ne 'Junction' -or [IO.Path]::GetFullPath([string]$usbExisting.Target) -ne $usbJunctionTarget) {
      throw ('已有路径不是预期的只读复用 Junction：' + $usbJunctionPath)
    }
  } else {
    New-Item -ItemType Junction -Path $usbJunctionPath -Target $usbJunctionTarget | Out-Null
  }
}
$usbFixtureSettings = [ordered]@{
  schema = 1
  kind = 'development-usb-ui-fixture'
  productionRoot = $usbProduction
  dataDirectory = $usbUserdata
  simulatedDevice = 'FixtureUsbPhone'
  physicalPhoneUsed = $false
}
$usbFixtureSettings | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $usbClone 'ui-fixture.json') -Encoding utf8
foreach ($usbOwnedDirectory in @('usb','license')) {
  $usbOwnedPath = Join-Path $usbClone $usbOwnedDirectory
  if ((Test-Path -LiteralPath $usbOwnedPath) -and ((Get-Item -LiteralPath $usbOwnedPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw ('fixture 自有目录不能使用链接：' + $usbOwnedPath)
  }
  New-Item -ItemType Directory -Force -Path $usbOwnedPath | Out-Null
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'ui-fixture-server.py') -Destination (Join-Path $usbClone 'usb\server.py') -Force
# License uses an owned bootstrap; the real production gate/vendor are imported
# read-only with bytecode disabled, preventing pycache writes through junctions.
$usbLicenseBootstrap = @'
import sys
sys.dont_write_bytecode = True
import pathlib, runpy
script = pathlib.Path(__file__).resolve().parent.parent / 'usb' / 'server.py'
sys.argv.insert(1, '--fixture-license-gate')
runpy.run_path(str(script), run_name='__main__')
'@
$usbLicenseBootstrap | Set-Content -LiteralPath (Join-Path $usbClone 'license\gate.py') -Encoding utf8
Write-Output '独立 UI fixture 已准备；没有启动进程，没有修改 native 生产文件。'
Write-Output ('Clone: ' + $usbClone)
Write-Output ('Data:  ' + $usbUserdata)
Write-Output '仅此 clone 的 USB runner 使用模拟手机；授权、APK 构建、下载与清单解析仍使用真实生产实现。'
Write-Output ('请在正常 Core 停止后，启动 clone AppInventor.exe --headless --no-browser --data-dir "' + $usbUserdata + '"。')
