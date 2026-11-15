param([switch]$Check, [switch]$CreateAdmin)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Environment missing. Follow README.md to create .venv and install dependencies.'
}
$env:PYTHONUTF8 = '1'
$arguments = @('-m', 'filemanager')
if ($Check) { $arguments += '--check' }
if ($CreateAdmin) { $arguments += '--create-admin' }
& $python @arguments
exit $LASTEXITCODE

