"""Create an offline, traceable Release ZIP and its SHA-256 file."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXE_NAME = "Cosy Craft Launcher.exe"
PROJECT = "MVPS680/Cosy-Craft-Launcher"


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
    for name in (EXE_NAME, EXE_NAME + ".config"):
        files[name] = (build_dir / name).read_bytes()
        if not files[name]:
            raise ValueError("Empty build output")
    if not files[EXE_NAME].startswith(b"MZ"):
        raise ValueError("Expected a Windows executable")
    files["LICENCE"] = (ROOT / "LICENCE").read_bytes()
    info = {
        "project": PROJECT, "name": "Cosy Craft Launcher", "author": "MVPClub (https://mvpclub.cc)",
        "version": config["version"], "tag": config["tag"], "source_commit": commit,
        "configuration": "Release",
        "executable_sha256": hashlib.sha256(files[EXE_NAME]).hexdigest(),
    }
    files["BUILD.json"] = (json.dumps(info, indent=2) + "\n").encode()
    files["README.txt"] = (
        f"Cosy Craft Launcher {config['version']}\n"
        f"Author: MVPClub (https://mvpclub.cc)\n"
        f"Source: https://github.com/{PROJECT}/tree/{commit}\n"
        "Unofficial third-party distribution based on the public PCL 2.99.0.0 source.\n"
        "Configuration: Release.\n\n"
        f"Extract all files into a writable folder and run {EXE_NAME}.\n"
        "Keep the .exe.config alongside the executable. Back up saves before updating.\n"
        "Requires Windows, .NET Framework 4.8 and Java suitable for the game version.\n\n"
        "Microsoft login requires your approved COSY_MS_CLIENT_ID\n"
        "(legacy PCL_MS_CLIENT_ID is also accepted).\n"
        "CurseForge services require your COSY_CURSEFORGE_API_KEY\n"
        "(legacy PCL_CURSEFORGE_API_KEY is also accepted). Neither is bundled.\n"
        "Modrinth search needs no user-provided key. Updates are manual.\n"
        "The executable is unsigned. Full account/download/game-launch testing is not claimed.\n\n"
        f"Instructions: https://github.com/{PROJECT}#readme\n"
        "License: LICENCE. Build identity: BUILD.json.\n"
    ).encode()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"Cosy-Craft-Launcher-{config['version']}-win.zip"
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
