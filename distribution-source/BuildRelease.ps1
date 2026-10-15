param([string]$Workspace,[string]$OutputDirectory)
$ErrorActionPreference='Stop'
$Workspace=[IO.Path]::GetFullPath($Workspace)
$native=Join-Path $Workspace 'work/native'
if(-not (Test-Path -LiteralPath (Join-Path $native 'AppInventor.exe'))){throw 'Prepare native payload first'}
# Inno Setup 7 supports extended-length source, destination, and uninstall paths.
$compiler=Join-Path $Workspace 'work/build-tools/InnoSetup7/ISCC.exe'
if(-not (Test-Path -LiteralPath $compiler)){throw 'Install the signed Inno Setup 7.1.0 x64 compiler in work/build-tools/InnoSetup7 first'}
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
& $compiler /Qp ('/O'+[IO.Path]::GetFullPath($OutputDirectory)) (Join-Path $Workspace 'work/Setup.iss')
if($LASTEXITCODE -ne 0){throw ('Installer compile failed: '+$LASTEXITCODE)}
