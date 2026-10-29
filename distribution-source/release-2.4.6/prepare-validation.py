from pathlib import Path
R=Path.cwd();H=R/'work/release-2.4.6';O=R/'work/release-2.4.5'
for n in ['acceptance-full.ps1','installed-smoke.py','installed-teaching.cjs','studio-view-check.cjs','UpdateNetworkCheck.cs']:
 s=(O/n).read_text(encoding='utf-8-sig').replace('2.4.5','2.4.6').replace('r245','r246')
 if n=='UpdateNetworkCheck.cs':s=s.replace('v2.4.6";asset[','v2.4.7";asset[').replace('to-2.4.6.exe','to-2.4.7.exe')
 if n=='acceptance-full.ps1':
  marker=' $before=Hash-PreservedData'
  insertion='''
 $newInstaller=$Installer
 $Installer=Join-Path $workspace 'work/release-2.4.5/package/AppInventor-Offline-Setup-x64.exe'
 Install-Candidate 'baseline-2.4.5' | Out-Null
 if((Get-Item (Join-Path $installed 'AppInventor.exe')).VersionInfo.FileVersion -ne '2.4.5.0'){throw 'Baseline install version mismatch'}
 $Installer=Join-Path $PSScriptRoot 'package/Yuxuan-Programming-Studio-Update-2.4.5-to-2.4.6.exe'
 $report['incrementalExit']=Install-Candidate 'incremental-2.4.5'
 $report.payload=Run-Helper 'payload' 'installed-incremental-payload'
 $report['incrementalVerified']=$true
 $Installer=$newInstaller
'''
  s=s.replace(marker,insertion+marker,1)
 (H/n).write_text(s,encoding='utf8')
print('Prepared full and 2.4.5 upgrade acceptance')
