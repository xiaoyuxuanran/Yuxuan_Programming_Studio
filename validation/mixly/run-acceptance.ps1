param([string]$NativeRoot,[string]$DataRoot,[string]$OutputRoot)
$ErrorActionPreference='Stop'
$runtime=Join-Path $NativeRoot 'mixly/runtime'
$main=Join-Path $runtime 'resources/app/main.js'
$originalMain=[IO.File]::ReadAllBytes($main)
$testProcess=$null
try {
 Add-Content -LiteralPath $main -Value "`nif(process.env.YUXUAN_MIXLY_SELFTEST) require(process.env.YUXUAN_MIXLY_SELFTEST);" -Encoding utf8
 $env:YUXUAN_MIXLY_SELFTEST=Join-Path $PSScriptRoot 'integration-test.js'
 $env:YUXUAN_MIXLY_TEST_RESULT=Join-Path $OutputRoot 'result.json'
 $testProcess=Start-Process -FilePath (Join-Path $runtime 'Mixly.exe') -ArgumentList @('--data-dir',('"'+$DataRoot+'"'),'--suite-token','mixly-functional-test-token') -WorkingDirectory $runtime -WindowStyle Hidden -RedirectStandardOutput (Join-Path $OutputRoot 'stdout.log') -RedirectStandardError (Join-Path $OutputRoot 'stderr.log') -PassThru
 if(-not $testProcess.WaitForExit(600000)){ $testProcess.Kill();throw 'Functional test timed out' }
 if($testProcess.ExitCode -ne 0){throw ('Functional test failed: '+$testProcess.ExitCode)}
} finally {
 [IO.File]::WriteAllBytes($main,$originalMain)
 Remove-Item Env:YUXUAN_MIXLY_SELFTEST,Env:YUXUAN_MIXLY_TEST_RESULT -ErrorAction SilentlyContinue
 if($testProcess){$testProcess.Dispose()}
}
$report=Get-Content (Join-Path $OutputRoot 'result.json') -Raw | ConvertFrom-Json
$report.results | Select-Object name,ok
$fatal=@($report.errors | Where-Object {$_.message -notlike '*was deprecated*'})
if($fatal.Count){throw 'Renderer error detected'}
