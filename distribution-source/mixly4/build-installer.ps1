$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskRelease=Join-Path $taskRoot 'work/release-2.3'
$taskResult=Join-Path $taskRelease 'installer-build-result.json'
$taskStatus=[ordered]@{ok=$false;state='running';startedUTC=[DateTime]::UtcNow.ToString('o');finishedUTC=$null;bytes=$null;sha256=$null;failure=$null}
$taskStatus | ConvertTo-Json | Set-Content -LiteralPath $taskResult -Encoding utf8
try {
 & (Join-Path $taskRoot 'work/mixly/BuildRelease.ps1') -Workspace $taskRoot -OutputDirectory (Join-Path $taskRelease 'package') *> (Join-Path $taskRelease 'installer-build.log')
 if($LASTEXITCODE -ne 0){throw ('Installer compile exit '+$LASTEXITCODE)}
 $taskFile=Get-Item -LiteralPath (Join-Path $taskRelease 'package/AppInventor-Offline-Setup-x64.exe')
 $taskStatus.bytes=$taskFile.Length
 $taskStatus.sha256=(Get-FileHash -LiteralPath $taskFile.FullName).Hash
 $taskStatus.ok=$true;$taskStatus.state='complete'
}catch{$taskStatus.failure=$_.Exception.Message;$taskStatus.state='failed'}finally{
 $taskStatus.finishedUTC=[DateTime]::UtcNow.ToString('o')
 $taskStatus | ConvertTo-Json | Set-Content -LiteralPath $taskResult -Encoding utf8
}
if(-not $taskStatus.ok){throw $taskStatus.failure}
