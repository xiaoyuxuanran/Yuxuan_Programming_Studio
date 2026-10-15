param([string]$FromBoard='', [string]$Node='')
$ErrorActionPreference='Stop'
$workspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$upstream=Join-Path $PSScriptRoot 'upstream'
if(-not $Node){$Node=if(Test-Path -LiteralPath 'D:/nodejs/node.exe'){'D:/nodejs/node.exe'}else{(Get-Command node -ErrorAction Stop).Source}}
$node=$Node
$webpack=Join-Path $upstream 'node_modules/webpack/bin/webpack.js'
$env:PATH=(Split-Path -Parent $node)+';'+$env:PATH
$env:NODE_OPTIONS='--max-old-space-size=6144'
$logs=Join-Path $PSScriptRoot 'build-logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$targets=(Get-Content (Join-Path $upstream 'boards.json') -Raw -Encoding utf8 | ConvertFrom-Json).boardIndex | ForEach-Object {($_ -split '/')[3]} | Select-Object -Unique
$started=($FromBoard -eq '')
foreach($board in $targets){
    if($board -eq $FromBoard){$started=$true}
    if(-not $started){continue}
    Push-Location (Join-Path $upstream ('boards/default_src/'+$board))
    try {
        & $node $webpack --config webpack.prod.js *> (Join-Path $logs ($board+'.log'))
        if($LASTEXITCODE -ne 0){throw ('Board build failed: '+$board)}
        Write-Output ('Built '+$board)
    } finally {Pop-Location}
}
Write-Output 'All hardware and simulator board modules built.'
