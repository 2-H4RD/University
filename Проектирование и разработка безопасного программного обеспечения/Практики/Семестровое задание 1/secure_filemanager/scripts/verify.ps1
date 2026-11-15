$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$python = '.\.venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:SEMGREP_SEND_METRICS = 'off'
New-Item -ItemType Directory -Path 'reports' -Force | Out-Null
function Check-Exit {
    if ($LASTEXITCODE -ne 0) { throw "Check failed (exit $LASTEXITCODE). See reports." }
}
& $python -m pytest --cov=filemanager --cov-report=term-missing --cov-report=xml:reports/coverage.xml --junitxml=reports/tests.xml
Check-Exit
& $python -m ruff check src scripts tests migrations
Check-Exit
& $python -m bandit -r src scripts -c pyproject.toml -f json -o reports/bandit.json
Check-Exit
& $python scripts/scan_semgrep.py --self-test
Check-Exit
& $python -m pip_audit --skip-editable --progress-spinner off --format json --output reports/pip-audit.json
Check-Exit

