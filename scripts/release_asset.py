#!/usr/bin/env python3
"""Preflight a release ZIP; --execute uploads and swaps one asset, keeping a backup.

Default mode is offline. Release text, tags and unrelated assets are not changed.
GitHub has no atomic asset swap; old bytes are retained under a backup name.
"""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib import error, parse, request
import uuid
import zipfile

DEFAULT_REPO = "MVPS680/Cosy-Craft-Launcher"
DEFAULT_RELEASE = 1  # 占位值；--execute 时请显式传入目标 Release ID
DEFAULT_TAG = "v2.99.0.0-r2"
DEFAULT_ZIP = Path(__file__).resolve().parents[1] / "dist/Cosy-Craft-Launcher-2.99.0.0-r2-win.zip"


class ReleaseError(Exception):
    """A failure without credential or API response contents."""


def prepare_package(path):
    # Snapshot first, so a concurrent local build cannot change uploaded bytes.
    payload = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        required = {"Cosy Craft Launcher.exe", "LICENCE", "README.txt"}
        if len(names) != len(set(names)) or not required.issubset(names):
            raise ReleaseError("ZIP must contain one launcher EXE, LICENCE and README.txt at its root.")
        for name in names:
            normalized = name.replace("\\", "/")
            if normalized.startswith("/") or ".." in normalized.split("/") or ":" in normalized:
                raise ReleaseError("ZIP contains an unsafe entry path.")
        if archive.testzip() is not None:
            raise ReleaseError("ZIP failed its CRC integrity check.")
        with archive.open("Cosy Craft Launcher.exe") as executable:
            if executable.read(2) != b"MZ":
                raise ReleaseError("Launcher EXE is not a Windows executable.")
        if any(archive.getinfo(name).file_size == 0 for name in required):
            raise ReleaseError("Required package files must not be empty.")
    return payload, hashlib.sha256(payload).hexdigest()


