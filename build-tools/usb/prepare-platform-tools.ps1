param([string]$Workspace = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent))
$ErrorActionPreference = 'Stop'
$usbWorkRoot = [IO.Path]::GetFullPath((Join-Path $Workspace 'work\usb'))
$usbNativeRoot = [IO.Path]::GetFullPath((Join-Path $Workspace 'work\native\usb'))
$usbLock = Get-Content -LiteralPath (Join-Path $usbNativeRoot 'platform-tools-lock.json') -Raw | ConvertFrom-Json
$usbArchive = Join-Path $usbWorkRoot 'platform-tools-latest-windows.zip'
New-Item -ItemType Directory -Force -Path $usbWorkRoot, $usbNativeRoot | Out-Null
if (!(Test-Path -LiteralPath $usbArchive)) {
  Invoke-WebRequest -Uri $usbLock.source -OutFile $usbArchive
}
if ((Get-FileHash -LiteralPath $usbArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $usbLock.archiveSha256) {
  throw 'Google 已更新 latest 下载内容，或缓存 ZIP 不完整。请先人工审核新版文件与许可证，再更新 platform-tools-lock.json；不会将未验证文件写入安装包。'
}
$usbExtractRoot = [IO.Path]::GetFullPath((Join-Path $usbWorkRoot 'platform-tools-download'))
if (!$usbExtractRoot.StartsWith($usbWorkRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
  throw '解压目录不在当前工作区内。'
}
Expand-Archive -LiteralPath $usbArchive -DestinationPath $usbExtractRoot -Force
$usbTarget = Join-Path $usbNativeRoot 'platform-tools'
New-Item -ItemType Directory -Force -Path $usbTarget | Out-Null
foreach ($usbEntry in $usbLock.files) {
  $usbSourceFile = Join-Path (Join-Path $usbExtractRoot 'platform-tools') $usbEntry.file
  if ((Get-FileHash -LiteralPath $usbSourceFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $usbEntry.sha256) {
    throw ('ADB 文件校验失败: ' + $usbEntry.file)
  }
  $usbDestinationFile = Join-Path $usbTarget $usbEntry.file
  if ((Test-Path -LiteralPath $usbDestinationFile) -and (Get-FileHash -LiteralPath $usbDestinationFile -Algorithm SHA256).Hash.ToLowerInvariant() -eq $usbEntry.sha256) {
    continue
  }
  Copy-Item -LiteralPath $usbSourceFile -Destination $usbDestinationFile -Force
}
Write-Output ('已准备 Google 官方 ADB ' + $usbLock.adbBuild + '，保留完整 NOTICE。')
