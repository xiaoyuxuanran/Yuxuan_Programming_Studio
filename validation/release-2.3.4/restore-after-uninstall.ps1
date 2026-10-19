$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$area=Join-Path $workspace 'work/r234';$app=Join-Path $area 'app'
$path=Join-Path $area 'install-acceptance.json';$report=Get-Content -LiteralPath $path -Raw -Encoding utf8 | ConvertFrom-Json
if($report.ok -or $report.uninstallExit -ne 0 -or -not $report.payload.ok -or -not $report.smoke.ok -or -not $report.preservationSmoke.ok){throw 'Unexpected recovery state'}
if(-not ((Get-Content -LiteralPath (Join-Path $area 'uninstall-final.log') -Raw) -match 'Uninstallation process succeeded')){throw 'Owned uninstaller did not succeed'}
$state=Get-Content -LiteralPath (Join-Path $area 'original-user-state.json') -Raw -Encoding utf8 | ConvertFrom-Json
$key='HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D394BCE3-729B-427F-A3EB-52885E97ED62}_is1'
if($state.existingRegistration){
 $current=Join-Path $area 'recovered-registration.reg'; & reg.exe export $key $current /y | Out-Null
 if($LASTEXITCODE -ne 0 -or (Get-FileHash -LiteralPath $current).Hash -ne $state.originalRegistrationSHA256){throw 'Original registry was not restored; inspect before writing'}
}
foreach($link in $state.shortcuts){
 if((Get-FileHash -LiteralPath $link.backup).Hash -ne $link.sha256){throw 'Backup shortcut differs'}
 if(Test-Path -LiteralPath $link.path){if((Get-FileHash -LiteralPath $link.path).Hash -ne $link.sha256){throw 'A shortcut was changed outside this test'}}
 else{
  $parent=[IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($link.path))
  if($parent -notin $state.shortcutFolders){throw 'Unexpected shortcut parent'}
  [IO.Directory]::CreateDirectory($parent) | Out-Null;Copy-Item -LiteralPath $link.backup -Destination $link.path
 }
 if((Get-FileHash -LiteralPath $link.path).Hash -ne $link.sha256){throw 'Shortcut restoration differs'}
}
foreach($relative in @('AppInventor.exe','runtime/python3.13.16/python.exe','server/war/WEB-INF/classes/com/google/appinventor/server/BundledExtensions.class','server/war/static/teaching/materials/Lesson56-Materials.zip')){if(Test-Path -LiteralPath (Join-Path $app $relative)){throw 'Owned program file remains'}}
$before=Get-Content -LiteralPath (Join-Path $area 'data-before-uninstall.json') -Raw -Encoding utf8 | ConvertFrom-Json
foreach($item in $before.PSObject.Properties){
 if(-not [IO.Path]::GetFullPath($item.Name).StartsWith($area+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Unsafe preservation path'}
 if(-not (Test-Path -LiteralPath $item.Name) -or (Get-FileHash -LiteralPath $item.Name).Hash -ne $item.Value){throw 'Preserved data differs'}
}
if((Get-Content -LiteralPath (Join-Path $app 'user-preserved-project.txt') -Raw) -ne 'A user-owned file inside the installation survives update and uninstall.'){throw 'Unrelated file differs'}
Copy-Item -LiteralPath $path -Destination (Join-Path $area 'acceptance-before-shortcut-parent-recovery.json')
$report | Add-Member -NotePropertyName mergedUninstallVerified -NotePropertyValue $true -Force
$report.ok=$true;$report.userStateRestored=$true;$report.failure=$null;$report.cleanupFailure=$null
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $path -Encoding utf8
Write-Output ('PASS uninstall exit 0; all '+$state.shortcuts.Count+' original shortcuts and registry restored; data preserved')
