from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from tools.privacy_history_scan import historical_paths, reachable_objects, scan_history


ROOT = Path(__file__).parents[1]
AUDIT = ROOT / "evidence" / "audits" / "git-history-privacy-2026-07-12.json"
REFS = ROOT / "evidence" / "audits" / "git-history-privacy-2026-07-12-refs.json"
SCANNER = ROOT / "tools" / "privacy_history_scan.py"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class HistoryAuditRecordTests(unittest.TestCase):
    def test_record_replays_exact_immutable_ref_set(self) -> None:
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        ref_record = json.loads(REFS.read_text(encoding="utf-8"))
        refs = ref_record["refs"]
        revisions = tuple(dict.fromkeys(refs.values()))

        self.assertEqual(hashlib.sha256(REFS.read_bytes()).hexdigest(), audit["revision_set_file_sha256"])
        self.assertEqual(hashlib.sha256(canonical(refs)).hexdigest(), audit["revision_set_canonical_sha256"])
        self.assertEqual(hashlib.sha256(SCANNER.read_bytes()).hexdigest(), audit["scanner_sha256"])
        self.assertEqual(len(refs), audit["remote_refs"])

        result = scan_history(ROOT, revisions=revisions)
        objects = reachable_objects(ROOT, revisions)
        paths, path_bytes_scanned = historical_paths(ROOT, revisions)
        findings = [{
            "object_id": item.object_id,
            "object_type": item.object_type,
            "path_digest": item.path_digest,
            "line": item.line,
            "rule": item.rule,
        } for item in result.findings]
        sorted_findings = sorted(findings, key=canonical)
        path_digests = sorted(
            hashlib.sha256(path.encode("utf-8", errors="surrogateescape")).hexdigest()
            for _, path in paths
        )

        self.assertEqual(result.objects_scanned, audit["reachable_objects_examined"])
        self.assertEqual(result.paths_scanned, audit["historical_paths_examined"])
        self.assertEqual(result.path_bytes_scanned, audit["historical_path_bytes_scanned"])
        self.assertEqual(path_bytes_scanned, audit["historical_path_bytes_scanned"])
        self.assertEqual(result.bytes_scanned, audit["payload_bytes_scanned"])
        self.assertEqual(len(result.findings), audit["finding_count"])
        self.assertEqual(
            hashlib.sha256(("\n".join(sorted(objects)) + "\n").encode()).hexdigest(),
            audit["reachable_object_set_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(("\n".join(path_digests) + "\n").encode()).hexdigest(),
            audit["historical_path_set_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(canonical(sorted_findings)).hexdigest(),
            audit["finding_set_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