def get_token():
    for variable in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(variable, "").strip():
            return os.environ[variable].strip()
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
    try:
        result = subprocess.run(
            ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True, timeout=20, env=environment,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ReleaseError("Cannot read GitHub credentials; configure GH_TOKEN or Git credentials.") from None
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if line.startswith("password=") and line[9:].strip():
                return line[9:].strip()
    raise ReleaseError("No GitHub credential available; configure GH_TOKEN or Git credentials.")


class SafeRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if parse.urlsplit(newurl).scheme != "https":
            raise ReleaseError("Refusing a non-HTTPS asset redirect.")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.remove_header("Authorization")
        return redirected


class GitHub:
    def __init__(self, repo, release_id, token):
        self.base = "https://api.github.com/repos/" + repo
        self.upload_base = "https://uploads.github.com/repos/" + repo
        self.release_id = release_id
        self.token = token
        self.opener = request.build_opener(SafeRedirect())

    def open(self, method, url, data=None, accept="application/vnd.github+json", content_type=None):
        req = request.Request(url, data=data, method=method, headers={
            "Accept": accept, "User-Agent": "Cosy-Craft-Launcher-release-tool",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        # Do not forward authentication to the signed CDN download URL.
        req.add_unredirected_header("Authorization", "Bearer " + self.token)
        if content_type:
            req.add_header("Content-Type", content_type)
        try:
            return self.opener.open(req, timeout=120)
        except error.HTTPError as exc:
            status = exc.code
            exc.close()
            raise ReleaseError(f"GitHub {method} failed (HTTP {status}).") from None
        except (error.URLError, OSError, TimeoutError):
            raise ReleaseError(f"GitHub {method} failed; check connectivity before retrying.") from None

    def json(self, method, url, data=None, content_type=None):
        with self.open(method, url, data, content_type=content_type) as response:
            try:
                return json.load(response)
            except (ValueError, UnicodeError):
                raise ReleaseError("GitHub returned an invalid JSON response.") from None

    def release(self):
        return self.json("GET", f"{self.base}/releases/{self.release_id}")

    def assets(self):
        assets, page = [], 1
        while True:
            batch = self.json("GET", f"{self.base}/releases/{self.release_id}/assets?per_page=100&page={page}")
            if not isinstance(batch, list):
                raise ReleaseError("GitHub returned an invalid asset list.")
            assets.extend(batch)
            if len(batch) < 100:
                return assets
            page += 1

    def asset(self, asset_id):
        return self.json("GET", f"{self.base}/releases/assets/{asset_id}")

    def upload(self, name, payload):
        url = f"{self.upload_base}/releases/{self.release_id}/assets?" + parse.urlencode({"name": name})
        return self.json("POST", url, payload, "application/zip")

    def rename(self, asset_id, name):
        return self.json("PATCH", f"{self.base}/releases/assets/{asset_id}",
                         json.dumps({"name": name}).encode("utf-8"), "application/json")

    def download_digest(self, asset_id):
        digest = hashlib.sha256()
        with self.open("GET", f"{self.base}/releases/assets/{asset_id}",
                       accept="application/octet-stream") as response:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


def check_asset(asset, name, size):
    if (not isinstance(asset, dict) or not isinstance(asset.get("id"), int)
            or asset.get("name") != name or asset.get("state") != "uploaded"
            or asset.get("size") != size):
        raise ReleaseError("Remote asset name/state/size does not match the package.")


def rename_checked(api, asset_id, name):
    try:
        renamed = api.rename(asset_id, name)
    except ReleaseError:
        # A lost response can follow a successful PATCH. Query instead of guessing.
        renamed = api.asset(asset_id)
    if renamed.get("id") != asset_id or renamed.get("name") != name:
        raise ReleaseError(f"Could not confirm asset {asset_id} was renamed to {name}.")
    return renamed


def asset_snapshot(assets):
    return sorted((a["id"], a["name"], a["size"], a["state"]) for a in assets)


def replace_asset(api, name, payload, digest, expected_tag, emit=print):
    if api.release().get("tag_name") != expected_tag:
        raise ReleaseError("Release tag does not match --tag; no assets were changed.")
    assets = api.assets()
    matches = [asset for asset in assets if asset["name"] == name]
    if len(matches) > 1:
        raise ReleaseError("Multiple assets have the target name; resolve them before replacing.")
    old = matches[0] if matches else None
    nonce = uuid.uuid4().hex
    pending_name, backup_name = f"pending-{nonce}-{name}", f"backup-{nonce}-{name}"
    emit("Uploading a temporary asset; the existing download is unchanged.")
    staged = api.upload(pending_name, payload)
    check_asset(staged, pending_name, len(payload))
    staged_id = staged["id"]
    if api.download_digest(staged_id) != digest:
        raise ReleaseError(f"Uploaded SHA-256 differs. Old download is unchanged; inspect temporary asset {staged_id}.")
    emit("Temporary asset downloaded and SHA-256 verified.")
    # Ignore counters/timestamps, but detect another publication before switching.
    current = [asset for asset in api.assets() if asset["id"] != staged_id]
    if asset_snapshot(current) != asset_snapshot(assets):
        raise ReleaseError("Asset list changed during upload; old assets retained. Inspect the release before retrying.")
    try:
        if old:
            rename_checked(api, old["id"], backup_name)
            emit(f"Previous package retained as: {backup_name} (asset {old['id']})")
        promoted = rename_checked(api, staged_id, name)
        check_asset(promoted, name, len(payload))
    except (ReleaseError, OSError, ValueError):
        # Never delete either copy. Restore the old name only if it is still free.
        if old:
            try:
                current = api.assets()
                original = next(asset for asset in current if asset["id"] == old["id"])
                if original["name"] == backup_name and not any(asset["name"] == name for asset in current):
                    rename_checked(api, old["id"], name)
                    emit("Previous download name restored.")
                elif original["name"] != name:
                    emit(f"Previous package retained as asset {old['id']}; inspect names before retrying.")
            except (ReleaseError, OSError, ValueError, StopIteration, KeyError):
                emit(f"Recovery unconfirmed. Previous package asset {old['id']} was not deleted.")
        raise
    emit(f"Published asset {staged_id}: {name}")
    emit("Release text and unrelated attachments are unchanged. No assets were deleted.")
    return promoted


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP, help="Local release ZIP")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--release-id", type=int, default=DEFAULT_RELEASE)
    parser.add_argument("--tag", default=DEFAULT_TAG, help="Expected release tag, checked before upload")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true", help="Upload, verify and switch; keep the old package")
    mode.add_argument("--dry-run", action="store_true", help="Offline preflight only (the default)")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo) or args.release_id <= 0:
        parser.error("Invalid repository or release ID")
    try:
        if len(args.zip.name) > 180:
            raise ReleaseError("ZIP filename is too long for temporary/backup asset names.")
        payload, digest = prepare_package(args.zip)
        print(f"Package: {args.zip.resolve()}\nBytes: {len(payload)}\nSHA-256: {digest}")
        print(f"Target: {args.repo}, release {args.release_id}, tag {args.tag}")
        if not args.execute:
            print("DRY RUN OK: no credentials read, no network requests, no GitHub changes.")
            return 0
        api = GitHub(args.repo, args.release_id, get_token())
        replace_asset(api, args.zip.name, payload, digest, args.tag)
        return 0
    except (ReleaseError, OSError, zipfile.BadZipFile, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
