from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import verify_history_exception_boundary as verifier
from tools.privacy_history_scan import scan_history


ROOT = Path(__file__).parents[1]
BOUNDARY = ROOT / "evidence" / "audits" / "git-history-privacy-exceptions-2026-07-12.json"
REFS = ROOT / "evidence" / "audits" / "git-history-privacy-2026-07-12-refs.json"


class HistoryExceptionBoundaryVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.refs = json.loads(REFS.read_text(encoding="utf-8"))["refs"]
        cls.recorded_result = scan_history(
            ROOT, revisions=tuple(dict.fromkeys(cls.refs.values()))
        )

    def boundary(self) -> dict:
        return json.loads(BOUNDARY.read_text(encoding="utf-8"))

    def pending_boundary(self) -> dict:
        boundary = self.boundary()
        boundary.update(status="pending_second_h1", activation=None)
        return boundary

    def write_boundary(self, value: dict) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "boundary.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def recorded_refs(self) -> dict[str, str]:
        return self.refs

    def test_recorded_boundary_matches_exact_identities_but_cannot_self_authorize(self) -> None:
        refs = self.recorded_refs()
        with (mock.patch.object(verifier, "verify_remote_refs", return_value=refs),
              mock.patch.object(verifier, "scan_history", return_value=self.recorded_result)):
            result = verifier.compare(ROOT, "origin")
        self.assertEqual(result.status, self.boundary()["status"])
        self.assertFalse(result.authorized)
        self.assertEqual(result.finding_count, 124)
        self.assertEqual(
            result.finding_set_sha256,
            "7a42c274bb021a4a07b08e10bb27a0d34019a839ded490fce8517205db852566",
        )
        stderr = io.StringIO()
        current = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        with (mock.patch.object(verifier, "verify_remote_refs", return_value=refs),
              mock.patch.object(verifier, "scan_history", return_value=self.recorded_result),
              mock.patch.object(verifier, "_validate_current_candidate", return_value=False),
              mock.patch("sys.argv", [
                  "verify_history_exception_boundary.py", "--root", str(ROOT),
                  "--remote", "origin", "--current", current,
              ]),
              mock.patch("sys.stderr", stderr)):
            self.assertEqual(verifier.main(), 3)
        output = stderr.getvalue()
        self.assertIn("MATCH BUT NOT EXTERNALLY AUTHORIZED", output)
        first_finding = self.recorded_result.findings[0]
        self.assertNotIn(first_finding.object_id[:12], output)
        self.assertNotIn(f":{first_finding.line}:", output)

    def test_ready_boundary_has_closed_activation_shape_but_is_not_self_authorizing(self) -> None:
        boundary = self.boundary()
        boundary.update(
            status="ready_for_second_h1",
            activation={
                "policy_base_revision": "a" * 40,
                "allowed_paths": list(verifier.ALLOWED_ACTIVATION_PATHS),
            },
        )
        path = self.write_boundary(boundary)
        refs = self.recorded_refs()
        with (mock.patch.object(verifier, "verify_remote_refs", return_value=refs),
              mock.patch.object(verifier, "scan_history", return_value=self.recorded_result)):
            result = verifier.compare(ROOT, "origin", path)
        self.assertEqual(result.status, "ready_for_second_h1")
        self.assertFalse(result.authorized)

        boundary["activation"] = None
        with self.assertRaisesRegex(verifier.BoundaryError, "ready boundary"):
            verifier.load_boundary(ROOT, self.write_boundary(boundary))

    def test_nested_boundary_is_closed_and_mismatch_fails(self) -> None:
        cases = []
        extra = self.boundary()
        extra["categories"][0]["raw_locator"] = "forbidden"
        cases.append(extra)
        duplicate = self.boundary()
        duplicate["categories"][1] = copy.deepcopy(duplicate["categories"][0])
        cases.append(duplicate)
        wrong_type = self.boundary()
        wrong_type["categories"][0]["matches"] = True
        cases.append(wrong_type)
        extra_category = self.boundary()
        extra_category["categories"].append({
            "rule": "AWS access key", "object_type": "blob", "matches": 1,
            "treatment": "bounded historical exception only",
        })
        cases.append(extra_category)
        for candidate in cases:
            with self.assertRaises(verifier.BoundaryError):
                verifier.load_boundary(ROOT, self.write_boundary(candidate))

        refs = self.recorded_refs()
        original = self.recorded_result
        changed = original.__class__(
            objects_scanned=original.objects_scanned,
            paths_scanned=original.paths_scanned,
            path_bytes_scanned=original.path_bytes_scanned,
            bytes_scanned=original.bytes_scanned,
            findings=original.findings[:-1],
        )
        with (mock.patch.object(verifier, "verify_remote_refs", return_value=refs),
              mock.patch.object(verifier, "scan_history", return_value=changed)):
            with self.assertRaisesRegex(verifier.BoundaryMismatch, "differs"):
                verifier.compare(ROOT, "origin")

    def test_boundary_validation_failures_are_closed(self) -> None:
        malformed = self.write_boundary({"not": "the schema"})
        with self.assertRaisesRegex(verifier.BoundaryError, "top-level shape"):
            verifier.load_boundary(ROOT, malformed)
        malformed.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(verifier.BoundaryError, "must be an object"):
            verifier.load_boundary(ROOT, malformed)
        malformed.write_text("not json", encoding="utf-8")
        with self.assertRaisesRegex(verifier.BoundaryError, "cannot load"):
            verifier.load_boundary(ROOT, malformed)

        cases: list[tuple[dict, str]] = []
        boolean_schema = self.boundary()
        boolean_schema["schema_version"] = True
        cases.append((boolean_schema, "top-level shape"))
        for field, value, message in (
            ("status", "forged", "invalid status"),
            ("decision_owner", "Agent", "decision metadata"),
            ("finding_set_sha256", "x", "invalid digest"),
            ("audited_revision", "main", "audited revision"),
            ("scanner", "private/scanner.py", "confined path"),
            ("preserve_history", False, "safety fields"),
            ("activation_rule", "self activate", "activation rule"),
        ):
            candidate = self.boundary()
            candidate[field] = value
            cases.append((candidate, message))
        bad_sum = self.boundary()
        bad_sum["categories"][0]["matches"] -= 1
        cases.append((bad_sum, "counts differ"))
        pending_activation = self.pending_boundary()
        pending_activation["activation"] = {}
        cases.append((pending_activation, "pending boundary"))
        bad_ready = self.boundary()
        bad_ready.update(status="ready_for_second_h1", activation={})
        cases.append((bad_ready, "ready boundary"))
        scalar_type = self.boundary()
        scalar_type["categories"][0]["rule"] = []
        cases.append((scalar_type, "scalar types"))
        bad_audit_digest = self.boundary()
        bad_audit_digest["audit_record_sha256"] = "0" * 64
        cases.append((bad_audit_digest, "audit record digest"))
        bad_scanner_digest = self.boundary()
        bad_scanner_digest["scanner_sha256"] = "0" * 64
        cases.append((bad_scanner_digest, "scanner digest"))
        bad_audit_binding = self.boundary()
        bad_audit_binding["audited_revision"] = "b" * 40
        cases.append((bad_audit_binding, "differs from immutable audit"))
        bad_categories = self.boundary()
        bad_categories["categories"][0]["matches"] -= 1
        bad_categories["categories"][1]["matches"] += 1
        cases.append((bad_categories, "categories differ"))
        for candidate, message in cases:
            with self.assertRaisesRegex(verifier.BoundaryError, message):
                verifier.load_boundary(ROOT, self.write_boundary(candidate))

    def test_environment_restoration_and_cli_result_classes(self) -> None:
        refs = self.recorded_refs()
        previous = os.environ.get("GIT_NO_REPLACE_OBJECTS")
        os.environ["GIT_NO_REPLACE_OBJECTS"] = "prior"
        try:
            with (mock.patch.object(verifier, "verify_remote_refs", return_value=refs),
                  mock.patch.object(verifier, "scan_history", return_value=self.recorded_result)):
                verifier.compare(ROOT, "origin")
            self.assertEqual(os.environ["GIT_NO_REPLACE_OBJECTS"], "prior")
        finally:
            if previous is None:
                os.environ.pop("GIT_NO_REPLACE_OBJECTS", None)
            else:
                os.environ["GIT_NO_REPLACE_OBJECTS"] = previous

        argv = [
            "verify_history_exception_boundary.py", "--root", str(ROOT), "--remote", "origin",
            "--current", "a" * 40,
        ]
        with (mock.patch("sys.argv", argv),
              mock.patch.object(verifier, "compare", side_effect=verifier.BoundaryMismatch("changed"))):
            self.assertEqual(verifier.main(), 1)
        with (mock.patch("sys.argv", argv),
              mock.patch.object(verifier, "compare", side_effect=verifier.BoundaryError("bad"))):
            self.assertEqual(verifier.main(), 2)
        active = verifier.Comparison(
            status="ready_for_second_h1",
            authorized=True,
            current_revision="a" * 40,
            remote_ref_count=1,
            remote_ref_set_sha256="a" * 64,
            objects_scanned=3,
            path_observations=1,
            finding_count=124,
            finding_set_sha256="b" * 64,
        )
        stdout = io.StringIO()
        with (mock.patch("sys.argv", argv), mock.patch.object(verifier, "compare", return_value=active),
              mock.patch("sys.stdout", stdout)):
            self.assertEqual(verifier.main(), 0)
        self.assertIn("PASS WITH RECORDED HISTORICAL EXCEPTIONS", stdout.getvalue())

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        target = Path(directory.name) / "external.json"
        target.write_text("{}", encoding="utf-8")
        linked = Path(directory.name) / "external-link.json"
        linked.symlink_to(target)
        captured: dict[str, Path | None] = {}

        def capture_compare(*args, **kwargs):
            captured["attestation_path"] = kwargs["attestation_path"]
            raise verifier.BoundaryError("stop after argument capture")

        with (mock.patch("sys.argv", argv + ["--attestation", str(linked)]),
              mock.patch.object(verifier, "compare", side_effect=capture_compare)):
            self.assertEqual(verifier.main(), 2)
        self.assertEqual(captured["attestation_path"], linked)
        self.assertTrue(captured["attestation_path"].is_symlink())

    def test_ready_candidate_requires_exact_diff_and_external_attestation(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name) / "repo"
        root.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "synthetic@example.test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Synthetic Test"], cwd=root, check=True)
        boundary_path = root / verifier.BOUNDARY_RELATIVE
        policy_path = root / verifier.POLICY_RELATIVE
        test_path = root / verifier.TEST_RELATIVE
        for path in (boundary_path, policy_path, test_path):
            path.parent.mkdir(parents=True, exist_ok=True)
        pending = self.pending_boundary()
        boundary_path.write_text(json.dumps(pending, indent=2) + "\n", encoding="utf-8")
        policy_path.write_text("pending policy\n", encoding="utf-8")
        test_path.write_text("pending test\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "pending policy"], cwd=root, check=True)
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()

        ready = copy.deepcopy(pending)
        ready.update(
            status="ready_for_second_h1",
            activation={
                "policy_base_revision": base,
                "allowed_paths": list(verifier.ALLOWED_ACTIVATION_PATHS),
            },
        )
        boundary_path.write_text(json.dumps(ready, indent=2) + "\n", encoding="utf-8")
        policy_path.write_text("ready policy\n", encoding="utf-8")
        test_path.write_text("ready test\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "ready policy"], cwd=root, check=True)
        current = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        statement = (
            "H1 PASS BOUNDED EXCEPTIONS: approve activation candidate " + current
            + "; activate exact closed boundary; create confidential metadata register controls "
            "only; H2/H3/H4 remain closed."
        )
        attestation = {
            "schema_version": 1,
            "decision_owner": "Patrick Selamy",
            "decision_recorded_at": "2026-07-12",
            "activation_candidate_revision": current,
            "decision_statement": statement,
            "decision_statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
        }
        attestation_path = Path(directory.name) / "external-attestation.json"
        attestation_path.write_text(json.dumps(attestation), encoding="utf-8")
        with verifier._replacement_objects_disabled():
            self.assertTrue(verifier._validate_current_candidate(
                root, ready, boundary_path, current, attestation_path
            ))
            self.assertFalse(verifier._validate_current_candidate(
                root, ready, boundary_path, current, None
            ))

        in_repo_attestation = root / "local-attestation.json"
        in_repo_attestation.write_text(json.dumps(attestation), encoding="utf-8")
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "outside the worktree"):
                verifier._validate_current_candidate(
                    root, ready, boundary_path, current, in_repo_attestation
                )
        subprocess.run(["git", "add", str(in_repo_attestation)], cwd=root, check=True)
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "outside the worktree"):
                verifier._validate_current_candidate(
                    root, ready, boundary_path, current, in_repo_attestation
                )
        symlink_attestation = Path(directory.name) / "linked-attestation.json"
        symlink_attestation.symlink_to(in_repo_attestation)
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "symbolic link"):
                verifier._validate_current_candidate(
                    root, ready, boundary_path, current, symlink_attestation
                )

        worktree_link = root / "external-attestation-link.json"
        worktree_link.symlink_to(attestation_path)
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "symbolic link"):
                verifier._validate_current_candidate(
                    root, ready, boundary_path, current, worktree_link
                )

        git_attestation = root / ".git" / "attestation.json"
        git_attestation.write_text(json.dumps(attestation), encoding="utf-8")
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "outside the worktree"):
                verifier._validate_current_candidate(
                    root, ready, boundary_path, current, git_attestation
                )

        boolean_attestation = copy.deepcopy(attestation)
        boolean_attestation["schema_version"] = True
        boolean_attestation_path = Path(directory.name) / "boolean-attestation.json"
        boolean_attestation_path.write_text(json.dumps(boolean_attestation), encoding="utf-8")
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "invalid shape"):
                verifier._validate_current_candidate(
                    root, ready, boundary_path, current, boolean_attestation_path
                )

        forged = copy.deepcopy(attestation)
        forged["activation_candidate_revision"] = base
        forged_path = Path(directory.name) / "forged-attestation.json"
        forged_path.write_text(json.dumps(forged), encoding="utf-8")
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "attestation"):
                verifier._validate_current_candidate(root, ready, boundary_path, current, forged_path)

        (root / "unapproved.md").write_text("extra\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "unapproved extra"], cwd=root, check=True)
        extra = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "outside"):
                verifier._validate_current_candidate(root, ready, boundary_path, extra, None)

        nonexistent = copy.deepcopy(ready)
        nonexistent["activation"]["policy_base_revision"] = "f" * 40
        boundary_path.write_text(json.dumps(nonexistent, indent=2) + "\n", encoding="utf-8")
        subprocess.run(["git", "add", str(verifier.BOUNDARY_RELATIVE)], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "nonexistent base"], cwd=root, check=True)
        bad_current = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "Git validation"):
                verifier._validate_current_candidate(
                    root, nonexistent, boundary_path, bad_current, None
                )

        blob = subprocess.run(
            ["git", "hash-object", "-w", str(policy_path)],
            cwd=root, check=True, capture_output=True, text=True,
        ).stdout.strip()
        noncommit = copy.deepcopy(ready)
        noncommit["activation"]["policy_base_revision"] = blob
        boundary_path.write_text(json.dumps(noncommit, indent=2) + "\n", encoding="utf-8")
        subprocess.run(["git", "add", str(verifier.BOUNDARY_RELATIVE)], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "noncommit base"], cwd=root, check=True)
        noncommit_current = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "not a commit"):
                verifier._validate_current_candidate(
                    root, noncommit, boundary_path, noncommit_current, None
                )

        subprocess.run(["git", "checkout", "-q", "--orphan", "unrelated"], cwd=root, check=True)
        subprocess.run(["git", "rm", "-q", "-rf", "."], cwd=root, check=True)
        unrelated_ready = copy.deepcopy(ready)
        for path in (boundary_path, policy_path, test_path):
            path.parent.mkdir(parents=True, exist_ok=True)
        boundary_path.write_text(json.dumps(unrelated_ready, indent=2) + "\n", encoding="utf-8")
        policy_path.write_text("unrelated ready policy\n", encoding="utf-8")
        test_path.write_text("unrelated ready test\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "unrelated ready"], cwd=root, check=True)
        unrelated_current = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        with verifier._replacement_objects_disabled():
            with self.assertRaisesRegex(verifier.BoundaryError, "not an ancestor"):
                verifier._validate_current_candidate(
                    root, unrelated_ready, boundary_path, unrelated_current, None
                )


if __name__ == "__main__":
    unittest.main()
