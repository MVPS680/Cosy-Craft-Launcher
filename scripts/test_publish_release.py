import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import publish_release as publisher
from release_asset import ReleaseError

COMMIT = "a" * 40
CONFIG = {"version": "2.99.0.0-r2", "tag": "v2.99.0.0-r2", "name": "Maintenance"}


class FakeApi:
    base = "https://api.github.com/repos/test/repo"
    upload_base = "https://uploads.github.com/repos/test/repo"
    release_id = 0

    def __init__(self):
        self.existing = None
        self.refs = []
        self.stored = []
        self.contents = {}
        self.mutations = []
        self.bad_digest = False

    def json(self, method, url, data=None, content_type=None):
        if method == "GET":
            return self.refs if "matching-refs" in url else ([self.existing] if self.existing else [])
        self.mutations.append((method, url))
        if method == "POST" and "/assets?" in url:
            from urllib.parse import parse_qs, urlsplit
            name = parse_qs(urlsplit(url).query)["name"][0]
            asset = {"id": len(self.stored) + 1, "name": name, "state": "uploaded", "size": len(data)}
            self.stored.append(asset)
            self.contents[asset["id"]] = data
            return asset
        body = json.loads(data)
        if method == "POST":
            self.existing = dict(body, id=1, html_url="https://github.com/test/repo/releases/tag/test")
        else:
            self.existing.update(body)
        return self.existing

    def assets(self):
        return self.stored

    def download_digest(self, asset_id):
        return "bad" if self.bad_digest else hashlib.sha256(self.contents[asset_id]).hexdigest()


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()
        (self.root / "docs/RELEASE_NOTES.md").write_text("Maintenance release", encoding="utf-8")
        self.archive = self.root / "MY-PCL-2.99.0.0-r2-win.zip"
        exe = b"MZ-test-executable"
        with zipfile.ZipFile(self.archive, "w") as zipped:
            for name, data in {"Plain Craft Launcher 2.exe": exe, "LICENCE": b"license", "README.txt": b"readme",
                               "BUILD.json": json.dumps({"tag": CONFIG["tag"], "configuration": "Release",
                                "source_commit": COMMIT, "executable_sha256": hashlib.sha256(exe).hexdigest()}).encode()}.items():
                zipped.writestr(name, data)
        self.checksum = self.archive.with_suffix(".zip.sha256")
        self.checksum.write_text(hashlib.sha256(self.archive.read_bytes()).hexdigest() + "  " + self.archive.name + "\n")
        self.api = FakeApi()
        for target, value in (("ROOT", self.root), ("configuration", lambda: CONFIG),
                              ("GitHub", lambda *args: self.api), ("get_token", lambda: "test-only")):
            handle = patch.object(publisher, target, value)
            handle.start()
            self.addCleanup(handle.stop)
        handle = patch.dict(publisher.os.environ, {"GITHUB_SHA": COMMIT})
        handle.start()
        self.addCleanup(handle.stop)

    def test_offline_preflight_does_not_read_credentials(self):
        with patch.object(publisher, "get_token", side_effect=AssertionError("credential access")):
            publisher.publish(self.root)
        self.assertEqual(self.api.mutations, [])

    def test_checksum_failure_prevents_remote_changes(self):
        self.checksum.write_text("wrong")
        with self.assertRaises(ReleaseError):
            publisher.publish(self.root, True)
        self.assertEqual(self.api.mutations, [])

    def test_success_verifies_both_assets_before_publication(self):
        publisher.publish(self.root, True)
        self.assertEqual(len(self.api.stored), 2)
        self.assertFalse(self.api.existing["draft"])
        self.assertEqual(self.api.mutations[-1][0], "PATCH")

    def test_download_mismatch_keeps_draft(self):
        self.api.bad_digest = True
        with self.assertRaises(ReleaseError):
            publisher.publish(self.root, True)
        self.assertTrue(self.api.existing["draft"])
        self.assertFalse(any(m[0] == "PATCH" for m in self.api.mutations))

    def test_published_matching_release_is_not_rewritten(self):
        publisher.publish(self.root, True)
        self.api.mutations.clear()
        publisher.publish(self.root, True)
        self.assertEqual(self.api.mutations, [])

    def test_missing_published_asset_is_not_added(self):
        self.api.existing = {"id": 1, "target_commitish": COMMIT, "tag_name": CONFIG["tag"], "draft": False}
        with self.assertRaises(ReleaseError):
            publisher.publish(self.root, True)
        self.assertEqual(self.api.mutations, [])

    def test_existing_tag_cannot_be_moved(self):
        self.api.refs = [{"ref": "refs/tags/" + CONFIG["tag"], "object": {"sha": "b" * 40}}]
        with self.assertRaises(ReleaseError):
            publisher.publish(self.root, True)
        self.assertEqual(self.api.mutations, [])

    def test_package_source_must_match_workflow_commit(self):
        with patch.dict(publisher.os.environ, {"GITHUB_SHA": "b" * 40}):
            with self.assertRaises(ReleaseError):
                publisher.publish(self.root, True)
        self.assertEqual(self.api.mutations, [])


if __name__ == "__main__":
    unittest.main()
