"""Push the local dist/ staging dir to the Linode host over rsync/ssh.

Usage:
  python3 deploy.py --dry-run   # show what would change, touches nothing remote
  python3 deploy.py             # actually push

Reads LINODE_HOST, LINODE_USER, LINODE_PORT, LINODE_WWW_PATH from .env.
"""
import subprocess
import sys


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
    sys.exit(result.returncode)
