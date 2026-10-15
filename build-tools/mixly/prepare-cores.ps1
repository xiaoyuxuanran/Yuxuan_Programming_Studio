$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$toolDir = Join-Path $workspace 'work/native/mixly/arduino-cli'
$downloadDir = Join-Path $PSScriptRoot 'downloads'
Invoke-WebRequest 'https://github.com/arduino/arduino-cli/releases/download/v0.35.3/0.35.3-checksums.txt' -OutFile (Join-Path $downloadDir 'arduino-cli-checksums.txt')
$archive = Join-Path $downloadDir 'arduino-cli.zip'
$hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
$line = (Select-String -LiteralPath (Join-Path $downloadDir 'arduino-cli-checksums.txt') -Pattern 'arduino-cli_0.35.3_Windows_64bit.zip').Line
if (!$line.StartsWith($hash)) { throw 'Arduino CLI checksum mismatch' }
Expand-Archive -LiteralPath $archive -DestinationPath $toolDir -Force
'PASS Arduino CLI official SHA256 ' + $hash
$configPath = Join-Path $toolDir 'arduino-cli.json'
@{
    board_manager = @{additional_urls = @('https://arduino.esp8266.com/stable/package_esp8266com_index.json', 'https://espressif.github.io/arduino-esp32/package_esp32_index.json')}
    directories = @{data = (Join-Path $toolDir 'Arduino15'); downloads = (Join-Path $downloadDir 'staging'); user = (Join-Path $toolDir 'Arduino')}
    metrics = @{enabled = $false}
    network = @{connection_timeout = '300s'}
    updater = @{enable_notification = $false}
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $configPath -Encoding utf8NoBOM
$cli = Join-Path $toolDir 'arduino-cli.exe'
& $cli core update-index --config-file $configPath --no-color
if ($LASTEXITCODE -ne 0) { throw 'Arduino indexes failed' }
foreach ($core in @('arduino:avr@1.8.6', 'esp8266:esp8266@3.1.2', 'esp32:esp32@2.0.17')) {
    & $cli core install $core --config-file $configPath --no-color
    if ($LASTEXITCODE -ne 0) { throw ('Core installation failed: ' + $core) }
}
& $cli core list --config-file $configPath --no-color
if ($LASTEXITCODE -ne 0) { throw 'Core list failed' }
exit 0
