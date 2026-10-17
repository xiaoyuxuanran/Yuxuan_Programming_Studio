param([string]$NativeRoot=(Join-Path $PSScriptRoot '../native'),[string]$DataRoot=(Join-Path $PSScriptRoot 'smoke/data'),[string]$OutputRoot=(Join-Path $PSScriptRoot 'smoke'),[string]$OnlyBoard)
$ErrorActionPreference='Stop'
$taskNative=[IO.Path]::GetFullPath($NativeRoot);$taskData=[IO.Path]::GetFullPath($DataRoot);$taskOutput=[IO.Path]::GetFullPath($OutputRoot)
New-Item -ItemType Directory -Path $taskOutput -Force | Out-Null
$taskRuntime=Join-Path $taskNative 'mixly/runtime';$taskMain=Join-Path $taskRuntime 'resources/app/main.js';$taskOriginal=[IO.File]::ReadAllBytes($taskMain)
try {
 Add-Content -LiteralPath $taskMain -Value "`nif(process.env.YUXUAN_MIXLY_SELFTEST)require(process.env.YUXUAN_MIXLY_SELFTEST);" -Encoding utf8
 $env:YUXUAN_MIXLY_SELFTEST=Join-Path $PSScriptRoot 'desktop-smoke.cjs';$env:YUXUAN_MIXLY_TEST_RESULT=Join-Path $taskOutput 'desktop-smoke.json'
 $env:YUXUAN_MIXLY_ONLY_BOARD=$OnlyBoard
 $taskProc=Start-Process -FilePath (Join-Path $taskRuntime 'Mixly.exe') -ArgumentList ('--data-dir "'+$taskData+'" --suite-token smoke-232') -WorkingDirectory $taskRuntime -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskOutput 'stdout.log') -RedirectStandardError (Join-Path $taskOutput 'stderr.log') -PassThru
 $null=$taskProc.Handle # Keep the native handle open for Windows PowerShell 5 exit-code retrieval.
 if(-not $taskProc.WaitForExit(900000)){$taskProc.Kill();throw 'Desktop smoke timed out'}
 $taskProc.WaitForExit()
 if($taskProc.ExitCode -ne 0){Get-Content -LiteralPath $env:YUXUAN_MIXLY_TEST_RESULT;throw ('Desktop smoke failed; process exit='+[string]$taskProc.ExitCode)}
 Get-Content -LiteralPath $env:YUXUAN_MIXLY_TEST_RESULT
} finally {
 [IO.File]::WriteAllBytes($taskMain,$taskOriginal)
 foreach($taskName in @('YUXUAN_MIXLY_SELFTEST','YUXUAN_MIXLY_TEST_RESULT','YUXUAN_MIXLY_ONLY_BOARD')){[Environment]::SetEnvironmentVariable($taskName,$null,'Process')}
}
