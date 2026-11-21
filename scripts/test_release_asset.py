"""Offline failure-injection tests. Never use GitHub credentials or the network."""

from copy import deepcopy
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib import request
import zipfile

import release_asset as tool


NAME = "Cosy-Craft-Launcher-2.99.0.0-r2-win.zip"
PAYLOAD = b"new package"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


class FakeGitHub:
    def __init__(self, failure=None):
        self.records = {
            1: dict(id=1, name=NAME, state="uploaded", size=3, content=b"old"),
            2: dict(id=2, name="other.txt", state="uploaded", size=4, content=b"keep"),
        }
        self.failure = failure
        self.events = []

    def release(self):
        return {"tag_name": "wrong" if self.failure == "tag" else tool.DEFAULT_TAG}

    def assets(self):
        if self.failure == "recovery" and any(e[0] == "rename" for e in self.events):
            raise tool.ReleaseError("offline")
        return deepcopy(list(self.records.values()))

    def asset(self, asset_id):
        return deepcopy(self.records[asset_id])

    def upload(self, name, payload):
        self.events.append(("upload", name))
        if self.failure == "upload":
            raise tool.ReleaseError("upload failed")
        self.records[3] = dict(id=3, name=name, state="uploaded", size=len(payload), content=payload)
        if self.failure == "size":
            self.records[3]["size"] += 1
        return self.asset(3)

    def download_digest(self, asset_id):
        self.events.append(("verify", asset_id))
        if self.failure == "concurrent":
            self.records[2]["name"] = "changed-by-another-publisher.txt"
        if self.failure == "digest":
            return "bad digest"
        return hashlib.sha256(self.records[asset_id]["content"]).hexdigest()

    def rename(self, asset_id, name):
        self.events.append(("rename", asset_id, name))
        if self.failure == "backup" and asset_id == 1 and name.startswith("backup-"):
            raise tool.ReleaseError("backup failed")
        if self.failure in ("promote", "recovery") and asset_id == 3:
            raise tool.ReleaseError("promotion failed")
        if any(a["name"] == name and a["id"] != asset_id for a in self.records.values()):
            raise tool.ReleaseError("name collision")
        self.records[asset_id]["name"] = name
        if self.failure == "lost-response":
            raise tool.ReleaseError("response lost after successful PATCH")
        return self.asset(asset_id)


