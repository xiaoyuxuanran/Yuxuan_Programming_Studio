param([Parameter(Mandatory=$true)][string]$DataRoot,[Parameter(Mandatory=$true)][string]$TargetPath,[string]$AliasName='esp32sdk')
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath($DataRoot)
$target=[IO.Path]::GetFullPath($TargetPath)
if($AliasName -notmatch '^[A-Za-z0-9_-]{1,40}$'){throw 'Invalid SDK alias name'}
$alias=[IO.Path]::GetFullPath((Join-Path $root $AliasName))
if([IO.Path]::GetDirectoryName($alias) -ne $root){throw 'SDK alias outside data root'}
if(Test-Path -LiteralPath $alias){
  $item=Get-Item -LiteralPath $alias -Force
  if(!($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'SDK alias already exists as a normal directory'}
  if([IO.Path]::GetFullPath([string]$item.Target) -eq $target){exit 0}
  # Delete the junction itself, without traversing or deleting its target.
  [IO.Directory]::Delete($alias,$false)
}
New-Item -ItemType Junction -Path $alias -Target $target | Out-Null
