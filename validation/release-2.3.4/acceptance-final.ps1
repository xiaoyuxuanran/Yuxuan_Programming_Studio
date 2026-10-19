param([string]$Installer=(Join-Path $PSScriptRoot 'package/Yuxuan-Programming-Studio-Update-2.2.0-to-2.3.4.exe'),[string]$BaseInstaller=(Join-Path $PSScriptRoot '../release-2.2/package/AppInventor-Offline-Setup-x64.exe'),[switch]$ResumeInstalled,[switch]$WaitForRebuiltInstaller)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$area=[IO.Path]::GetFullPath((Join-Path $workspace 'work/r234'))
New-Item -ItemType Directory -Path $area -Force | Out-Null
$installed=Join-Path $area 'app'
$data=Join-Path $area 'd'
$native=Join-Path $workspace 'work/native'
$helper=Join-Path $PSScriptRoot 'installed-smoke.py'
$snapshot=Join-Path $area 'original-user-state.json'
$registrationBackup=Join-Path $area 'original-uninstall-registration.reg'
$key='HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D394BCE3-729B-427F-A3EB-52885E97ED62}_is1'
$providerKey='Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D394BCE3-729B-427F-A3EB-52885E97ED62}_is1'
$group='Yuxuan Studio Acceptance 2.3.4 from 2.2 final'
$state=$null;$setupStarted=$false;$finishedUninstall=$false
$report=[ordered]@{ok=$false;installer=$Installer;installerSHA256=$null;installed=$installed;data=$data;freshExit=$null;reinstallExit=$null;uninstallExit=$null;preservedFiles=0;payload=$null;smoke=$null;preservationSmoke=$null;userStateRestored=$false;failure=$null;cleanupFailure=$null}

