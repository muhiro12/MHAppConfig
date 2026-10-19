"""Exercise exact-Git-object checks without publishing configuration."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


VALIDATOR = str(Path(sys.argv.pop(1)).resolve())
VERIFIER = Path(__file__).with_name("verify.py")


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.git("init", "--quiet")
        self.git("config", "user.name", "Validation Test")
        self.git("config", "user.email", "validation@example.invalid")
        self.policy = {
            "schemaVersion": 1,
            "bundleIdentifier": "example.app",
            "features": {"remoteUpdate": {"revision": 2, "requirement": None}},
        }
        self.write(self.policy)
        self.base = self.save()

    def git(self, *arguments):
        return subprocess.check_output(["git", *arguments], cwd=self.root).decode().strip()

    def write(self, document):
        path = self.root / "example/app.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(document))

    def save(self):
        self.git("add", "--all")
        self.git("commit", "--quiet", "--allow-empty", "-m", "Record test configuration")
        return self.git("rev-parse", "HEAD")

    def verify(self, candidate=None, base=None):
        arguments = [sys.executable, str(VERIFIER), "--validator", VALIDATOR, "--base", base or self.base]
        if candidate:
            arguments += ["--candidate", candidate]
        return subprocess.run(arguments, cwd=self.root, capture_output=True, text=True, check=False)

    def test_unchanged_policy_and_sibling_edits_are_accepted(self):
        self.policy["features"]["futureFeature"] = {"value": 1}
        self.write(self.policy)
        self.assertEqual(self.verify(self.save()).returncode, 0)

    def test_exact_commit_is_checked_instead_of_uncommitted_repairs(self):
        self.policy["features"]["remoteUpdate"]["revision"] = 1
        self.write(self.policy)
        invalid = self.save()
        self.policy["features"]["remoteUpdate"]["revision"] = 3
        self.write(self.policy)
        self.assertNotEqual(self.verify(invalid).returncode, 0)
        self.assertEqual(self.verify().returncode, 0)

    def test_immutable_revision_and_changed_identity_are_rejected(self):
        candidate = copy.deepcopy(self.policy)
        candidate["bundleIdentifier"] = "other.app"
        self.write(candidate)
        self.assertNotEqual(self.verify().returncode, 0)
        candidate = copy.deepcopy(self.policy)
        candidate["features"]["remoteUpdate"]["scheduledRequirements"] = [{
            "minimumVersion": "3", "effectiveAt": "2026-11-01T00:00:00Z",
        }]
        self.write(candidate)
        self.assertNotEqual(self.verify().returncode, 0)
        candidate["features"]["remoteUpdate"]["revision"] = 3
        self.write(candidate)
        self.assertEqual(self.verify().returncode, 0)

    def test_deleted_endpoint_is_rejected(self):
        (self.root / "example/app.json").unlink()
        self.assertNotEqual(self.verify(self.save()).returncode, 0)

    def test_repair_uses_last_readable_policy_and_still_requires_a_higher_revision(self):
        (self.root / "example/app.json").write_text("{invalid")
        broken = self.save()
        self.policy["features"]["remoteUpdate"]["requirement"] = {
            "minimumVersion": "3", "effectiveAt": "2026-01-01T00:00:00Z",
        }
        self.write(self.policy)
        self.assertNotEqual(self.verify(base=broken).returncode, 0)
        self.policy["features"]["remoteUpdate"]["revision"] = 3
        self.write(self.policy)
        self.assertEqual(self.verify(base=broken).returncode, 0)

    def test_recovery_after_a_published_rollback_cannot_reuse_a_historical_revision(self):
        self.policy["features"]["remoteUpdate"]["revision"] = 3
        self.write(self.policy)
        self.save()
        self.policy["features"]["remoteUpdate"]["revision"] = 1
        self.write(self.policy)
        rollback = self.save()
        self.policy["features"]["remoteUpdate"].update({
            "revision": 3,
            "requirement": {"minimumVersion": "2", "effectiveAt": "2026-01-01T00:00:00Z"},
        })
        self.write(self.policy)
        self.assertNotEqual(self.verify(base=rollback).returncode, 0)
        self.policy["features"]["remoteUpdate"]["revision"] = 4
        self.write(self.policy)
        self.assertEqual(self.verify(base=rollback).returncode, 0)

    def test_shallow_history_cannot_hide_a_previously_published_revision(self):
        self.policy["features"]["remoteUpdate"]["revision"] = 5
        self.write(self.policy)
        self.save()
        self.policy["features"]["remoteUpdate"]["revision"] = 1
        self.write(self.policy)
        self.save()
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory, "shallow")
            subprocess.run([
                "git", "clone", "--quiet", "--depth=1", self.root.as_uri(), str(checkout),
            ], check=True)
            self.policy["features"]["remoteUpdate"]["revision"] = 3
            candidate = checkout / "example/app.json"
            candidate.write_text(json.dumps(self.policy))

            def check():
                return subprocess.run([
                    sys.executable, str(VERIFIER), "--validator", VALIDATOR, "--base", "HEAD",
                ], cwd=checkout, capture_output=True, text=True, check=False)

            result = check()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Complete Git history is required", result.stderr)
            subprocess.run([
                "git", "-C", str(checkout), "fetch", "--quiet", "--unshallow",
            ], check=True)
            self.assertNotEqual(check().returncode, 0)
            self.policy["features"]["remoteUpdate"]["revision"] = 6
            candidate.write_text(json.dumps(self.policy))
            self.assertEqual(check().returncode, 0)

    def test_new_endpoint_and_initial_push_are_validated(self):
        new = copy.deepcopy(self.policy)
        new["bundleIdentifier"] = "new.app"
        path = self.root / "another/app.json"
        path.parent.mkdir()
        path.write_text(json.dumps(new))
        self.assertEqual(self.verify().returncode, 0)
        self.assertEqual(self.verify(candidate=self.save(), base="0" * 40).returncode, 0)


if __name__ == "__main__":
    unittest.main()
