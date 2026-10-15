$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$installed = [IO.Path]::GetFullPath((Join-Path $workspace 'work/安装验证 羽轩2.0.1'))
if (!$installed.StartsWith($workspace + '\work\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected test install directory' }
$installer = Join-Path $workspace 'work/studio/package-2.0.1/AppInventor-Offline-Setup-x64.exe'
$log = Join-Path $workspace 'work/installer-hint-fix-acceptance.log'
$arguments = '/CURRENTUSER /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR="' + $installed + '" /LOG="' + $log + '"'
$process = Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0) { throw ('Installer failed: ' + $process.ExitCode) }
'PASS installer exit 0'
foreach ($relative in @('AppInventor.exe', 'AppInventorCore.exe', 'studio/server.py', 'studio/studio.js', 'studio/studio.css', 'studio/index.html', 'studio/vs/loader.js', 'studio/brand-logo.png', 'runtime/python3.8.9/python.exe', 'runtime/python3.13.16/python.exe', 'runtime/python3.8.9/DLLs/_tkinter.pyd', 'runtime/python3.13.16/DLLs/_tkinter.pyd', 'runtime/python3.8.9/Lib/turtle.py', 'runtime/python3.13.16/Lib/turtle.py', 'runtime/llvm-mingw/bin/clang++.exe', 'resources/使用说明.txt')) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $installed $relative) -Algorithm SHA256).Hash
    $expected = (Get-FileHash -LiteralPath (Join-Path $workspace ('work/native/' + $relative)) -Algorithm SHA256).Hash
    if ($actual -ne $expected) { throw ('Installed file mismatch: ' + $relative) }
}
'PASS 16 installed file hashes match'
$data = Join-Path $workspace 'work/已安装版 提示验收'
$info = New-Object Diagnostics.ProcessStartInfo
$info.FileName = Join-Path $installed 'runtime/python3.13.16/python.exe'
$info.Arguments = '-X utf8 "' + (Join-Path $installed 'studio/server.py') + '" --data "' + $data + '" --token test-studio-token'
$info.UseShellExecute = $false
$info.CreateNoWindow = $true
$info.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
$info.Environment.Remove('PATH')
$info.Environment['Path'] = $env:PATH
$server = [Diagnostics.Process]::Start($info)
$timer = [Diagnostics.Stopwatch]::StartNew()
$running = Join-Path $data 'studio-running.json'
while (!(Test-Path -LiteralPath $running)) {
    if ($server.HasExited -or $timer.Elapsed.TotalSeconds -gt 20) { throw 'Installed studio failed to start' }
    Start-Sleep -Milliseconds 200
}
'PASS installed server ready for browser completion verification'
Get-Content -LiteralPath $running
exit 0
