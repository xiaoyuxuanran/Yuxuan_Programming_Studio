from pathlib import Path
import re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'work/release-2.3.4'
for n in ['installed-smoke.py','installed-teaching.cjs','studio-view-check.cjs','UpdateNetworkCheck.cs']:
 s=(OLD/n).read_text(encoding='utf8').replace('2.3.4','2.4.5').replace('r234','r245').replace('Installed234','Installed245').replace('test-234','test-245')
 if n=='UpdateNetworkCheck.cs':s=s.replace('v2.3.5','v2.4.6').replace('to-2.3.5.exe','to-2.4.6.exe')
 (HERE/n).write_text(s,encoding='utf8')
p=HERE/'installed-smoke.py';s=p.read_text(encoding='utf8');a=s.index('def payload(');b=s.index('\ndef process_env(',a)
s=s[:a]+'''def payload(root, native):
    manifest=read_json(HERE/'target-files.json');files=manifest['files'];long_count=0
    assert manifest['version']=='2.4.5' and len(files)>59000
    for name,expected in files.items():
        assert digest(root/name).lower()==expected['sha256'], 'Installed payload differs: '+name
        if len(str(root/name))>260:long_count+=1
    assert long_count>1000, 'Expected complete SDK long paths'
    boards=read_json(root/'mixly/src/boards.json')
    assert {b['boardIndex'].split('/')[3] for b in boards}=={'arduino_avr','arduino_esp32','arduino_esp8266','micropython_esp32'}
    for excluded in ['license/device-license.bin','mixly/arduino-cli/Arduino15/inventory.yaml','LayoutCheck.exe']:
        assert not (root/excluded).exists(), excluded
    assert not list(root.glob('AppInventor-*-test.exe'))
    print('PASS full installed payload: '+str(len(files))+' files and '+str(long_count)+' long SDK paths',flush=True)
    return {'ok':True,'verifiedFiles':len(files),'longPathFiles':long_count,'fullManifest':True,'privateFilesExcluded':True}
''' +s[b:];p.write_text(s,encoding='utf8')
old=(OLD/'acceptance-final.ps1').read_text(encoding='utf-8-sig');prefix=old[:old.index('\ntry {\n Assert-WithinArea')]
prefix=prefix[prefix.index('\n$ErrorActionPreference'):].replace('2.3.4','2.4.5').replace('r234','r245')
prefix=prefix.replace("$group='Yuxuan Studio Acceptance 2.4.5 from 2.2 final'","$group='Yuxuan Studio Acceptance 2.4.5 full'")
prefix=prefix.replace("$folders=@('license','studio/projects','mixly/projects','mixly/custom-libraries','mixly/src','studio-view/data')","$folders=@('license','config','war/WEB-INF/appengine-generated','studio/projects','mixly/projects','mixly/custom-libraries','mixly/src','studio-view/data')")
main='''
try {
 Assert-WithinArea $installed | Out-Null;Assert-WithinArea $data | Out-Null
 if(Get-Process AppInventor,AppInventorCore,Mixly -ErrorAction SilentlyContinue){throw 'Stop workbench instances before the isolated installation acceptance'}
 if(Test-Path -LiteralPath $installed){throw 'Fresh full acceptance directory already exists; inspect it before reusing'}
 if(-not (Test-Path -LiteralPath $Installer -PathType Leaf)){throw 'Full installer missing'}
 $report.installerSHA256=(Get-FileHash -LiteralPath $Installer).Hash
 Save-OriginalState
 $grant=Join-Path $workspace 'work/activation/ui-test-data/license/device-license.bin'
 if(-not (Test-Path -LiteralPath $grant)){throw 'Same-user private test grant missing'}
 New-Item -ItemType Directory -Path (Join-Path $data 'license') -Force | Out-Null
 Copy-Item -LiteralPath $grant -Destination (Join-Path $data 'license/device-license.bin')
 $report.freshExit=Install-Candidate 'fresh-full'
 $report.payload=Run-Helper 'payload' 'installed-payload'
 $taskMarker=Join-Path $installed 'user-preserved-project.txt'
 [IO.File]::WriteAllText($taskMarker,'Unrelated user file retained after overwrite and uninstall.')
 $taskMarkerHash=(Get-FileHash -LiteralPath $taskMarker).Hash
 $report.smoke=Run-Helper 'smoke' 'installed-smoke'
 $before=Hash-PreservedData
 if($before.Count -lt 30){throw 'Too few retained data/dependency files'}
 $before | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $area 'data-before-reinstall.json') -Encoding utf8
 $report.preservedFiles=$before.Count
 $report.reinstallExit=Install-Candidate 'overwrite-full'
 $report.payload=Run-Helper 'payload' 'installed-payload'
 Assert-Preserved $before
 if((Get-FileHash -LiteralPath $taskMarker).Hash -ne $taskMarkerHash){throw 'Overwrite changed an unrelated file'}
 $report.preservationSmoke=Run-Helper 'preservation' 'installed-reinstall-smoke'
 Assert-Preserved $before
 $beforeUninstall=Hash-PreservedData
 $beforeUninstall | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $area 'data-before-uninstall.json') -Encoding utf8
 Uninstall-Isolated
 if((Get-FileHash -LiteralPath $taskMarker).Hash -ne $taskMarkerHash){throw 'Uninstall removed an unrelated file'}
 foreach($relative in @('runtime/python3.13.16/python.exe','server/war/WEB-INF/classes/com/google/appinventor/server/BundledExtensions.class','server/war/static/teaching/materials/Lesson56-Materials.zip')){if(Test-Path -LiteralPath (Join-Path $installed $relative)){throw ('Merged uninstall left managed file: '+$relative)}}
 Assert-Preserved $beforeUninstall
 $report['mergedUninstallVerified']=$true;$report['fullInstallerVerified']=$true
 $report.ok=$true
 Write-Host ('PASS clean full install, overwrite, uninstall and '+$beforeUninstall.Count+' retained user files')
}catch{$report.failure=$_.Exception.Message;throw}finally{
 try{Restore-OriginalState}catch{$report.cleanupFailure=$_.Exception.Message;$report.ok=$false;Write-Error $_ -ErrorAction Continue}
 $report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $area 'install-acceptance.json') -Encoding utf8
}
'''
param="param([string]$Installer=(Join-Path $PSScriptRoot 'package/AppInventor-Offline-Setup-x64.exe'))\n"
(HERE/'acceptance-full.ps1').write_text(param+prefix+main,encoding='utf-8-sig')
print('Prepared isolated full-install validation tools')
