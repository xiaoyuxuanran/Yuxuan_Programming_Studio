"""Compile only into this isolated fixture, then exercise the unchanged production entry.

No real licensing files, key, activation code, external endpoint or native payload changes.
The periodic test waits for the production 60-second timer without shortening it.
"""
import datetime
import json
import pathlib
import subprocess
import time
import uuid

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = HERE / ("run-" + uuid.uuid4().hex[:8])
BIN = RUN / "bin"
BIN.mkdir(parents=True)
CSC = pathlib.Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
REFS = ["System.Windows.Forms.dll", "System.Drawing.dll", "System.Web.Extensions.dll", "System.Core.dll"]
SOURCES = [ROOT / "work/SuiteLauncher.cs", ROOT / "work/SuiteLicense.cs"]
FLAGS = subprocess.CREATE_NO_WINDOW


def compile_to(target, sources, main=None):
    cmd = [str(CSC), "/nologo", "/target:exe", "/platform:x64", "/out:" + str(target)]
    cmd += ["/r:" + ref for ref in REFS]
    if main:
        cmd += ["/main:" + main]
    cmd += [str(source) for source in sources]
    result = subprocess.run(cmd, capture_output=True, text=True, creationflags=FLAGS, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr


compile_to(BIN / "AppInventor.exe", SOURCES)
compile_to(BIN / "NetworkFixture.exe", SOURCES + [HERE / "NetworkFixture.cs"], "NetworkFixture")
compile_to(BIN / "AppInventorCore.exe", [HERE / "FakeCore.cs"])
runtime = BIN / "runtime/python3.13.16"
runtime.mkdir(parents=True)
compile_to(runtime / "python.exe", [HERE / "FakeBridge.cs"])
results = []


def run(name, mode, core_mode="wait", fixture=None, expected=4, timeout=25):
    data = RUN / name
    data.mkdir()
    (data / "license-mode").write_text(mode, encoding="utf-8")
    (data / "core-mode").write_text(core_mode, encoding="utf-8")
    args = [str(BIN / ("NetworkFixture.exe" if fixture else "AppInventor.exe")), "--stop" if name == "stop-without-grant" else "--headless", "--no-browser", "--data-dir", str(data)]
    if fixture:
        args.append("--fixture-" + fixture)
    started = time.monotonic()
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=FLAGS)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        (data / "stop.request").write_text("", encoding="utf-8")
        try:
            process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
        raise
    elapsed = time.monotonic() - started
    assert process.returncode == expected, (name, process.returncode, stdout, stderr)
    checks = [json.loads(line) for line in (data / "checks.ndjson").read_text(encoding="utf-8").splitlines()] if (data / "checks.ndjson").exists() else []
    result = {"test": name, "ok": True, "exitCode": process.returncode, "elapsedSeconds": round(elapsed, 3), "checks": checks}
    results.append(result)
    if checks:
        assert (data / "bridge.exited").exists(), "authorization bridge did not gracefully exit"
    return data, checks, result


data, checks, _ = run("first-use-denied", "deny")
assert not (data / "core.started").exists() and len(checks) == 1

data, checks, _ = run("stop-without-grant", "deny", expected=0)
assert (data / "stop.command").exists() and not checks

data, checks, _ = run("natural-core-exit", "valid", core_mode="natural", expected=7)
assert (data / "core.started").exists() and len(checks) == 1

data, checks, _ = run("network-event-revocation", "after-first", fixture="network")
assert len(checks) == 2 and checks[0]["valid"] and not checks[1]["valid"]
assert (data / "core.saved").exists() and (data / "resources.cleaned").exists()

data, checks, _ = run("pre-spawn-revocation-race", "valid", fixture="race")
assert len(checks) == 2 and not (data / "core.started").exists()
assert (data / "resources.cleaned").exists()

data, checks, _ = run("startup-cleanup-revocation-race", "after-first", core_mode="startup-clear", fixture="network")
assert (data / "core.discarded-startup-stop").exists(), "fixture must remove the first request"
assert (data / "core.saved").exists() and (data / "resources.cleaned").exists()

print("Six isolated entry, cleanup and race checks passed; waiting for production 60-second timer.", flush=True)
data, checks, result = run("periodic-revocation", "after-first", timeout=85)
assert len(checks) == 2 and checks[0]["valid"] and not checks[1]["valid"]
assert (data / "core.saved").exists(), "revoked Core must complete its graceful-save handshake"
interval = (datetime.datetime.fromisoformat(checks[1]["time"]) - datetime.datetime.fromisoformat(checks[0]["time"])).total_seconds()
assert 57 <= interval <= 80, interval
result["periodSeconds"] = round(interval, 3)
report = {"ok": True, "fixtureOnly": True, "productionTimerMs": 60000, "runDirectory": str(RUN), "tests": results}
(HERE / "acceptance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False), flush=True)
