param([switch]$Baseline,[string]$NativeRoot=(Join-Path $PSScriptRoot '../native'),[string]$OutputRoot)
$ErrorActionPreference='Stop'
$taskWorkspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskRuntime=Join-Path ([IO.Path]::GetFullPath($NativeRoot)) 'mixly/runtime'
$taskMain=Join-Path $taskRuntime 'resources/app/main.js'
$taskOriginal=[IO.File]::ReadAllBytes($taskMain)
$taskMode=if($Baseline){'baseline'}else{'fixed'}
$taskOutput=if($OutputRoot){[IO.Path]::GetFullPath($OutputRoot)}else{Join-Path $PSScriptRoot $taskMode}
New-Item -ItemType Directory -Path $taskOutput -Force | Out-Null
$taskData=Join-Path $taskOutput 'data'
try {
 Add-Content -LiteralPath $taskMain -Value "`nif(process.env.YUXUAN_MIXLY_SELFTEST)require(process.env.YUXUAN_MIXLY_SELFTEST);" -Encoding utf8
 $env:YUXUAN_MIXLY_SELFTEST=Join-Path $PSScriptRoot 'desktop-regression.cjs'
 $env:YUXUAN_MIXLY_TEST_RESULT=Join-Path $taskOutput 'result.json'
 $env:YUXUAN_MIXLY_BASELINE=if($Baseline){'1'}else{'0'}
 $taskProcess=Start-Process -FilePath (Join-Path $taskRuntime 'Mixly.exe') -ArgumentList ('--data-dir "'+$taskData+'" --suite-token regression-232') -WorkingDirectory $taskRuntime -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskOutput 'stdout.log') -RedirectStandardError (Join-Path $taskOutput 'stderr.log') -PassThru
 $null=$taskProcess.Handle # Keep the native handle open for Windows PowerShell 5 exit-code retrieval.
 if(-not $taskProcess.WaitForExit(180000)){$taskProcess.Kill();throw 'Desktop regression timed out'}
 $taskProcess.WaitForExit()
 if($taskProcess.ExitCode -ne 0){Get-Content -LiteralPath $env:YUXUAN_MIXLY_TEST_RESULT;throw 'Desktop regression failed'}
 Get-Content -LiteralPath $env:YUXUAN_MIXLY_TEST_RESULT
 if(-not $Baseline){
  $env:YUXUAN_MIXLY_RESTART='1';$env:YUXUAN_MIXLY_TEST_RESULT=Join-Path $taskOutput 'restart-result.json'
  $taskProcess=Start-Process -FilePath (Join-Path $taskRuntime 'Mixly.exe') -ArgumentList ('--data-dir "'+$taskData+'" --suite-token regression-232') -WorkingDirectory $taskRuntime -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskOutput 'restart-stdout.log') -RedirectStandardError (Join-Path $taskOutput 'restart-stderr.log') -PassThru
  $null=$taskProcess.Handle # Keep the native handle open for Windows PowerShell 5 exit-code retrieval.
 if(-not $taskProcess.WaitForExit(120000)){$taskProcess.Kill();throw 'Process restart regression timed out'}
  $taskProcess.WaitForExit()
 if($taskProcess.ExitCode -ne 0){Get-Content -LiteralPath $env:YUXUAN_MIXLY_TEST_RESULT;throw 'Process restart regression failed'}
  Get-Content -LiteralPath $env:YUXUAN_MIXLY_TEST_RESULT
 }
} finally {
 [IO.File]::WriteAllBytes($taskMain,$taskOriginal)
 foreach($taskName in @('YUXUAN_MIXLY_SELFTEST','YUXUAN_MIXLY_TEST_RESULT','YUXUAN_MIXLY_BASELINE','YUXUAN_MIXLY_RESTART')){[Environment]::SetEnvironmentVariable($taskName,$null,'Process')}
}
