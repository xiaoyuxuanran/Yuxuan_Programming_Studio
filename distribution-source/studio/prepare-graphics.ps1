# Supplement official NuGet CPython with the matching complete stdlib and Tcl/Tk.
$ErrorActionPreference='Stop'
$downloads=Join-Path $PSScriptRoot 'downloads';$native=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../native'))
foreach($version in @('3.8.9','3.13.16')) {
  foreach($component in @('lib','tcltk')) {
    $msi=Join-Path $downloads ($component+'-'+$version+'.msi');$dest=Join-Path $downloads ($component+'-'+$version)
    if(!(Test-Path -LiteralPath $msi)){Invoke-WebRequest ('https://www.python.org/ftp/python/'+$version+'/amd64/'+$component+'.msi') -OutFile $msi}
    $args='/a "'+$msi+'" /qn TARGETDIR="'+$dest+'"'
    $p=Start-Process msiexec.exe -ArgumentList $args -WindowStyle Hidden -Wait -PassThru
    if($p.ExitCode -ne 0){throw ('Official MSI extraction failed '+$p.ExitCode)}
    foreach($part in @('DLLs','Lib','libs','tcl')) {
      if(Test-Path -LiteralPath ($dest+'/'+$part)){Copy-Item -LiteralPath ($dest+'/'+$part) -Destination ($native+'/runtime/python'+$version) -Recurse -Force}
    }
  }
}
$wheels=Join-Path $native 'studio/pip-wheels';New-Item -ItemType Directory -Force $wheels | Out-Null
foreach($package in @(@{Name='pip';Version='24.3.1';Pattern='pip-24.3.1-py3-none-any.whl'},@{Name='pygame';Version='2.6.1';Pattern='pygame-2.6.1-cp38-cp38-win_amd64.whl'},@{Name='pygame';Version='2.6.1';Pattern='pygame-2.6.1-cp313-cp313-win_amd64.whl'})) {
  $meta=Invoke-RestMethod ('https://pypi.org/pypi/'+$package.Name+'/'+$package.Version+'/json')
  $wheel=$meta.urls | Where-Object filename -eq $package.Pattern
  $target=Join-Path $wheels $wheel.filename
  Invoke-WebRequest $wheel.url -OutFile $target
  if((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $wheel.digests.sha256){throw 'Wheel hash mismatch'}
}
foreach($version in @('3.8.9','3.13.16')) {
  & ($native+'/runtime/python'+$version+'/python.exe') -m pip install --no-index --find-links $wheels pygame==2.6.1
  if($LASTEXITCODE -ne 0){throw 'Preinstall pygame failed'}
  & ($native+'/runtime/python'+$version+'/python.exe') -X utf8 -c "import tkinter,turtle,pygame; print(pygame.version.ver)"
  if($LASTEXITCODE -ne 0){throw 'Graphical Python modules unavailable'}
}
