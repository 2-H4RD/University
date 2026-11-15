# Native Semgrep

The executable and DLLs are from the official PyPI Windows wheel semgrep 1.185.0.
The upstream LICENSE is preserved alongside them. SHA-256 hashes and origin
are recorded in provenance.json and checked by scripts/scan_semgrep.py.

Only the native local analysis engine is used. The Python wrapper and its
MCP/OpenTelemetry service dependencies are intentionally not installed.
The native engine parses local rules and source files without sending metrics
or source code over the network.

Run from the project root:

```powershell
.\.venv\Scripts\python.exe scripts\scan_semgrep.py --self-test
```

The self-test verifies that an unsafe eval call is detected; the probe is parsed,
never executed. The full result is written to reports/semgrep.json.
