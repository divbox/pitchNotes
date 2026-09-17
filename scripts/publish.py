"""Promote the latest built weekly HTML to the local deploy staging area.

Takes the newest-dated file in weeklies/, makes it dist/index.html, and
if a different edition was previously live, moves that one into dist/archive/
under its original filename. Tracks the live edition in manifest.json so this
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


def latest_edition():
    files = glob.glob(os.path.join(WEEKLIES_DIR, "pitch-notes-*.html"))
    dated = []
    for f in files:
        m = re.search(r"pitch-notes-(\d{4}-\d{2}-\d{2})\.html$", f)
        if m:
            dated.append((m.group(1), f))
    if not dated:
        print(f"No dated edition files found in {WEEKLIES_DIR}/", file=sys.stderr)
        sys.exit(1)
    return max(dated)  # ISO dates sort chronologically as strings


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            return json.load(f)
    return {"current_date": None, "current_file": None}


def save_manifest(manifest):
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)


def publish():
    date, src = latest_edition()
    manifest = load_manifest()
    current_date = manifest.get("current_date")

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    index_path = os.path.join(DIST_DIR, "index.html")

    if current_date is not None and current_date != date and os.path.exists(index_path):
        archived_path = os.path.join(ARCHIVE_DIR, manifest["current_file"])
        shutil.copyfile(index_path, archived_path)
        print(f"archived {current_date} -> {archived_path}")

    shutil.copyfile(src, index_path)
    manifest["current_date"] = date
    manifest["current_file"] = os.path.basename(src)
    save_manifest(manifest)
    print(f"published {date} -> {index_path}")


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

        with open(os.path.join(WEEKLIES_DIR, "pitch-notes-2026-09-03.html"), "w") as f:
            f.write("first edition")
        publish()
        assert open(os.path.join(DIST_DIR, "index.html")).read() == "first edition"
        assert not os.listdir(ARCHIVE_DIR), "nothing to archive on first publish"

        with open(os.path.join(WEEKLIES_DIR, "pitch-notes-2026-09-10.html"), "w") as f:
            f.write("second edition")
        publish()
        assert open(os.path.join(DIST_DIR, "index.html")).read() == "second edition"
        assert open(os.path.join(ARCHIVE_DIR, "pitch-notes-2026-09-03.html")).read() == "first edition"
    WEEKLIES_DIR, DIST_DIR, ARCHIVE_DIR, MANIFEST = orig
    print("demo OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        publish()
