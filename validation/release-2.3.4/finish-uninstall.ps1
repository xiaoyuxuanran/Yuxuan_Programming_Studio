$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$area=Join-Path $workspace 'work/r234'
$installed=Join-Path $area 'app'
$path=Join-Path $area 'install-acceptance.json'
$report=Get-Content -LiteralPath $path -Raw -Encoding utf8 | ConvertFrom-Json
if($report.ok -or -not $report.userStateRestored -or $report.cleanupFailure -or -not $report.payload.ok -or -not $report.smoke.ok -or -not $report.preservationSmoke.ok -or $report.reinstallExit -ne 0 -or $report.failure -ne 'Isolated uninstaller exit 1'){throw 'Unexpected acceptance state'}
if(Get-Process AppInventor,AppInventorCore,Mixly -ErrorAction SilentlyContinue){throw 'A workbench instance is still running; leave it untouched'}
$state=Get-Content -LiteralPath (Join-Path $area 'original-user-state.json') -Raw -Encoding utf8 | ConvertFrom-Json
$key='HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D394BCE3-729B-427F-A3EB-52885E97ED62}_is1'
$provider='Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D394BCE3-729B-427F-A3EB-52885E97ED62}_is1'
$backup=Join-Path $area 'original-uninstall-registration.reg'
function Assert-CurrentState {
 if((Test-Path -LiteralPath $provider) -ne [bool]$state.existingRegistration){throw 'Original registration presence changed'}
 if($state.existingRegistration){
  $current=Join-Path $area 'cleanup-current-registration.reg'
  & reg.exe export $key $current /y | Out-Null
  if($LASTEXITCODE -ne 0 -or (Get-FileHash -LiteralPath $current).Hash -ne $state.originalRegistrationSHA256){throw 'Original registration changed'}
 }
 foreach($link in $state.shortcuts){if(-not (Test-Path -LiteralPath $link.path) -or (Get-FileHash -LiteralPath $link.path).Hash -ne $link.sha256){throw 'Original shortcut changed'}}
}
Assert-CurrentState
$before=Get-Content -LiteralPath (Join-Path $area 'data-before-uninstall.json') -Raw -Encoding utf8 | ConvertFrom-Json
foreach($item in $before.PSObject.Properties){if(-not [IO.Path]::GetFullPath($item.Name).StartsWith($area+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Preservation fixture escapes owned area'}}
$uninstaller=[IO.Path]::GetFullPath((Join-Path $installed 'unins000.exe'))
if(-not $uninstaller.StartsWith($area+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Unsafe cleanup path'}
$marker=Join-Path $installed 'user-preserved-project.txt';$markerHash=(Get-FileHash -LiteralPath $marker).Hash
Copy-Item -LiteralPath $path -Destination (Join-Path $area 'install-acceptance-before-mutex-cleanup.json')
try {
 $report.userStateRestored=$false
 $process=Start-Process -FilePath $uninstaller -ArgumentList ('/CURRENTUSER /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG="'+(Join-Path $area 'uninstall-final.log')+'"') -WindowStyle Hidden -Wait -PassThru
 $report.uninstallExit=$process.ExitCode
 if($process.ExitCode -ne 0){throw ('Isolated uninstaller exit '+$process.ExitCode)}
 foreach($relative in @('AppInventor.exe','runtime/python3.13.16/python.exe','server/war/WEB-INF/classes/com/google/appinventor/server/BundledExtensions.class','server/war/static/teaching/materials/Lesson56-Materials.zip')){
  if(Test-Path -LiteralPath (Join-Path $installed $relative)){throw ('Merged uninstall left program file: '+$relative)}
 }
 if((Get-FileHash -LiteralPath $marker).Hash -ne $markerHash){throw 'Uninstall removed unrelated file'}
 foreach($item in $before.PSObject.Properties){if(-not (Test-Path -LiteralPath $item.Name) -or (Get-FileHash -LiteralPath $item.Name).Hash -ne $item.Value){throw ('Data was not preserved: '+$item.Name)}}
 $report | Add-Member -NotePropertyName mergedUninstallVerified -NotePropertyValue $true -Force
 $report.failure=$null;$report.ok=$true
}catch{$report.failure=$_.Exception.Message;throw}finally{
 try{
  if($state.existingRegistration){& reg.exe import $backup | Out-Null;if($LASTEXITCODE -ne 0){throw 'Cannot restore original registration'}}
  elseif(Test-Path -LiteralPath $provider){$current=Get-ItemProperty -LiteralPath $provider;if($current.InstallLocation -and [IO.Path]::GetFullPath($current.InstallLocation).TrimEnd('\') -eq $installed.TrimEnd('\')){& reg.exe delete $key /f | Out-Null}else{throw 'Unrelated registration appeared'}}
  foreach($link in $state.shortcuts){
   if((Get-FileHash -LiteralPath $link.backup).Hash -ne $link.sha256){throw 'Shortcut backup changed'}
   if(-not (Test-Path -LiteralPath $link.path) -or (Get-FileHash -LiteralPath $link.path).Hash -ne $link.sha256){[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($link.path)) | Out-Null;Copy-Item -LiteralPath $link.backup -Destination $link.path -Force}
  }
  Assert-CurrentState;$report.userStateRestored=$true
 }catch{$report.ok=$false;$report.cleanupFailure=$_.Exception.Message;Write-Error $_ -ErrorAction Continue}
 $report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $path -Encoding utf8
}
Write-Output 'PASS final uninstall, merged file removal, user data preservation and original registration restoration'
