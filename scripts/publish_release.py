"""Publish a new maintenance release only after uploaded assets verify."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlencode
import zipfile

from package_release import ROOT, configuration
from release_asset import GitHub, ReleaseError, check_asset, get_token, prepare_package


def publish(directory, execute=False):
    config = configuration()
    archive = directory / f"Cosy-Craft-Launcher-{config['version']}-win.zip"
    payload, digest = prepare_package(archive)
    checksum = archive.with_suffix(".zip.sha256")
    if checksum.read_text(encoding="ascii").strip() != f"{digest}  {archive.name}":
        raise ReleaseError("Checksum file does not match ZIP")
    with zipfile.ZipFile(archive) as zipped:
        identity = json.loads(zipped.read("BUILD.json"))
        if identity.get("executable_sha256") != hashlib.sha256(zipped.read("Cosy Craft Launcher.exe")).hexdigest():
            raise ReleaseError("Executable identity mismatch")
    commit = identity.get("source_commit", "")
    if (identity.get("tag") != config["tag"] or identity.get("configuration") != "Release"
            or not re.fullmatch(r"[0-9a-f]{40}", commit)):
        raise ReleaseError("Invalid package build identity")
    if os.environ.get("GITHUB_SHA", commit) != commit:
        raise ReleaseError("Package source does not match this workflow commit")
    if not execute:
        print(f"Offline preflight passed: {config['tag']} at {commit}")
        return
    api = GitHub("MVPS680/Cosy-Craft-Launcher", 0, get_token())
    # Do not move a pre-existing tag or publish bytes from a different source revision.
    refs = api.json("GET", api.base + "/git/matching-refs/tags/" + config["tag"])
    for ref in refs:
        if ref["ref"] == "refs/tags/" + config["tag"] and ref["object"]["sha"] != commit:
            raise ReleaseError("Release tag already points to a different object")
    releases, page = [], 1
    while True:
        batch = api.json("GET", f"{api.base}/releases?per_page=100&page={page}")
        releases.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    existing = next((r for r in releases if r["tag_name"] == config["tag"]), None)
    if existing and existing["target_commitish"] != commit:
        raise ReleaseError("Existing release has a different target commit")
    notes = (ROOT / "docs/RELEASE_NOTES.md").read_text(encoding="utf-8-sig")
    notes += f"\n\n构建提交：`{commit}`\n\nZIP SHA-256：`{digest}`\n"
    if existing is None:
        existing = api.json("POST", api.base + "/releases", json.dumps({
            "tag_name": config["tag"], "target_commitish": commit, "name": config["name"],
            "body": notes, "draft": True, "prerelease": False,
        }).encode(), "application/json")
    api.release_id = existing["id"]
    assets = {a["name"]: a for a in api.assets()}
    for path, content, mime in ((archive, payload, "application/zip"), (checksum, checksum.read_bytes(), "text/plain")):
        asset = assets.get(path.name)
        if asset is None:
            if not existing["draft"]:
                raise ReleaseError("Refusing to modify an already-published release")
            asset = api.json("POST", f"{api.upload_base}/releases/{api.release_id}/assets?" + urlencode({"name": path.name}), content, mime)
        check_asset(asset, path.name, len(content))
        if api.download_digest(asset["id"]) != hashlib.sha256(content).hexdigest():
            raise ReleaseError("Uploaded asset verification failed; release stays unpublished")
        print("Verified uploaded asset:", path.name)
    if existing["draft"]:
        existing = api.json("PATCH", f"{api.base}/releases/{api.release_id}", json.dumps({
            "body": notes, "draft": False, "prerelease": False, "make_latest": "true",
        }).encode(), "application/json")
    if existing["draft"] or existing["prerelease"]:
        raise ReleaseError("Release was not published as a stable version")
    print("Published:", existing["html_url"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / "dist")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        publish(args.directory, args.execute)
    except ReleaseError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
