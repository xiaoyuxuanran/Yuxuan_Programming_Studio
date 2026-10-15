$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$installed=[IO.Path]::GetFullPath((Join-Path $workspace 'work/安装验证 羽轩2.0'))
if(!$installed.StartsWith($workspace+'\work\',[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($installed) -ne '安装验证 羽轩2.0'){throw 'Unexpected uninstall target'}
$roots=@('work/已安装版 App验收/config','work/已安装版 App验收/war/WEB-INF/authkey','work/已安装版 App验收/war/WEB-INF/keystore','work/已安装版 App验收/war/WEB-INF/appengine-generated','work/已安装版 代码验收/projects')
$files=@();foreach($relative in $roots){$files+=Get-ChildItem -LiteralPath (Join-Path $workspace $relative) -File -Recurse}
$files+=Get-Item -LiteralPath (Join-Path $workspace 'work/已安装版 代码验收/studio.json')
$files+=Get-ChildItem -LiteralPath (Join-Path $workspace 'work/已安装版 代码验收/environments') -Filter 'studio-runtime.txt' -File -Recurse
$hashes=@($files | ForEach-Object {Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256} | Select-Object Path,Hash)
$hashes | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $workspace 'work/studio/uninstall-data-before.json') -Encoding utf8
$p=Start-Process -FilePath (Join-Path $installed 'unins000.exe') -ArgumentList ('/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG="'+(Join-Path $workspace 'work/uninstaller-suite-acceptance.log')+'"') -WindowStyle Hidden -Wait -PassThru
if($p.ExitCode -ne 0){throw ('Uninstall failed '+$p.ExitCode)}
foreach($entry in $hashes){if(!(Test-Path -LiteralPath $entry.Path) -or (Get-FileHash -LiteralPath $entry.Path -Algorithm SHA256).Hash -ne $entry.Hash){throw ('User data changed '+$entry.Path)}}
if(Test-Path -LiteralPath (Join-Path $installed 'AppInventor.exe')){throw 'Installed launcher remains'}
'PASS dedicated test uninstall exit 0; '+$hashes.Count+' protected files unchanged'
exit 0
