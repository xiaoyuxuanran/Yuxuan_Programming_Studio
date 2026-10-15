$ErrorActionPreference='Stop'
$downloads=Join-Path $PSScriptRoot 'downloads'
$runtime=Join-Path $PSScriptRoot '../native/runtime'
foreach($v in @('3.8.9','3.13.16')) {
  $file=Join-Path $downloads "python-$v.nupkg"
  if(-not (Test-Path $file)){Invoke-WebRequest "https://api.nuget.org/v3-flatcontainer/python/$v/python.$v.nupkg" -OutFile $file}
  $unpack=Join-Path $downloads "python-$v"
  if(-not (Test-Path "$unpack/tools/python.exe")){Expand-Archive $file $unpack -Force}
  $target=Join-Path $runtime "python$v"
  if(-not (Test-Path "$target/python.exe")){Copy-Item "$unpack/tools" $target -Recurse}
  & "$target/python.exe" --version
  & "$target/python.exe" -m pip --version
}
$llvm='llvm-mingw-20260922-ucrt-x86_64'
$zip=Join-Path $downloads "$llvm.zip"
if(-not (Test-Path $zip)){Invoke-WebRequest "https://github.com/mstorsjo/llvm-mingw/releases/download/20260922/$llvm.zip" -OutFile $zip}
if((Get-FileHash $zip).Hash.ToLower() -ne 'e3ad77d117a4bea19a7a3b333341824d79a5a371004a10e25b8504e7b3047666'){throw 'LLVM package SHA256 mismatch'}
if(-not (Test-Path "$runtime/llvm-mingw/bin/clang++.exe")) {
  Expand-Archive $zip "$downloads/llvm" -Force
  Move-Item -LiteralPath "$downloads/llvm/$llvm" -Destination "$runtime/llvm-mingw"
}
$metadata=Invoke-RestMethod 'https://registry.npmjs.org/monaco-editor/latest'
$metadata | ConvertTo-Json -Depth 8 | Set-Content "$downloads/monaco.json" -Encoding utf8
$tgz=Join-Path $downloads 'monaco.tgz'
Invoke-WebRequest $metadata.dist.tarball -OutFile $tgz
$sha=[Security.Cryptography.SHA512]::Create()
$expected='sha512-'+[Convert]::ToBase64String($sha.ComputeHash([IO.File]::ReadAllBytes($tgz)))
if($expected -ne $metadata.dist.integrity){throw 'Monaco npm integrity mismatch'}
New-Item -ItemType Directory -Force "$downloads/monaco" | Out-Null
tar -xzf $tgz -C "$downloads/monaco"
Copy-Item "$downloads/monaco/package/min/vs" "$PSScriptRoot/../native/studio/vs" -Recurse -Force
Copy-Item "$downloads/monaco/package/LICENSE" "$PSScriptRoot/../native/studio/Monaco-LICENSE.txt" -Force
Get-FileHash "$downloads/*.nupkg",$zip,$tgz | Select-Object Path,Hash | ConvertTo-Json | Set-Content "$downloads/tool-hashes.json" -Encoding utf8
'Runtime download and verification complete.'
