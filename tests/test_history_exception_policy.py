from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
BOUNDARY = ROOT / "evidence" / "audits" / "git-history-privacy-exceptions-2026-07-12.json"
AUDIT = ROOT / "evidence" / "audits" / "git-history-privacy-2026-07-12.json"
POLICY = ROOT / "docs" / "disclosure-policy.md"
SCANNER = ROOT / "tools" / "privacy_history_scan.py"
FORWARD_GUARD = ROOT / "tools" / "privacy_forward_guard.py"


class HistoryExceptionPolicyTests(unittest.TestCase):
    def test_ready_boundary_is_exactly_bound_and_grants_no_self_authorization(self) -> None:
        boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(set(boundary), {
            "schema_version", "status", "decision_owner", "decision_recorded_at",
            "decision_statement", "audit_record", "audit_record_sha256", "audited_revision", "scanner",
            "scanner_sha256", "finding_count", "finding_set_sha256", "categories",
            "forward_guard", "preserve_history", "history_rewrite_authorized",
            "raw_values_recorded", "activation", "activation_rule",
        })
        self.assertEqual(boundary["schema_version"], 1)
        self.assertEqual(boundary["status"], "ready_for_second_h1")
        self.assertEqual(
            boundary["decision_statement"],
            "H1 REVISE: preserve history; treat the two recorded audit categories as "
            "bounded historical exceptions; add a forward guard; do not rewrite.",
        )
        self.assertEqual(boundary["audit_record"], str(AUDIT.relative_to(ROOT)))
        self.assertEqual(boundary["audited_revision"], audit["audited_revision"])
        self.assertEqual(boundary["scanner"], audit["scanner"])
        self.assertEqual(boundary["scanner_sha256"], audit["scanner_sha256"])
        self.assertEqual(boundary["finding_count"], audit["finding_count"])
        self.assertEqual(boundary["finding_set_sha256"], audit["finding_set_sha256"])
        self.assertEqual(
            hashlib.sha256(SCANNER.read_bytes()).hexdigest(), boundary["scanner_sha256"]
        )
        self.assertTrue(FORWARD_GUARD.is_file())
        self.assertTrue(boundary["preserve_history"])
        self.assertFalse(boundary["history_rewrite_authorized"])
        self.assertFalse(boundary["raw_values_recorded"])
        self.assertEqual(boundary["activation"], {
            "policy_base_revision": "aa883e4277bb80559a8822dc016922b15ef8100e",
            "allowed_paths": [
                "docs/disclosure-policy.md",
                "evidence/audits/git-history-privacy-exceptions-2026-07-12.json",
                "tests/test_history_exception_policy.py",
            ],
        })

        categories = {(item["rule"], item["object_type"]): item["matches"]
                      for item in boundary["categories"]}
        expected = {(item["rule"], item["object_type"]): item["matches"]
                    for item in audit["finding_summary"]}
        self.assertEqual(categories, expected)
        self.assertTrue(all(
            item["treatment"] == "bounded historical exception only"
            for item in boundary["categories"]
        ))

    def test_policy_states_closed_identity_boundary_and_second_gate(self) -> None:
        policy = POLICY.read_text(encoding="utf-8")
        for required in (
            "those finding identities—not the pattern categories generally",
            "same 124 finding identities, categories, counts, and finding-set digest with no missing or additional finding",
            "PASS WITH RECORDED HISTORICAL EXCEPTIONS",
            "pending_second_h1",
            "History rewriting is prohibited",
            "second H1 decision",
        ):
            self.assertIn(required, policy)
        self.assertNotIn("clean Git history", policy)


if __name__ == "__main__":
    unittest.main()