class ReplacementTests(unittest.TestCase):
    def replace(self, api):
        return tool.replace_asset(api, NAME, PAYLOAD, DIGEST, tool.DEFAULT_TAG, emit=lambda _: None)

    def test_success_verifies_before_switch_and_retains_all_old_bytes(self):
        api = FakeGitHub()
        other = api.asset(2)
        result = self.replace(api)
        self.assertEqual(result["id"], 3)
        self.assertEqual(result["name"], NAME)
        self.assertTrue(api.records[1]["name"].startswith("backup-"))
        self.assertEqual(api.records[1]["content"], b"old")
        self.assertEqual(api.asset(2), other)
        self.assertEqual([e[0] for e in api.events], ["upload", "verify", "rename", "rename"])

    def test_upload_failure_preserves_original_and_unrelated_asset(self):
        api = FakeGitHub("upload")
        before = api.assets()
        with self.assertRaises(tool.ReleaseError):
            self.replace(api)
        self.assertEqual(api.assets(), before)

    def test_bad_digest_or_metadata_never_renames_the_original(self):
        for failure in ("digest", "size"):
            with self.subTest(failure=failure):
                api = FakeGitHub(failure)
                with self.assertRaises(tool.ReleaseError):
                    self.replace(api)
                self.assertEqual(api.records[1]["name"], NAME)
                self.assertFalse(any(e[0] == "rename" for e in api.events))

    def test_backup_failure_preserves_original_name(self):
        api = FakeGitHub("backup")
        with self.assertRaises(tool.ReleaseError):
            self.replace(api)
        self.assertEqual(api.records[1]["name"], NAME)

    def test_promotion_failure_restores_original_name(self):
        api = FakeGitHub("promote")
        with self.assertRaises(tool.ReleaseError):
            self.replace(api)
        self.assertEqual(api.records[1]["name"], NAME)
        self.assertEqual(api.records[1]["content"], b"old")
        self.assertTrue(api.records[3]["name"].startswith("pending-"))

    def test_lost_patch_responses_are_confirmed_without_false_rollback(self):
        api = FakeGitHub("lost-response")
        self.replace(api)
        self.assertEqual(api.records[3]["name"], NAME)
        self.assertTrue(api.records[1]["name"].startswith("backup-"))

    def test_unreachable_recovery_keeps_both_packages(self):
        api = FakeGitHub("recovery")
        with self.assertRaises(tool.ReleaseError):
            self.replace(api)
        self.assertEqual(api.records[1]["content"], b"old")
        self.assertEqual(api.records[3]["content"], PAYLOAD)

    def test_wrong_release_tag_stops_before_upload(self):
        api = FakeGitHub("tag")
        with self.assertRaises(tool.ReleaseError):
            self.replace(api)
        self.assertEqual(api.events, [])

    def test_concurrent_asset_change_stops_before_switch(self):
        api = FakeGitHub("concurrent")
        with self.assertRaises(tool.ReleaseError):
            self.replace(api)
        self.assertEqual(api.records[1]["name"], NAME)
        self.assertFalse(any(e[0] == "rename" for e in api.events))

    def test_first_upload_with_no_previous_target(self):
        api = FakeGitHub()
        del api.records[1]
        self.replace(api)
        self.assertEqual(api.records[3]["name"], NAME)
        self.assertEqual(api.records[2]["content"], b"keep")


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.package = Path(self.directory.name) / NAME

    def make_zip(self, extra=None, executable=b"MZtest"):
        with zipfile.ZipFile(self.package, "w") as archive:
            archive.writestr("Cosy Craft Launcher.exe", executable)
            archive.writestr("LICENCE", "license")
            archive.writestr("README.txt", "instructions")
            if extra:
                archive.writestr(extra, "extra")

    def test_default_dry_run_never_reads_credentials_or_opens_network(self):
        self.make_zip()
        with patch.object(tool, "get_token", side_effect=AssertionError("credential access")), \
                patch.object(tool, "GitHub", side_effect=AssertionError("network access")), \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(tool.main(["--zip", str(self.package)]), 0)
            self.assertIn("DRY RUN OK", output.getvalue())

    def test_bad_zip_stops_before_credentials_even_in_execute_mode(self):
        self.package.write_bytes(b"not a ZIP")
        with patch.object(tool, "get_token", side_effect=AssertionError("credential access")), \
                patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(tool.main(["--zip", str(self.package), "--execute"]), 1)

    def test_package_snapshot_and_digest_match_exact_bytes(self):
        self.make_zip()
        payload, digest = tool.prepare_package(self.package)
        self.package.write_bytes(b"changed during publication")
        self.assertTrue(payload.startswith(b"PK"))
        self.assertEqual(digest, hashlib.sha256(payload).hexdigest())

    def test_zip_rejects_traversal_and_non_executable(self):
        for extra, executable in (("../secret", b"MZtest"), ("C:/bad", b"MZtest"),
                                  (None, b"not an EXE")):
            with self.subTest(extra=extra, executable=executable):
                self.make_zip(extra, executable)
                with self.assertRaises(tool.ReleaseError):
                    tool.prepare_package(self.package)

    def test_missing_required_file_or_empty_executable_is_rejected(self):
        with zipfile.ZipFile(self.package, "w") as archive:
            archive.writestr("Cosy Craft Launcher.exe", b"MZtest")
        with self.assertRaises(tool.ReleaseError):
            tool.prepare_package(self.package)
        self.make_zip(executable=b"")
        with self.assertRaises(tool.ReleaseError):
            tool.prepare_package(self.package)

    def test_duplicate_executable_is_rejected(self):
        self.make_zip()
        with self.assertWarns(UserWarning), zipfile.ZipFile(self.package, "a") as archive:
            archive.writestr("Cosy Craft Launcher.exe", b"MZduplicate")
        with self.assertRaises(tool.ReleaseError):
            tool.prepare_package(self.package)

    def test_corrupted_zip_member_is_rejected(self):
        self.make_zip()
        payload = self.package.read_bytes()
        self.package.write_bytes(payload.replace(b"MZtest", b"MZfail", 1))
        with self.assertRaises(tool.ReleaseError):
            tool.prepare_package(self.package)

    def test_asset_download_redirect_does_not_forward_token(self):
        req = request.Request("https://api.github.com/repos/example/repo/releases/assets/1")
        req.add_unredirected_header("Authorization", "Bearer test-only")
        redirected = tool.SafeRedirect().redirect_request(
            req, None, 302, "Found", {}, "https://release-assets.githubusercontent.com/file")
        self.assertFalse(redirected.has_header("Authorization"))
        with self.assertRaises(tool.ReleaseError):
            tool.SafeRedirect().redirect_request(req, None, 302, "Found", {}, "http://example.com/file")

    def test_asset_pagination_reads_beyond_first_page(self):
        api = tool.GitHub("example/repo", 1, "test-only")
        with patch.object(api, "json", side_effect=[[{"id": i} for i in range(100)], [{"id": 100}]]) as call:
            self.assertEqual(len(api.assets()), 101)
            self.assertIn("page=2", call.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
