"""Promote the latest built weekly HTML to the local deploy staging area.

Takes the highest-numbered file in weeklies/, makes it dist/index.html, and
if a different week was previously live, moves that one into dist/archive/
under its original filename. Tracks the live week in manifest.json so this
never has to guess or reparse old content.

Usage: python3 publish.py
"""
import glob
import json
import os
import re
import shutil
import sys

WEEKLIES_DIR = "weeklies"
DIST_DIR = "dist"
ARCHIVE_DIR = os.path.join(DIST_DIR, "archive")
MANIFEST = "manifest.json"


def latest_week():
    files = glob.glob(os.path.join(WEEKLIES_DIR, "pitch-notes-W*.html"))
    if not files:
        print(f"No weekly files found in {WEEKLIES_DIR}/", file=sys.stderr)
        sys.exit(1)
    weeks = [(int(re.search(r"W(\d+)", f).group(1)), f) for f in files]
    return max(weeks)


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            return json.load(f)
    return {"current_week": None, "current_file": None}


def save_manifest(manifest):
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)


def publish():
    week, src = latest_week()
    manifest = load_manifest()
    current_week = manifest["current_week"]

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    index_path = os.path.join(DIST_DIR, "index.html")

    if current_week is not None and current_week != week and os.path.exists(index_path):
        archived_path = os.path.join(ARCHIVE_DIR, manifest["current_file"])
        shutil.copyfile(index_path, archived_path)
        print(f"archived week {current_week} -> {archived_path}")

    shutil.copyfile(src, index_path)
    manifest["current_week"] = week
    manifest["current_file"] = os.path.basename(src)
    save_manifest(manifest)
    print(f"published week {week} -> {index_path}")


def demo():
    """ponytail: self-check the rotation logic against a scratch dir, not the real dist/."""
    import tempfile

    global WEEKLIES_DIR, DIST_DIR, ARCHIVE_DIR, MANIFEST
    orig = (WEEKLIES_DIR, DIST_DIR, ARCHIVE_DIR, MANIFEST)
    with tempfile.TemporaryDirectory() as tmp:
        WEEKLIES_DIR = os.path.join(tmp, "weeklies")
        DIST_DIR = os.path.join(tmp, "dist")
        ARCHIVE_DIR = os.path.join(DIST_DIR, "archive")
        MANIFEST = os.path.join(tmp, "manifest.json")
        os.makedirs(WEEKLIES_DIR)

        with open(os.path.join(WEEKLIES_DIR, "pitch-notes-W3.html"), "w") as f:
            f.write("week 3 content")
        publish()
        assert open(os.path.join(DIST_DIR, "index.html")).read() == "week 3 content"
        assert not os.listdir(ARCHIVE_DIR), "nothing to archive on first publish"

        with open(os.path.join(WEEKLIES_DIR, "pitch-notes-W4.html"), "w") as f:
            f.write("week 4 content")
        publish()
        assert open(os.path.join(DIST_DIR, "index.html")).read() == "week 4 content"
        assert open(os.path.join(ARCHIVE_DIR, "pitch-notes-W3.html")).read() == "week 3 content"
    WEEKLIES_DIR, DIST_DIR, ARCHIVE_DIR, MANIFEST = orig
    print("demo OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        publish()
