"""Push the local dist/ staging dir to the Linode host over rsync/ssh.

Usage:
  python3 deploy.py --dry-run   # show what would change, touches nothing remote
  python3 deploy.py             # actually push

Reads LINODE_HOST, LINODE_USER, LINODE_PORT, LINODE_WWW_PATH from .env.

This is the only step that touches the live site, so it is deliberately not
part of run_pipeline.py. Logs its outcome to the same file that script uses,
so the log still shows the whole story of a run.
"""
import datetime
import subprocess
import sys

LOG = "logs/pitch-notes.log"


def log(line):
    with open(LOG, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {line}\n")


def load_env(path=".env"):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key] = value.strip('"')
    return env


def build_command(env, dry_run):
    ssh = f"ssh -p {env['LINODE_PORT']}"
    dest = f"{env['LINODE_USER']}@{env['LINODE_HOST']}:{env['LINODE_WWW_PATH']}/"
    # The remote dirs are owned by www-data, not divbox, so divbox can't set
    # their permissions/ownership/times -- skip syncing all of that (-a would
    # try and exit nonzero). We only care that file content matches.
    cmd = ["rsync", "-rlvz", "-e", ssh, "dist/", dest]
    if dry_run:
        cmd.insert(1, "--dry-run")
    return cmd


if __name__ == "__main__":
    env = load_env()
    dry_run = "--dry-run" in sys.argv
    cmd = build_command(env, dry_run)
    print("running:", " ".join(cmd))
    result = subprocess.run(cmd)
    what = "deploy --dry-run" if dry_run else "deploy"
    log(f"OK {what}" if result.returncode == 0 else f"FAILED at {what}: exit {result.returncode}")
    sys.exit(result.returncode)
