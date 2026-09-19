"""Run the full weekly pipeline: build -> publish -> deploy.

Stops at the first failing step. No retries, no fallback behavior — a
failure here means stop and report, not improvise. Logs one line per step
to pitch-notes.log so an unattended run leaves a trace.

Usage: python3 scripts/run_weekly.py (from the project root)
Exit 0 on full success; otherwise exits with the failing step's code.
"""
import datetime
import subprocess
import sys

LOG = "logs/pitch-notes.log"
STEPS = [
    ("build", ["python3", "scripts/build.py"]),
    ("publish", ["python3", "scripts/publish.py"]),
    ("deploy", ["python3", "scripts/deploy.py"]),
]


def log(line):
    with open(LOG, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {line}\n")


def run(steps):
    for name, cmd in steps:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            err = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "unknown error"
            log(f"FAILED at {name}: {err}")
            print(f"Stopped: {name} failed (exit {result.returncode}).", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return result.returncode
        if result.stderr.strip():
            for line in result.stderr.strip().splitlines():
                log(f"WARN {name}: {line}")
        log(f"OK {name}")
    log("SUCCESS full run")
    print("Weekly run complete.")
    return 0


def demo():
    """ponytail: verify the stop-on-first-failure logic without touching real build/publish/deploy or the real log."""
    import tempfile

    global LOG
    orig_log = LOG
    ok = ["python3", "-c", "pass"]
    fail = ["python3", "-c", "import sys; sys.exit(7)"]

    with tempfile.TemporaryDirectory() as tmp:
        LOG = f"{tmp}/test.log"

        code = run([("step_a", ok), ("step_b", ok)])
        assert code == 0, "all-success run should exit 0"

        code = run([("step_a", ok), ("step_b", fail), ("step_c", ok)])
        assert code == 7, "should surface the failing step's exit code"

        with open(LOG) as f:
            lines = f.read().strip().splitlines()
        assert "FAILED at step_b" in lines[-1], "step_c must never run after step_b fails"
    LOG = orig_log
    print("demo OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        sys.exit(run(STEPS))
