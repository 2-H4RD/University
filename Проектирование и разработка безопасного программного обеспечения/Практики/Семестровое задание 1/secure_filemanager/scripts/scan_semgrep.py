"""Run the official native Semgrep engine without its Python service dependencies."""
import argparse
import hashlib
import json

# Only a SHA-256-verified local scanner is executed, using an argument list and no shell.
import subprocess  # nosec B404
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "tools" / "semgrep" / "semgrep-core.exe"


def scan_one(path: Path):
    relative = path.relative_to(ROOT)
    # Fixed trusted executable and argument list; target paths come from this repository.
    result = subprocess.run(
        [str(CORE), "-json_nodots", "-j", "1", "-timeout", "10", "-max_memory", "512",
         "-lang", "python", "-rules", "semgrep.yml", str(relative)],
        cwd=ROOT, capture_output=True, timeout=30, check=False,
    )  # nosec B603
    if result.returncode != 0:
        raise RuntimeError("Native Semgrep failed: " + str(relative))
    data = json.loads(result.stdout.decode("utf-8"))
    if data.get("errors"):
        raise RuntimeError("Semgrep parsing errors: " + str(relative))
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((CORE.parent / "provenance.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        if Path(name).name != name or hashlib.sha256((CORE.parent / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("Native scanner integrity check failed")
    report_dir = ROOT / "reports"
    report_dir.mkdir(exist_ok=True)
    if args.self_test:
        probe = report_dir / "semgrep-selftest.py"
        probe.write_text("value = eval(user_input)\n", encoding="utf-8")
        # This probe is parsed only; it is never executed.
        try:
            result = scan_one(probe)
            if not any(row["check_id"] == "no-python-eval" for row in result["results"]):
                raise RuntimeError("Semgrep self-test failed")
        finally:
            probe.unlink()
    report = {"version": None, "engine": "official semgrep-core", "results": [], "errors": [],
              "paths": {"scanned": []}, "self_test": bool(args.self_test)}
    for section in ("src", "scripts", "migrations"):
        for path in sorted((ROOT / section).rglob("*.py")):
            result = scan_one(path)
            report["version"] = result["version"]
            report["results"].extend(result["results"])
            report["paths"]["scanned"].append(str(path.relative_to(ROOT)))
    (report_dir / "semgrep.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Semgrep {report['version']}: {len(report['paths']['scanned'])} files, "
          f"{len(report['results'])} findings, self-test={args.self_test}")
    return 1 if report["results"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

