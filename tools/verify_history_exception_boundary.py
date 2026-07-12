#!/usr/bin/env python3
"""Compare a fresh verified-remote history scan with one closed exception identity set."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from tools.privacy_history_scan import scan_history, verify_remote_refs
else:
    ROOT_IMPORT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT_IMPORT))
    from tools.privacy_history_scan import scan_history, verify_remote_refs


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "evidence" / "audits" / "git-history-privacy-exceptions-2026-07-12.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
OID = re.compile(r"^[0-9a-f]{40}$")
DATE = re.compile(r"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$")
BOUNDARY_FIELDS = {
    "schema_version", "status", "decision_owner", "decision_recorded_at",
    "decision_statement", "audit_record", "audit_record_sha256", "audited_revision",
    "scanner", "scanner_sha256", "finding_count", "finding_set_sha256", "categories",
    "forward_guard", "preserve_history", "history_rewrite_authorized",
    "raw_values_recorded", "activation", "activation_rule",
}
CATEGORY_FIELDS = {"rule", "object_type", "matches", "treatment"}
ACTIVATION_FIELDS = {
    "approved_candidate_revision", "decision_recorded_at", "decision_statement",
    "decision_statement_sha256",
}
DECISION = (
    "H1 REVISE: preserve history; treat the two recorded audit categories as bounded "
    "historical exceptions; add a forward guard; do not rewrite."
)
ACTIVATION_RULE = (
    "A second H1 decision must bind the exact candidate revision and activation diff. "
    "Activation changes status to active, adds the external decision record metadata, "
    "updates the policy status text and tests, and requires a successful fresh "
    "verified-remote comparison before merge."
)


class BoundaryError(ValueError):
    """The boundary or execution environment cannot support a trustworthy comparison."""


class BoundaryMismatch(ValueError):
    """The fresh finding identities differ from the closed historical exception set."""


@dataclass(frozen=True)
class Comparison:
    status: str
    remote_ref_count: int
    remote_ref_set_sha256: str
    objects_scanned: int
    path_observations: int
    finding_count: int
    finding_set_sha256: str


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


@contextmanager
def _replacement_objects_disabled():
    previous = os.environ.get("GIT_NO_REPLACE_OBJECTS")
    os.environ["GIT_NO_REPLACE_OBJECTS"] = "1"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("GIT_NO_REPLACE_OBJECTS", None)
        else:
            os.environ["GIT_NO_REPLACE_OBJECTS"] = previous


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BoundaryError("cannot load exception boundary or audit record") from exc
    if not isinstance(value, dict):
        raise BoundaryError("exception boundary or audit record must be an object")
    return value


def load_boundary(root: Path, path: Path) -> tuple[dict, dict]:
    boundary = _load_json(path)
    if set(boundary) != BOUNDARY_FIELDS or boundary.get("schema_version") != 1:
        raise BoundaryError("exception boundary has an invalid top-level shape")
    if not isinstance(boundary["status"], str) or boundary["status"] not in {
            "pending_second_h1", "active"}:
        raise BoundaryError("exception boundary has an invalid status")
    if (boundary["decision_owner"] != "Patrick Selamy"
            or not isinstance(boundary["decision_recorded_at"], str)
            or DATE.fullmatch(boundary["decision_recorded_at"]) is None
            or boundary["decision_statement"] != DECISION):
        raise BoundaryError("exception boundary has invalid decision metadata")
    for field in ("audit_record_sha256", "scanner_sha256", "finding_set_sha256"):
        if not isinstance(boundary[field], str) or SHA256.fullmatch(boundary[field]) is None:
            raise BoundaryError("exception boundary has an invalid digest")
    if (not isinstance(boundary["audited_revision"], str)
            or OID.fullmatch(boundary["audited_revision"]) is None):
        raise BoundaryError("exception boundary has an invalid audited revision")
    if (boundary["audit_record"] != "evidence/audits/git-history-privacy-2026-07-12.json"
            or boundary["scanner"] != "tools/privacy_history_scan.py"
            or boundary["forward_guard"] != "tools/privacy_forward_guard.py"):
        raise BoundaryError("exception boundary has an invalid confined path")
    if (not isinstance(boundary["finding_count"], int)
            or isinstance(boundary["finding_count"], bool)
            or boundary["finding_count"] < 1
            or boundary["preserve_history"] is not True
            or boundary["history_rewrite_authorized"] is not False
            or boundary["raw_values_recorded"] is not False):
        raise BoundaryError("exception boundary has invalid safety fields")
    if boundary["activation_rule"] != ACTIVATION_RULE:
        raise BoundaryError("exception boundary has an invalid activation rule")

    categories = boundary["categories"]
    if not isinstance(categories, list) or len(categories) != 2:
        raise BoundaryError("exception boundary requires exactly two categories")
    seen: set[tuple[str, str]] = set()
    for category in categories:
        if not isinstance(category, dict) or set(category) != CATEGORY_FIELDS:
            raise BoundaryError("exception category has an invalid field set")
        key = (category["rule"], category["object_type"])
        if (key in seen or key not in {
                ("private hostname", "commit"), ("local file URL", "blob")}
                or not isinstance(category["matches"], int)
                or isinstance(category["matches"], bool)
                or category["matches"] < 1
                or category["treatment"] != "bounded historical exception only"):
            raise BoundaryError("exception category is invalid, duplicate, or outside policy")
        seen.add(key)
    if sum(item["matches"] for item in categories) != boundary["finding_count"]:
        raise BoundaryError("exception category counts differ from finding count")

    activation = boundary["activation"]
    if boundary["status"] == "pending_second_h1":
        if activation is not None:
            raise BoundaryError("pending boundary cannot contain activation metadata")
    else:
        if not isinstance(activation, dict) or set(activation) != ACTIVATION_FIELDS:
            raise BoundaryError("active boundary lacks exact activation metadata")
        candidate = activation["approved_candidate_revision"]
        expected_statement = (
            "H1 PASS BOUNDED EXCEPTIONS: approve policy candidate " + candidate
            + "; activate exact closed boundary; create confidential metadata register "
            "controls only; H2/H3/H4 remain closed."
        ) if isinstance(candidate, str) else ""
        if (not isinstance(candidate, str) or OID.fullmatch(candidate) is None
                or not isinstance(activation["decision_recorded_at"], str)
                or DATE.fullmatch(activation["decision_recorded_at"]) is None
                or activation["decision_statement"] != expected_statement
                or not isinstance(activation["decision_statement_sha256"], str)
                or SHA256.fullmatch(activation["decision_statement_sha256"]) is None
                or hashlib.sha256(activation["decision_statement"].encode()).hexdigest()
                != activation["decision_statement_sha256"]):
            raise BoundaryError("active boundary has invalid activation metadata")

    audit_path = root / boundary["audit_record"]
    audit = _load_json(audit_path)
    if hashlib.sha256(audit_path.read_bytes()).hexdigest() != boundary["audit_record_sha256"]:
        raise BoundaryError("immutable audit record digest differs")
    scanner_path = root / boundary["scanner"]
    if hashlib.sha256(scanner_path.read_bytes()).hexdigest() != boundary["scanner_sha256"]:
        raise BoundaryError("historical scanner digest differs")
    if (audit.get("audited_revision") != boundary["audited_revision"]
            or audit.get("scanner_sha256") != boundary["scanner_sha256"]
            or audit.get("finding_count") != boundary["finding_count"]
            or audit.get("finding_set_sha256") != boundary["finding_set_sha256"]):
        raise BoundaryError("exception boundary differs from immutable audit record")
    expected_categories = Counter({
        (item["rule"], item["object_type"]): item["matches"]
        for item in audit.get("finding_summary", [])
    })
    boundary_categories = Counter({
        (item["rule"], item["object_type"]): item["matches"] for item in categories
    })
    if boundary_categories != expected_categories:
        raise BoundaryError("exception categories differ from immutable audit record")
    return boundary, audit


def compare(root: Path, remote: str, boundary_path: Path = BOUNDARY) -> Comparison:
    boundary, _ = load_boundary(root, boundary_path)
    with _replacement_objects_disabled():
        refs = verify_remote_refs(root, remote)
        revisions = tuple(dict.fromkeys(refs.values()))
        result = scan_history(root, revisions=revisions)
    findings = [{
        "object_id": item.object_id,
        "object_type": item.object_type,
        "path_digest": item.path_digest,
        "line": item.line,
        "rule": item.rule,
    } for item in result.findings]
    finding_digest = hashlib.sha256(canonical(sorted(findings, key=canonical))).hexdigest()
    categories = Counter((item.rule, item.object_type) for item in result.findings)
    expected_categories = Counter({
        (item["rule"], item["object_type"]): item["matches"]
        for item in boundary["categories"]
    })
    if (len(findings) != boundary["finding_count"]
            or finding_digest != boundary["finding_set_sha256"]
            or categories != expected_categories):
        raise BoundaryMismatch("fresh finding identity set differs from closed boundary")
    ref_digest = hashlib.sha256(canonical(refs)).hexdigest()
    return Comparison(
        status=boundary["status"],
        remote_ref_count=len(refs),
        remote_ref_set_sha256=ref_digest,
        objects_scanned=result.objects_scanned,
        path_observations=result.paths_scanned,
        finding_count=len(findings),
        finding_set_sha256=finding_digest,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--remote", required=True)
    args = parser.parse_args()
    try:
        result = compare(args.root.resolve(), args.remote, args.root.resolve() / BOUNDARY.relative_to(ROOT))
    except BoundaryMismatch as exc:
        print(f"Historical exception comparison REVISE: {exc}", file=sys.stderr)
        return 1
    except (BoundaryError, OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Historical exception comparison failed closed: {exc}", file=sys.stderr)
        return 2
    summary = (
        f"refs={result.remote_ref_count}, ref_set_sha256={result.remote_ref_set_sha256}, "
        f"objects={result.objects_scanned}, path_observations={result.path_observations}, "
        f"findings={result.finding_count}, finding_set_sha256={result.finding_set_sha256}"
    )
    if result.status != "active":
        print(f"Historical exception identities MATCH BUT INACTIVE: {summary}", file=sys.stderr)
        return 3
    print(f"PASS WITH RECORDED HISTORICAL EXCEPTIONS: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
