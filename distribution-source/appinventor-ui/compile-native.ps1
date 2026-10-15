$ErrorActionPreference='Stop'
$taskWork=Split-Path $PSScriptRoot -Parent
$native=Join-Path $taskWork 'native'
& (Join-Path $native 'runtime/python3.13.16/python.exe') (Join-Path $PSScriptRoot 'stage-web.py')
if($LASTEXITCODE -ne 0){throw 'Web staging failed'}
$classes=Join-Path $native 'server/war/WEB-INF/classes'
$libs=Join-Path $native 'server/war/WEB-INF/lib/*'
$servlet=Join-Path $native 'server/sdk/jetty94/jetty-home/lib/servlet-api-3.1.jar'
& (Join-Path $native 'runtime/java17/bin/javac.exe') -encoding UTF-8 -cp ($classes+';'+$libs+';'+$servlet) -d $classes (Join-Path $PSScriptRoot 'OfflineUsbServlet.java')
if($LASTEXITCODE -ne 0){throw 'USB servlet compilation failed'}
$compiler='C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'
& $compiler /nologo /target:winexe /platform:x64 ('/win32icon:'+(Join-Path $native 'resources/brand.ico')) ('/out:'+(Join-Path $native 'AppInventorCore.exe')) /r:System.Windows.Forms.dll /r:System.Drawing.dll (Join-Path $taskWork 'AppInventor.cs')
if($LASTEXITCODE -ne 0){throw 'Core compilation failed'}
Write-Output 'Core and local USB servlet compiled.'
