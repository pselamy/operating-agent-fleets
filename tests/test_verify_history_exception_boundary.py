from __future__ import annotations

import copy
import hashlib
import io
import json
import os
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

    def write_boundary(self, value: dict) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "boundary.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def recorded_refs(self) -> dict[str, str]:
        return self.refs

    def test_pending_boundary_matches_exact_recorded_identities_but_cannot_pass(self) -> None:
        refs = self.recorded_refs()
        with (mock.patch.object(verifier, "verify_remote_refs", return_value=refs),
              mock.patch.object(verifier, "scan_history", return_value=self.recorded_result)):
            result = verifier.compare(ROOT, "origin")
        self.assertEqual(result.status, "pending_second_h1")
        self.assertEqual(result.finding_count, 124)
        self.assertEqual(
            result.finding_set_sha256,
            "7a42c274bb021a4a07b08e10bb27a0d34019a839ded490fce8517205db852566",
        )
        stderr = io.StringIO()
        with (mock.patch.object(verifier, "verify_remote_refs", return_value=refs),
              mock.patch.object(verifier, "scan_history", return_value=self.recorded_result),
              mock.patch("sys.argv", [
                  "verify_history_exception_boundary.py", "--root", str(ROOT),
                  "--remote", "origin",
              ]),
              mock.patch("sys.stderr", stderr)):
            self.assertEqual(verifier.main(), 3)
        output = stderr.getvalue()
        self.assertIn("MATCH BUT INACTIVE", output)
        first_finding = self.recorded_result.findings[0]
        self.assertNotIn(first_finding.object_id[:12], output)
        self.assertNotIn(f":{first_finding.line}:", output)

    def test_active_boundary_requires_external_decision_metadata(self) -> None:
        boundary = self.boundary()
        candidate = "a" * 40
        statement = (
            "H1 PASS BOUNDED EXCEPTIONS: approve policy candidate " + candidate
            + "; activate exact closed boundary; create confidential metadata register "
            "controls only; H2/H3/H4 remain closed."
        )
        boundary.update(
            status="active",
            activation={
                "approved_candidate_revision": candidate,
                "decision_recorded_at": "2026-07-12",
                "decision_statement": statement,
                "decision_statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
            },
        )
        path = self.write_boundary(boundary)
        refs = self.recorded_refs()
        with (mock.patch.object(verifier, "verify_remote_refs", return_value=refs),
              mock.patch.object(verifier, "scan_history", return_value=self.recorded_result)):
            result = verifier.compare(ROOT, "origin", path)
        self.assertEqual(result.status, "active")

        boundary["activation"] = None
        with self.assertRaisesRegex(verifier.BoundaryError, "activation metadata"):
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
        pending_activation = self.boundary()
        pending_activation["activation"] = {}
        cases.append((pending_activation, "pending boundary"))
        bad_active = self.boundary()
        bad_active.update(status="active", activation={})
        cases.append((bad_active, "activation metadata"))
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
        ]
        with (mock.patch("sys.argv", argv),
              mock.patch.object(verifier, "compare", side_effect=verifier.BoundaryMismatch("changed"))):
            self.assertEqual(verifier.main(), 1)
        with (mock.patch("sys.argv", argv),
              mock.patch.object(verifier, "compare", side_effect=verifier.BoundaryError("bad"))):
            self.assertEqual(verifier.main(), 2)
        active = verifier.Comparison(
            status="active",
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


if __name__ == "__main__":
    unittest.main()
