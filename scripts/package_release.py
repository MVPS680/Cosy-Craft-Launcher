"""Create an offline, traceable Release ZIP and its SHA-256 file."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def configuration():
    config = json.loads((ROOT / "release.json").read_text(encoding="utf-8-sig"))
    if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+-r[1-9]\d*", config["version"]):
        raise ValueError("Invalid maintenance version")
    if config["tag"] != "v" + config["version"]:
        raise ValueError("Tag/version mismatch")
    return config


def package(build_dir, output_dir):
    config = configuration()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Commit tracked source changes before packaging")
    files = {}
    for name in ("Plain Craft Launcher 2.exe", "Plain Craft Launcher 2.exe.config"):
        files[name] = (build_dir / name).read_bytes()
        if not files[name]:
            raise ValueError("Empty build output")
    if not files["Plain Craft Launcher 2.exe"].startswith(b"MZ"):
        raise ValueError("Expected a Windows executable")
    files["LICENCE"] = (ROOT / "LICENCE").read_bytes()
    info = {
        "project": "FLandreyu/MY-PCL", "version": config["version"],
        "tag": config["tag"], "source_commit": commit, "configuration": "Release",
        "executable_sha256": hashlib.sha256(files["Plain Craft Launcher 2.exe"]).hexdigest(),
    }
    files["BUILD.json"] = (json.dumps(info, indent=2) + "\n").encode()
    files["README.txt"] = (
        f"Plain Craft Launcher (PCL) - MY-PCL {config['version']}\n"
        f"Source: https://github.com/FLandreyu/MY-PCL/tree/{commit}\n"
        "Unofficial community-maintained distribution. Configuration: Release.\n\n"
        "Extract all files into a writable folder and run Plain Craft Launcher 2.exe.\n"
        "Keep the .exe.config alongside the executable. Back up saves before updating.\n"
        "Requires Windows, .NET Framework 4.8 and Java suitable for the game version.\n\n"
        "Microsoft login requires your approved PCL_MS_CLIENT_ID.\n"
        "CurseForge services require your PCL_CURSEFORGE_API_KEY. Neither is bundled.\n"
        "Modrinth search needs no user-provided key. Updates are manual.\n"
        "The executable is unsigned. Full account/download/game-launch testing is not claimed.\n\n"
        "Instructions: https://github.com/FLandreyu/MY-PCL#readme\n"
        "License: LICENCE. Build identity: BUILD.json.\n"
    ).encode()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"MY-PCL-{config['version']}-win.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            entry = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, content)
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    archive_path.with_suffix(".zip.sha256").write_text(f"{digest}  {archive_path.name}\n", encoding="ascii")
    print(f"Package: {archive_path.name}\nSource: {commit}\nSHA-256: {digest}")
    return archive_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    package(args.build_dir, args.output_dir)
