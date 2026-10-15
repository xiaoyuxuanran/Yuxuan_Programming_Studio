$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$installed=[IO.Path]::GetFullPath((Join-Path $workspace 'work/安装验证 羽轩2.1.0'))
$data=[IO.Path]::GetFullPath((Join-Path $workspace 'work/已安装版 羽轩2.1.0'))
if(-not $installed.StartsWith($workspace+'\work\') -or -not $data.StartsWith($workspace+'\work\')){throw 'Unexpected acceptance paths'}
$installer=Join-Path $workspace 'work/studio/package-2.1.0-final/AppInventor-Offline-Setup-x64.exe'
$native=Join-Path $workspace 'work/native'
$log=Join-Path $workspace 'work/installer-2.1-final-acceptance.log'
$registrationSnapshot=Join-Path $PSScriptRoot 'registration-snapshot.json'
$registrationBackup=Join-Path $PSScriptRoot 'original-uninstall-registration.reg'
$previousDataSnapshot=Join-Path $PSScriptRoot 'uninstall-data-before.json'
$snapshotPath=Join-Path $PSScriptRoot 'final-install-data-before.json'
$resultPath=Join-Path $PSScriptRoot 'final-install-result.json'
$helper=Join-Path $PSScriptRoot 'final-installed-smoke.py'
$payloadPath=Join-Path $PSScriptRoot 'final-install-payload.json'
$smokePath=Join-Path $PSScriptRoot 'final-install-smoke.json'
$report=[ordered]@{ok=$false;installed=$installed;data=$data;installer=$installer;installerSHA256=$null;installExitCode=$null;preservedFiles=0;registrationSnapshotPreserved=$false;checks=@();payload=$null;smoke=$null;failure=$null}

function Assert-PreservedData {
 param($Hashes)
 foreach($file in $Hashes.Keys){
  if(-not (Test-Path -LiteralPath $file -PathType Leaf) -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $Hashes[$file]){throw ('Existing acceptance data changed: '+$file)}
 }
}

try {
 if(-not (Test-Path -LiteralPath $installer -PathType Leaf)){throw 'Final package is not available; finish compression before running this script'}
 if(Test-Path -LiteralPath (Join-Path $installed 'AppInventor.exe')){throw 'The isolated acceptance application must be uninstalled before this final install'}
 if(-not (Test-Path -LiteralPath (Join-Path $data 'license/device-license.bin') -PathType Leaf)){throw 'Existing isolated signed device grant is missing; this script does not activate licenses'}
 if(-not (Test-Path -LiteralPath $registrationSnapshot -PathType Leaf)){throw 'Previous registration snapshot is missing; do not overwrite it with a new snapshot'}
 if(-not (Test-Path -LiteralPath $previousDataSnapshot -PathType Leaf)){throw 'Previous preserved-data manifest is missing'}
 $registrationHash=(Get-FileHash -LiteralPath $registrationSnapshot -Algorithm SHA256).Hash
 $backupExisted=Test-Path -LiteralPath $registrationBackup -PathType Leaf
 $backupHash=if($backupExisted){(Get-FileHash -LiteralPath $registrationBackup -Algorithm SHA256).Hash}else{$null}
 $registration=Get-Content -LiteralPath $registrationSnapshot -Encoding UTF8 -Raw | ConvertFrom-Json
 $key='Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D394BCE3-729B-427F-A3EB-52885E97ED62}_is1'
 if(-not $registration.existingRegistration -and (Test-Path -LiteralPath $key)){throw 'A new application registration exists since the prior snapshot; preserve it separately before acceptance'}
 if($registration.existingRegistration -and -not $backupExisted){throw 'Original registration backup is required for the subsequent acceptance uninstall'}

 # Re-hash current preserved files rather than relying on the previous run's values.
 $previous=Get-Content -LiteralPath $previousDataSnapshot -Encoding UTF8 -Raw | ConvertFrom-Json
 $before=@{}
 foreach($property in $previous.PSObject.Properties){
  $file=[IO.Path]::GetFullPath($property.Name)
  if(-not $file.StartsWith($data+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Preserved-data manifest points outside the isolated data directory'}
  if(-not (Test-Path -LiteralPath $file -PathType Leaf)){throw ('Previously preserved file is missing: '+$file)}
  $before[$file]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
 }
 if($before.Count -eq 0){throw 'Preserved-data manifest is empty'}
 $before | ConvertTo-Json | Set-Content -LiteralPath $snapshotPath -Encoding UTF8
 $report.preservedFiles=$before.Count
 $report.installerSHA256=(Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash
 $arguments='/CURRENTUSER /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /NOICONS /TASKS="" /GROUP="Yuxuan Studio Acceptance" /DIR="'+$installed+'" /LOG="'+$log+'"'
 $process=Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
 $report.installExitCode=$process.ExitCode
 if($process.ExitCode -ne 0){throw ('Final installer failed: '+$process.ExitCode)}
 $report.checks+=@{test='final installer exit';ok=$true;exitCode=$process.ExitCode}
 Assert-PreservedData $before
 $report.checks+=@{test='installation preserves existing data';ok=$true;files=$before.Count}
 'PASS final installer exit 0 and '+$before.Count+' preserved files'

 $python=Join-Path $installed 'runtime/python3.13.16/python.exe'
 & $python -X utf8 $helper payload --installed $installed --native $native --report $payloadPath
 if($LASTEXITCODE -ne 0){throw 'Final installed payload checks failed'}
 $report.payload=Get-Content -LiteralPath $payloadPath -Encoding UTF8 -Raw | ConvertFrom-Json
 & $python -X utf8 $helper smoke --installed $installed --data $data --report $smokePath
 if($LASTEXITCODE -ne 0){throw 'Final installed launcher smoke checks failed'}
 $report.smoke=Get-Content -LiteralPath $smokePath -Encoding UTF8 -Raw | ConvertFrom-Json

 # Runtime smoke uses a copied device grant in a fresh test directory, so these remain unchanged.
 Assert-PreservedData $before
 $report.checks+=@{test='isolated smoke preserves existing data';ok=$true;files=$before.Count}
 if((Get-FileHash -LiteralPath $registrationSnapshot -Algorithm SHA256).Hash -ne $registrationHash){throw 'Original registration snapshot was altered'}
 if($backupExisted){
  if(-not (Test-Path -LiteralPath $registrationBackup -PathType Leaf) -or (Get-FileHash -LiteralPath $registrationBackup -Algorithm SHA256).Hash -ne $backupHash){throw 'Original registration backup was altered'}
 }elseif(Test-Path -LiteralPath $registrationBackup){throw 'Unexpected original registration backup was created'}
 $report.registrationSnapshotPreserved=$true
 $report.checks+=@{test='prior registration snapshot retained';ok=$true}
 $report.ok=$true
 'PASS final installed launcher, 24 critical payload hashes, two SDK long paths and test exclusion'
}catch {
 $report.failure=$_.Exception.Message
 throw
}finally {
 $report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resultPath -Encoding UTF8
}
