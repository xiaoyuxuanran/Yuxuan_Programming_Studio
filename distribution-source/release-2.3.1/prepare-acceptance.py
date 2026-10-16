from pathlib import Path
import shutil
HERE=Path(__file__).resolve().parent;old=HERE.parent/'release-2.3'
s=(old/'install-acceptance.ps1').read_text(encoding='utf-8-sig')
s=s.replace("param([string]$Installer=(Join-Path $PSScriptRoot 'package/AppInventor-Offline-Setup-x64.exe'),", "param([string]$Installer=(Join-Path $PSScriptRoot 'package/Yuxuan-Programming-Studio-Update-2.3.0-to-2.3.1.exe'),[string]$BaseInstaller=(Join-Path $PSScriptRoot '../../outputs/AppInventor-Offline-Setup-x64.exe'),")
s=s.replace("$installed=Join-Path $area '安装 羽轩2.3'", "$installed=Join-Path $area 'app'")
s=s.replace("$data=Join-Path $area '数据 羽轩2.3'", "$data=Join-Path $area '用户数据'")
s=s.replace("$group='Yuxuan Studio Acceptance 2.3'", "$group='Yuxuan Studio Acceptance 2.3.1'")
needle=" if($ResumeInstalled){$setupStarted=$true;$report.freshExit=0;Write-Host 'Resuming the same candidate; installed payload hashes will be verified again'}else{$report.freshExit=Install-Candidate 'fresh'}"
assert needle in s
s=s.replace(needle,""" if((Get-FileHash -LiteralPath $BaseInstaller).Hash -ne 'D743DB5CAFD681F5DF99C0DEBE2FD8B1281A2D2C72C72365BEF8A77D62EA5A73'){throw 'Unexpected 2.3.0 baseline installer'}
 $wrong=Assert-WithinArea (Join-Path $area 'empty-directory')
 $rejected=Start-Process -FilePath $Installer -ArgumentList ('/CURRENTUSER /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR="'+$wrong+'" /LOG="'+(Join-Path $area 'rejected-empty.log')+'"') -WindowStyle Hidden -Wait -PassThru
 if($rejected.ExitCode -eq 0 -or (Test-Path -LiteralPath (Join-Path $wrong 'AppInventor.exe'))){throw 'Incremental package accepted an empty directory'}
 $report['emptyDirectoryRejected']=$true
 $taskPatch=$Installer
 if($ResumeInstalled){$setupStarted=$true;$report.freshExit=0}else{
  $Installer=$BaseInstaller
  $report.freshExit=Install-Candidate 'base-2.3.0'
  $Installer=$taskPatch
 }
 $taskMarker=Join-Path $installed 'user-preserved-project.txt'
 [IO.File]::WriteAllText($taskMarker,'A user-owned file inside the installation survives update and uninstall.')
 $taskMarkerHash=(Get-FileHash -LiteralPath $taskMarker).Hash
 $report['patchExit']=Install-Candidate 'patch-2.3.1'
 if((Get-FileHash -LiteralPath $taskMarker).Hash -ne $taskMarkerHash){throw 'Update overwrote an unrelated user file'}
""")
s=s.replace(" Uninstall-Isolated\n Assert-Preserved $beforeUninstall", " Uninstall-Isolated\n if((Get-FileHash -LiteralPath $taskMarker).Hash -ne $taskMarkerHash){throw 'Uninstaller removed an unrelated user file'}\n if(Test-Path -LiteralPath (Join-Path $installed 'runtime/python3.13.16/python.exe')){throw 'Merged uninstall left a base runtime behind'}\n if(Test-Path -LiteralPath (Join-Path $installed 'server/war/WEB-INF/classes/com/google/appinventor/server/BundledExtensions.class')){throw 'Merged uninstall left new program code behind'}\n $report['mergedUninstallVerified']=$true\n Assert-Preserved $beforeUninstall")
(HERE/'install-acceptance.ps1').write_text(s,encoding='utf-8-sig')
s=(old/'installed-smoke.py').read_text(encoding='utf-8')
needle="    relative = CRITICAL + LONG_PATHS"
assert needle in s
s=s.replace(needle,needle+"\n    relative += [f['path'] for f in json.loads((HERE / 'update-manifest.json').read_text(encoding='utf-8'))['files']]")
(HERE/'installed-smoke.py').write_text(s,encoding='utf-8')
print('Prepared isolated base-install / true patch / repeat-patch / merged-uninstall acceptance.')
