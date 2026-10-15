$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$installed=[IO.Path]::GetFullPath((Join-Path $workspace 'work/安装验证 羽轩2.1.0'))
$data=[IO.Path]::GetFullPath((Join-Path $workspace 'work/已安装版 羽轩2.1.0'))
if(-not $installed.StartsWith($workspace+'\work\') -or -not $data.StartsWith($workspace+'\work\')){throw 'Unexpected acceptance paths'}
$installer=Join-Path $workspace 'work/studio/package-2.1.0/AppInventor-Offline-Setup-x64.exe'
$log=Join-Path $workspace 'work/installer-2.1-acceptance.log'
$key='HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D394BCE3-729B-427F-A3EB-52885E97ED62}_is1'
$backup=Join-Path $PSScriptRoot 'original-uninstall-registration.reg'
$registrationSnapshot=Join-Path $PSScriptRoot 'registration-snapshot.json'
if(-not (Test-Path -LiteralPath $registrationSnapshot)){
 $existed=Test-Path 'Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D394BCE3-729B-427F-A3EB-52885E97ED62}_is1'
 if($existed){
  & reg.exe export $key $backup /y | Out-Null
  if($LASTEXITCODE -ne 0){throw 'Cannot preserve existing application registration'}
  'Existing application registration saved for restoration after acceptance uninstall'
 }
 [pscustomobject]@{existingRegistration=$existed;key=$key} | ConvertTo-Json | Set-Content -LiteralPath $registrationSnapshot -Encoding utf8
}
$arguments='/CURRENTUSER /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /NOICONS /TASKS="" /GROUP="Yuxuan Studio Acceptance" /DIR="'+$installed+'"'
if(-not (Test-Path -LiteralPath (Join-Path $installed 'AppInventor.exe'))){
 $old=Join-Path $workspace 'work/studio/package-2.0.1/AppInventor-Offline-Setup-x64.exe'
 $oldProcess=Start-Process -FilePath $old -ArgumentList ($arguments+' /LOG="'+(Join-Path $workspace 'work/installer-2.1-upgrade-base.log')+'"') -WindowStyle Hidden -Wait -PassThru
 if($oldProcess.ExitCode -ne 0){throw ('2.0.1 upgrade baseline install failed: '+$oldProcess.ExitCode)}
 'PASS original 2.0.1 installed in isolated path'
}
New-Item -ItemType Directory -Path (Join-Path $data 'license'),(Join-Path $data 'upgrade-project'),(Join-Path $data 'mixly') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $workspace 'work/activation/ui-test-data/license/device-license.bin') -Destination (Join-Path $data 'license/device-license.bin') -Force
[IO.File]::WriteAllText((Join-Path $data 'upgrade-project/main.py'),'print("Keep the existing project")')
[IO.File]::WriteAllText((Join-Path $data 'mixly/custom-library-marker.txt'),'Keep existing user hardware libraries')
$upgradeFiles=@('license/device-license.bin','upgrade-project/main.py','mixly/custom-library-marker.txt')
$upgradeHashes=@{}
foreach($file in $upgradeFiles){$upgradeHashes[$file]=(Get-FileHash -LiteralPath (Join-Path $data $file)).Hash}
$process=Start-Process -FilePath $installer -ArgumentList ($arguments+' /LOG="'+$log+'"') -WindowStyle Hidden -Wait -PassThru
if($process.ExitCode -ne 0){throw ('Installer failed: '+$process.ExitCode)}
'PASS installer exit 0'
foreach($file in $upgradeFiles){if((Get-FileHash -LiteralPath (Join-Path $data $file)).Hash -ne $upgradeHashes[$file]){throw ('Upgrade altered existing data: '+$file)}}
'PASS 2.0.1 to 2.1.0 upgrade preserved existing license, project and library marker'
$files=@('AppInventor.exe','AppInventorCore.exe','license/gate.py','license/license_client.py','license/vendor/_cffi_backend.cp313-win_amd64.pyd','studio/server.py','studio/studio.js','studio/studio.css','studio/index.html','studio/vs/loader.js','runtime/python3.8.9/python.exe','runtime/python3.13.16/python.exe','runtime/python3.8.9/DLLs/_tkinter.pyd','runtime/python3.13.16/DLLs/_tkinter.pyd','runtime/llvm-mingw/bin/clang++.exe','resources/使用说明.txt','mixly/runtime/Mixly.exe','mixly/runtime/resources/app/main.js','mixly/runtime/resources/app/suite-main.js','mixly/runtime/resources/app/compiler-paths.py','mixly/src/boards.json','mixly/src/yuxuan-recovery.js','mixly/src/yuxuan-home.js','mixly/arduino-cli/arduino-cli.exe')
foreach($relative in $files){
 $actual=(Get-FileHash -LiteralPath (Join-Path $installed $relative)).Hash
 $expected=(Get-FileHash -LiteralPath (Join-Path $workspace ('work/native/'+$relative))).Hash
 if($actual -ne $expected){throw ('Installed file mismatch: '+$relative)}
}
if(Test-Path (Join-Path $installed 'AppInventor-2.1-test.exe')){throw 'Test launcher incorrectly shipped'}
if(Select-String -LiteralPath (Join-Path $installed 'mixly/runtime/resources/app/main.js') -Pattern YUXUAN_MIXLY_SELFTEST -Quiet){throw 'Test entry incorrectly shipped'}
'PASS 24 installed file hashes and test exclusion'
& (Join-Path $installed 'runtime/python3.13.16/python.exe') -X utf8 (Join-Path $PSScriptRoot 'installed-smoke.py') $installed $data
if($LASTEXITCODE -ne 0){throw 'Installed smoke checks failed'}
$mixlyData=Join-Path $data 'mixly';New-Item -ItemType Directory -Path $mixlyData -Force | Out-Null
$mixlyOutput=Join-Path $workspace 'work/mixly/installed-acceptance';New-Item -ItemType Directory -Path $mixlyOutput -Force | Out-Null
& (Join-Path $PSScriptRoot 'run-acceptance.ps1') -NativeRoot $installed -DataRoot $mixlyData -OutputRoot $mixlyOutput
if($LASTEXITCODE -ne 0){throw 'Installed Mixly checks failed'}
'PASS installed suite and Mixly acceptance'
