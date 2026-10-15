$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$installed=[IO.Path]::GetFullPath((Join-Path $workspace 'work/安装验证 羽轩2.1.0'))
$data=[IO.Path]::GetFullPath((Join-Path $workspace 'work/已安装版 羽轩2.1.0'))
if(-not $installed.StartsWith($workspace+'\work\') -or -not $data.StartsWith($workspace+'\work\')){throw 'Unexpected acceptance paths'}
$files=@(Get-ChildItem -LiteralPath (Join-Path $data 'license'),(Join-Path $data 'studio/projects'),(Join-Path $data 'mixly/projects'),(Join-Path $data 'mixly/drafts') -File -Recurse)
$files+=Get-Item -LiteralPath (Join-Path $data 'studio/studio.json')
$library=Join-Path $data 'mixly/src/boards/default/arduino_avr/libraries/ThirdParty/Emakefun_Sensor'
$files+=Get-ChildItem -LiteralPath $library -File -Recurse
$before=@{}
foreach($file in $files){$before[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName).Hash}
$before | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'uninstall-data-before.json') -Encoding utf8
$uninstaller=Join-Path $installed 'unins000.exe'
if(-not (Test-Path -LiteralPath $uninstaller)){throw 'Expected acceptance uninstaller missing'}
$process=Start-Process -FilePath $uninstaller -ArgumentList ('/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG="'+(Join-Path $workspace 'work/uninstaller-2.1-acceptance.log')+'"') -WindowStyle Hidden -Wait -PassThru
if($process.ExitCode -ne 0){throw ('Uninstaller failed: '+$process.ExitCode)}
foreach($file in $before.Keys){if(-not (Test-Path -LiteralPath $file) -or (Get-FileHash -LiteralPath $file).Hash -ne $before[$file]){throw ('User data changed during uninstall: '+$file)}}
if(Test-Path -LiteralPath (Join-Path $installed 'AppInventor.exe')){throw 'Acceptance application still installed'}
$backup=Join-Path $PSScriptRoot 'original-uninstall-registration.reg'
if(Test-Path -LiteralPath $backup){& reg.exe import $backup | Out-Null;if($LASTEXITCODE -ne 0){throw 'Existing application registration restoration failed'}}
[pscustomobject]@{ok=$true;preservedFiles=$before.Count;existingRegistrationRestored=(Test-Path -LiteralPath $backup)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'uninstall-result.json') -Encoding utf8
'PASS uninstall preserved '+$before.Count+' license, project, draft and cloud library files'
