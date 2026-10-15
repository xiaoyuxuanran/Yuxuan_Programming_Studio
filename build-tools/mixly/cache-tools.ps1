$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$cliDir=Join-Path $workspace 'work/native/mixly/arduino-cli'
$cache=Join-Path $PSScriptRoot 'downloads/staging/packages'
# Arduino CLI's Go downloader stalls on this connection; WinHTTP downloads the same signed archives quickly.
$indexes=@('package_index.json','package_esp8266com_index.json','package_esp32_index.json')
$packages=@()
foreach($name in $indexes){$j=Get-Content -LiteralPath (Join-Path $cliDir ('Arduino15/'+$name)) -Raw|ConvertFrom-Json;$packages+=@($j.packages)}
$requested=@(@('esp8266','esp8266','3.1.2'),@('esp32','esp32','2.0.17'))
$archives=@()
foreach($wanted in $requested){
  $pkg=$packages|Where-Object name -eq $wanted[0]|Select-Object -First 1
  $platform=$pkg.platforms|Where-Object { $_.architecture -eq $wanted[1] -and $_.version -eq $wanted[2] }|Select-Object -First 1
  if(!$platform){throw 'Missing platform'}
  $archives+=$platform
  foreach($dep in $platform.toolsDependencies){
    $owner=$packages|Where-Object name -eq $dep.packager|Select-Object -First 1
    $tool=$owner.tools|Where-Object { $_.name -eq $dep.name -and $_.version -eq $dep.version }|Select-Object -First 1
    $systems=@($tool.systems|Where-Object { $_.host -match 'mingw|windows' })
    $system=$systems|Where-Object host -match 'x86_64'|Select-Object -First 1
    if(!$system){$system=$systems|Select-Object -First 1}
    if(!$system){throw ('Missing Windows tool '+$dep.name)}
    $archives+=$system
  }
}
foreach($archive in $archives|Sort-Object archiveFileName -Unique){
  $file=Join-Path $cache $archive.archiveFileName
  $expected=$archive.checksum.Split(':')[1].ToLowerInvariant()
  if((Test-Path -LiteralPath $file) -and (Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -eq $expected){'Cached '+$archive.archiveFileName;continue}
  'Downloading '+$archive.archiveFileName+' ('+$archive.size+' bytes)'
  Invoke-WebRequest $archive.url -OutFile ($file+'.download')
  if((Get-FileHash -LiteralPath ($file+'.download')).Hash.ToLowerInvariant() -ne $expected){throw ('Checksum mismatch '+$file)}
  Move-Item -LiteralPath ($file+'.download') -Destination $file -Force
  'Verified '+$archive.archiveFileName
}
foreach($core in @('esp8266:esp8266@3.1.2','esp32:esp32@2.0.17')){
  & (Join-Path $cliDir 'arduino-cli.exe') core install $core --config-file (Join-Path $cliDir 'arduino-cli.json') --no-color
  if($LASTEXITCODE -ne 0){throw ('Core install failed '+$core)}
}
& (Join-Path $cliDir 'arduino-cli.exe') core list --config-file (Join-Path $cliDir 'arduino-cli.json') --no-color
if($LASTEXITCODE -ne 0){throw 'Core verification failed'}