function Assert-WithinArea([string]$Path) {
 $absolute=[IO.Path]::GetFullPath($Path)
 if(-not $absolute.StartsWith($area+'\',[StringComparison]::OrdinalIgnoreCase)){throw ('Unsafe acceptance path: '+$absolute)}
 return $absolute
}
function Current-ShortcutFiles {
 $files=@()
 foreach($folder in $state.shortcutFolders){if(Test-Path -LiteralPath $folder -PathType Container){$files+=Get-ChildItem -LiteralPath $folder -Filter '*.lnk' -Recurse -File | ForEach-Object FullName}}
 foreach($file in $state.desktopFiles){if(Test-Path -LiteralPath $file -PathType Leaf){$files+=$file}}
 return @($files | Sort-Object -Unique)
}
function Save-OriginalState {
 if(Test-Path -LiteralPath $snapshot){
  $previousReport=Join-Path $area 'install-acceptance.json'
  if(-not (Test-Path -LiteralPath $previousReport)){throw 'Existing 2.3 snapshot has no restored acceptance report; inspect it before rerunning'}
  $previous=Get-Content -LiteralPath $previousReport -Encoding utf8 -Raw | ConvertFrom-Json
  if($previous.ok -or -not $previous.userStateRestored -or $previous.cleanupFailure){throw 'Existing 2.3 snapshot is not a safely restored failed attempt; inspect it before rerunning'}
  $script:state=Get-Content -LiteralPath $snapshot -Encoding utf8 -Raw | ConvertFrom-Json
  Assert-ShortcutsUnchanged
  if((Test-Path -LiteralPath $providerKey) -ne [bool]$state.existingRegistration){throw 'Original registry presence changed after the failed attempt'}
  if($state.existingRegistration){
   $retryExport=Join-Path $area 'retry-current-uninstall-registration.reg'
   & reg.exe export $key $retryExport /y | Out-Null
   if($LASTEXITCODE -ne 0 -or (Get-FileHash -LiteralPath $retryExport).Hash -ne $state.originalRegistrationSHA256){throw 'Original registration changed after the failed attempt'}
  }
  $index=1
  do{$attemptBackup=Join-Path $area ('install-acceptance-attempt-'+$index+'.json');$index++}while(Test-Path -LiteralPath $attemptBackup)
  Copy-Item -LiteralPath $previousReport -Destination $attemptBackup
  Write-Host 'Reusing independently preserved 2.3 original-state snapshot after verified restoration'
  return
 }
 $existed=Test-Path -LiteralPath $providerKey
 $original=if($existed){Get-ItemProperty -LiteralPath $providerKey}else{$null}
 if($existed){
  if($original.InstallLocation -and [IO.Path]::GetFullPath($original.InstallLocation).StartsWith($area+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Registry already points to this acceptance area; do not snapshot it as the real installation'}
  & reg.exe export $key $registrationBackup /y | Out-Null
  if($LASTEXITCODE -ne 0){throw 'Cannot preserve the existing uninstall registration'}
 }
 $groups=@('Yuxuan Programming Studio',$group)
 if($original -and $original.'Inno Setup: Icon Group'){$groups+=$original.'Inno Setup: Icon Group'}
 $folders=@()
 foreach($base in @([Environment]::GetFolderPath('Programs'),[Environment]::GetFolderPath('CommonPrograms'))){foreach($name in ($groups | Sort-Object -Unique)){if($name -and -not [IO.Path]::IsPathRooted($name) -and $name -notmatch '(^|[\\/])\.\.([\\/]|$)'){$folders+=Join-Path $base $name}}}
 $desktop=@([Environment]::GetFolderPath('DesktopDirectory'),[Environment]::GetFolderPath('CommonDesktopDirectory')) | ForEach-Object {Join-Path $_ 'Yuxuan Programming Studio.lnk'}
 $script:state=[ordered]@{existingRegistration=$existed;originalInstallLocation=$original.InstallLocation;originalRegistrationSHA256=$(if($existed){(Get-FileHash -LiteralPath $registrationBackup).Hash}else{$null});key=$key;shortcutFolders=@($folders | Sort-Object -Unique);desktopFiles=@($desktop | Sort-Object -Unique);shortcuts=@()}
 $backup=Join-Path $area 'shortcut-backup';New-Item -ItemType Directory -Path $backup | Out-Null
 $index=0
 foreach($file in (Current-ShortcutFiles)){
  $target=Join-Path $backup ($index.ToString()+'.lnk');Copy-Item -LiteralPath $file -Destination $target
  $script:state.shortcuts+=@{path=$file;backup=$target;sha256=(Get-FileHash -LiteralPath $file).Hash};$index++
 }
 $state | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $snapshot -Encoding utf8
}
function Assert-ShortcutsUnchanged([switch]$AllowOwnedNew) {
 $current=@(Current-ShortcutFiles)
 $expected=@($state.shortcuts | ForEach-Object path)
 if(-not $AllowOwnedNew -and $current.Count -ne $expected.Count){throw 'Installer unexpectedly changed the set of user shortcuts'}
 foreach($item in $state.shortcuts){
  if(-not (Test-Path -LiteralPath $item.path)){throw ('User shortcut missing: '+$item.path)}
  if((Get-FileHash -LiteralPath $item.path).Hash -ne $item.sha256){
   if(-not $AllowOwnedNew){throw ('User shortcut changed: '+$item.path)}
   # The disabled program-group wizard still creates links in its default group.
   # Permit only links redirected to this isolated install, with an intact backup.
   if(-not (Test-Path -LiteralPath $item.backup) -or (Get-FileHash -LiteralPath $item.backup).Hash -ne $item.sha256){throw ('Shortcut backup changed: '+$item.path)}
   $shell=New-Object -ComObject WScript.Shell
   $target=[string]$shell.CreateShortcut($item.path).TargetPath
   if(-not $target -or -not [IO.Path]::GetFullPath($target).StartsWith($installed+'\',[StringComparison]::OrdinalIgnoreCase)){throw ('Shortcut changed outside this test install: '+$item.path)}
  }
 }
 if($AllowOwnedNew){
  foreach($file in $current){
   if($file -notin $expected){
    $shell=New-Object -ComObject WScript.Shell
    $link=$shell.CreateShortcut($file);$target=[string]$link.TargetPath
    if(-not $target -or -not [IO.Path]::GetFullPath($target).StartsWith($installed+'\',[StringComparison]::OrdinalIgnoreCase)){throw ('Unrelated new shortcut was left unchanged: '+$file)}
   }
  }
 }
}
function Restore-OriginalState {
 if(-not $state){return}
 if(Test-Path -LiteralPath $providerKey){
  $current=Get-ItemProperty -LiteralPath $providerKey
  if($current.InstallLocation -and [IO.Path]::GetFullPath($current.InstallLocation).TrimEnd('\') -eq $installed.TrimEnd('\')){
   & reg.exe delete $key /f | Out-Null
   if($LASTEXITCODE -ne 0){throw 'Cannot remove the isolated test registration'}
  }elseif(-not $state.existingRegistration -or $current.InstallLocation -ne $state.originalInstallLocation){throw 'Unrelated new registration appeared during acceptance; it was left unchanged'}
 }
 if($state.existingRegistration){& reg.exe import $registrationBackup | Out-Null;if($LASTEXITCODE -ne 0){throw 'Cannot restore the original uninstall registration'}}
 foreach($file in (Current-ShortcutFiles)){
  if(-not ($state.shortcuts | Where-Object path -eq $file)){
   # Remove a newly created link only when its target is the isolated test install.
   $shell=New-Object -ComObject WScript.Shell
   $link=$shell.CreateShortcut($file);$target=[string]$link.TargetPath
   if($target -and [IO.Path]::GetFullPath($target).StartsWith($installed+'\',[StringComparison]::OrdinalIgnoreCase)){
    Remove-Item -LiteralPath $file -Force
   }else{throw ('Unrelated new shortcut was left unchanged: '+$file)}
  }
 }
 foreach($item in $state.shortcuts){
  if(-not (Test-Path -LiteralPath $item.path) -or (Get-FileHash -LiteralPath $item.path).Hash -ne $item.sha256){
   New-Item -ItemType Directory -Path (Split-Path -Parent $item.path) -Force | Out-Null
   Copy-Item -LiteralPath $item.backup -Destination $item.path -Force
  }
 }
 Assert-ShortcutsUnchanged
 if((Test-Path -LiteralPath $providerKey) -ne [bool]$state.existingRegistration){throw 'Original uninstall-registration presence was not restored'}
 if($state.existingRegistration){
  $restored=Get-ItemProperty -LiteralPath $providerKey
  if($restored.InstallLocation -ne $state.originalInstallLocation){throw 'Original installation location was not restored'}
  $restoredExport=Join-Path $area 'restored-uninstall-registration.reg'
  & reg.exe export $key $restoredExport /y | Out-Null
  if($LASTEXITCODE -ne 0 -or (Get-FileHash -LiteralPath $restoredExport).Hash -ne $state.originalRegistrationSHA256){throw 'Original uninstall-registration export contents were not restored exactly'}
 }
 $script:report.userStateRestored=$true
}
function Install-Candidate([string]$Stage) {
 $log=Join-Path $area ($Stage+'-setup.log')
 $args='/CURRENTUSER /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /NOICONS /TASKS="!desktopicon" /GROUP="'+$group+'" /DIR="'+$installed+'" /LOG="'+$log+'"'
 $script:setupStarted=$true
 $process=Start-Process -FilePath $Installer -ArgumentList $args -WindowStyle Hidden -Wait -PassThru
 if($process.ExitCode -ne 0){throw ($Stage+' installer exit '+$process.ExitCode)}
 Assert-ShortcutsUnchanged -AllowOwnedNew
 $registry=Get-ItemProperty -LiteralPath $providerKey
 if([IO.Path]::GetFullPath($registry.InstallLocation).TrimEnd('\') -ne $installed.TrimEnd('\')){throw 'Installer registered an unexpected directory'}
 Write-Host ('PASS '+$Stage+' installer exit 0; shortcut targets constrained to the isolated install')
 return $process.ExitCode
}
function Run-Helper([string]$Mode,[string]$Name) {
 $output=Join-Path $area ($Name+'.json')
 & (Join-Path $installed 'runtime/python3.13.16/python.exe') -X utf8 $helper $Mode --installed $installed --native $native --data $data --report $output | Out-Host
 if($LASTEXITCODE -ne 0){throw ($Mode+' installed acceptance failed')}
 return Get-Content -LiteralPath $output -Encoding utf8 -Raw | ConvertFrom-Json
}
function Hash-PreservedData {
 $hashes=@{}
 $folders=@('license','studio/projects','mixly/projects','mixly/custom-libraries','mixly/src','studio-view/data')
 foreach($relative in $folders){$folder=Join-Path $data $relative;if(Test-Path -LiteralPath $folder){foreach($file in (Get-ChildItem -LiteralPath $folder -Recurse -File)){$hashes[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName).Hash}}}
 $studio=Join-Path $data 'studio/studio.json';if(Test-Path -LiteralPath $studio){$hashes[$studio]=(Get-FileHash -LiteralPath $studio).Hash}
 $environments=Join-Path $data 'studio/environments'
 foreach($version in (Get-ChildItem -LiteralPath $environments -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object Name -eq '3.8.9')){
  foreach($relative in @('Lib/site-packages/colorama','Lib/site-packages/colorama-0.4.6.dist-info')){foreach($file in (Get-ChildItem -LiteralPath (Join-Path $version.FullName $relative) -Recurse -File)){$hashes[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName).Hash}}
  $custom=Join-Path $version.FullName 'Lib/site-packages/acceptance_custom.py';if(Test-Path -LiteralPath $custom){$hashes[$custom]=(Get-FileHash -LiteralPath $custom).Hash}
 }
 return $hashes
}
function Assert-Preserved($Hashes) {
 foreach($file in $Hashes.Keys){Assert-WithinArea $file | Out-Null;if(-not (Test-Path -LiteralPath $file) -or (Get-FileHash -LiteralPath $file).Hash -ne $Hashes[$file]){throw ('Acceptance user data changed: '+$file)}}
}
function Uninstall-Isolated {
 if($finishedUninstall){return}
 $uninstaller=Assert-WithinArea (Join-Path $installed 'unins000.exe')
 if(Test-Path -LiteralPath $uninstaller){
  $process=Start-Process -FilePath $uninstaller -ArgumentList ('/CURRENTUSER /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG="'+(Join-Path $area 'uninstall.log')+'"') -WindowStyle Hidden -Wait -PassThru
  $script:report.uninstallExit=$process.ExitCode
  if($process.ExitCode -ne 0){throw ('Isolated uninstaller exit '+$process.ExitCode)}
  if(Test-Path -LiteralPath (Join-Path $installed 'AppInventor.exe')){throw 'Isolated executable still exists after uninstall'}
 }
 $script:finishedUninstall=$true
}

try {
 Assert-WithinArea $installed | Out-Null;Assert-WithinArea $data | Out-Null

 if(Get-Process AppInventor,AppInventorCore,Mixly -ErrorAction SilentlyContinue){throw 'Stop all workspace/Core tests before running the installer acceptance'}
 if($ResumeInstalled){
  $previous=Get-Content -LiteralPath (Join-Path $area 'install-acceptance.json') -Raw -Encoding utf8 | ConvertFrom-Json
  $verifiedIntermediate=$false
  $resumeProof=Join-Path $area 'verified-resume.json'
  if(Test-Path -LiteralPath $resumeProof){
   $verified=Get-Content -LiteralPath $resumeProof -Raw -Encoding utf8 | ConvertFrom-Json
   $verifiedIntermediate=($verified.ok -and [IO.Path]::GetFullPath($verified.installed) -eq $installed -and $verified.previousInstallerSHA256 -eq $previous.installerSHA256 -and $verified.finalInstallerSHA256 -eq (Get-FileHash -LiteralPath $Installer).Hash -and $verified.launcherSHA256 -eq (Get-FileHash -LiteralPath (Join-Path $installed 'AppInventor.exe')).Hash)
  }
  if($previous.ok -or -not $previous.userStateRestored -or $previous.cleanupFailure -or $previous.freshExit -ne 0 -or (($previous.installerSHA256 -ne (Get-FileHash -LiteralPath $Installer).Hash) -and -not $verifiedIntermediate)){throw 'Cannot resume an unverified or different candidate installation'}
  if(-not (Test-Path -LiteralPath (Join-Path $installed 'AppInventor.exe')) -or -not (Test-Path -LiteralPath (Join-Path $installed 'unins000.exe'))){throw 'Verified test installation is not present'}
 }elseif(Test-Path -LiteralPath $installed){
  $previous=Get-Content -LiteralPath (Join-Path $area 'install-acceptance.json') -Raw -Encoding utf8 | ConvertFrom-Json
  if($previous.ok -or -not $previous.userStateRestored -or $previous.cleanupFailure -or $previous.uninstallExit -ne 0){throw 'Existing acceptance directory has no completed safe uninstall'}
  if((Test-Path -LiteralPath (Join-Path $installed 'AppInventor.exe')) -or (Test-Path -LiteralPath (Join-Path $installed 'unins000.exe'))){throw 'Existing acceptance installation is still installed'}
  $residue=@(Get-ChildItem -LiteralPath $installed -Recurse -Force)
  if(@($residue | Where-Object {($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -or (-not $_.PSIsContainer -and $_.Extension -ne '.pyc')}).Count){throw 'Unexpected files remain in the uninstalled test directory'}
  $index=1;do{$residueBackup=Assert-WithinArea (Join-Path $area ('uninstalled-bytecode-residue-'+$index));$index++}while(Test-Path -LiteralPath $residueBackup)
  $residueSource=Assert-WithinArea $installed
  Move-Item -LiteralPath $residueSource -Destination $residueBackup
 }
 $grant=Join-Path $workspace 'work/activation/ui-test-data/license/device-license.bin'
 if(-not (Test-Path -LiteralPath $grant)){throw 'Existing same-user grant missing; no activation request is made by this test'}
 Save-OriginalState
 New-Item -ItemType Directory -Path (Join-Path $data 'license') -Force | Out-Null
 Copy-Item -LiteralPath $grant -Destination (Join-Path $data 'license/device-license.bin')

 if((Get-FileHash -LiteralPath $BaseInstaller).Hash -ne '6D7358461F129E575CB42C3943DD14EDFAE442E77C77C98BD515C032FC97328D'){throw 'Unexpected 2.3.0 baseline installer'}
 $taskPatch=$Installer
 if($ResumeInstalled){$setupStarted=$true;$report.freshExit=0}else{
  $Installer=$BaseInstaller
  $report.freshExit=Install-Candidate 'base-2.2.0'
  $Installer=$taskPatch
 }
 if(-not (Test-Path -LiteralPath $Installer -PathType Leaf)){throw 'Final 2.2.0-to-2.3.4 patch is missing'}
 $report.installerSHA256=(Get-FileHash -LiteralPath $Installer).Hash
 $wrong=Assert-WithinArea (Join-Path $area 'empty-directory')
 $rejected=Start-Process -FilePath $Installer -ArgumentList ('/CURRENTUSER /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR="'+$wrong+'" /LOG="'+(Join-Path $area 'rejected-empty.log')+'"') -WindowStyle Hidden -Wait -PassThru
 if($rejected.ExitCode -eq 0 -or (Test-Path -LiteralPath (Join-Path $wrong 'AppInventor.exe'))){throw 'Incremental package accepted an empty directory'}
 $report['emptyDirectoryRejected']=$true
 $taskMarker=Join-Path $installed 'user-preserved-project.txt'
 [IO.File]::WriteAllText($taskMarker,'A user-owned file inside the installation survives update and uninstall.')
 $taskMarkerHash=(Get-FileHash -LiteralPath $taskMarker).Hash
 $report['patchExit']=Install-Candidate 'patch-2.3.4'
 if((Get-FileHash -LiteralPath $taskMarker).Hash -ne $taskMarkerHash){throw 'Update overwrote an unrelated user file'}

 $report.payload=Run-Helper 'payload' 'installed-payload'
 $report.smoke=Run-Helper 'smoke' 'installed-smoke'
 $before=Hash-PreservedData
 if($before.Count -lt 8){throw 'Too few retained project/dependency files for the upgrade test'}
 $before | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $area 'data-before-reinstall.json') -Encoding utf8
 $report.preservedFiles=$before.Count
 if($WaitForRebuiltInstaller){
  $report['initialVerifiedInstallerSHA256']=$report.installerSHA256
  do{
   Start-Sleep -Seconds 2
   $rebuilt=Get-Content -LiteralPath (Join-Path $area 'installer-build-result.json') -Raw -Encoding utf8 | ConvertFrom-Json
   if($rebuilt.state -eq 'failed'){throw $rebuilt.failure}
  }while(-not $rebuilt.ok -or $rebuilt.sha256 -eq $report.installerSHA256)
 
  if($report.installerSHA256 -ne $rebuilt.sha256){throw 'Rebuilt installer hash changed'}
 }
 $report.reinstallExit=Install-Candidate 'reinstall'
 $report.payload=Run-Helper 'payload' 'installed-payload'
 Assert-Preserved $before
 $report.preservationSmoke=Run-Helper 'preservation' 'installed-reinstall-smoke'
 Assert-Preserved $before
 $beforeUninstall=Hash-PreservedData
 $beforeUninstall | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $area 'data-before-uninstall.json') -Encoding utf8
 Uninstall-Isolated
 if((Get-FileHash -LiteralPath $taskMarker).Hash -ne $taskMarkerHash){throw 'Uninstaller removed an unrelated user file'}
 if(Test-Path -LiteralPath (Join-Path $installed 'runtime/python3.13.16/python.exe')){throw 'Merged uninstall left a base runtime behind'}
 if(Test-Path -LiteralPath (Join-Path $installed 'server/war/WEB-INF/classes/com/google/appinventor/server/BundledExtensions.class')){throw 'Merged uninstall left new program code behind'}
 $report['mergedUninstallVerified']=$true
 Assert-Preserved $beforeUninstall
 Write-Output ('PASS reinstall and uninstall preserve '+$beforeUninstall.Count+' license/project/dependency files')
 $report.ok=$true
}catch {
 $report.failure=$_.Exception.Message
 throw
}finally {
 try {if($setupStarted -and $report.ok){Uninstall-Isolated};Restore-OriginalState}catch{$report.cleanupFailure=$_.Exception.Message;$report.ok=$false;Write-Error ('Acceptance cleanup needs attention: '+$report.cleanupFailure) -ErrorAction Continue}
 $report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $area 'install-acceptance.json') -Encoding utf8
}
