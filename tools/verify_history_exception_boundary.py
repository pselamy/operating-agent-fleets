#!/usr/bin/env python3
"""Compare fresh public history with a closed, externally authorized exception set."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
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
BOUNDARY_RELATIVE = Path("evidence/audits/git-history-privacy-exceptions-2026-07-12.json")
BOUNDARY = ROOT / BOUNDARY_RELATIVE
POLICY_RELATIVE = Path("docs/disclosure-policy.md")
TEST_RELATIVE = Path("tests/test_history_exception_policy.py")
ALLOWED_ACTIVATION_PATHS = tuple(sorted(map(str, (
    BOUNDARY_RELATIVE, POLICY_RELATIVE, TEST_RELATIVE,
))))
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
ACTIVATION_FIELDS = {"policy_base_revision", "allowed_paths"}
ATTESTATION_FIELDS = {
    "schema_version", "decision_owner", "decision_recorded_at",
    "activation_candidate_revision", "decision_statement", "decision_statement_sha256",
}
DECISION = (
    "H1 REVISE: preserve history; treat the two recorded audit categories as bounded "
    "historical exceptions; add a forward guard; do not rewrite."
)
ACTIVATION_RULE = (
    "A second H1 decision must bind the exact ready candidate revision through an external "
    "attestation. The ready candidate may differ from its pending policy base only at the "
    "declared activation paths. No repository field can activate the boundary by itself."
)


class BoundaryError(ValueError):
    """The boundary, attestation, or execution environment is invalid."""


class BoundaryMismatch(ValueError):
    """Fresh finding identities differ from the closed historical exception set."""


@dataclass(frozen=True)
class Comparison:
    status: str
    authorized: bool
    current_revision: str | None
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


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    if result.returncode != 0:
        raise BoundaryError("Git validation operation failed")
    return result.stdout


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BoundaryError("cannot load boundary, audit, or attestation") from exc
    if not isinstance(value, dict):
        raise BoundaryError("boundary, audit, or attestation must be an object")
    return value


def _string(value: object) -> bool:
    return isinstance(value, str)


def _schema_one(value: object) -> bool:
    return type(value) is int and value == 1


def load_boundary(root: Path, path: Path) -> tuple[dict, dict]:
    boundary = _load_json(path)
    if set(boundary) != BOUNDARY_FIELDS or not _schema_one(boundary.get("schema_version")):
        raise BoundaryError("exception boundary has an invalid top-level shape")
    if not _string(boundary["status"]) or boundary["status"] not in {
            "pending_second_h1", "ready_for_second_h1"}:
        raise BoundaryError("exception boundary has an invalid status")
    if (boundary["decision_owner"] != "Patrick Selamy"
            or not _string(boundary["decision_recorded_at"])
            or DATE.fullmatch(boundary["decision_recorded_at"]) is None
            or boundary["decision_statement"] != DECISION):
        raise BoundaryError("exception boundary has invalid decision metadata")
    for field in ("audit_record_sha256", "scanner_sha256", "finding_set_sha256"):
        if not _string(boundary[field]) or SHA256.fullmatch(boundary[field]) is None:
            raise BoundaryError("exception boundary has an invalid digest")
    if (not _string(boundary["audited_revision"])
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
        if not _string(category["rule"]) or not _string(category["object_type"]):
            raise BoundaryError("exception category has invalid scalar types")
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
            raise BoundaryError("ready boundary lacks exact activation metadata")
        if (not _string(activation["policy_base_revision"])
                or OID.fullmatch(activation["policy_base_revision"]) is None
                or activation["allowed_paths"] != list(ALLOWED_ACTIVATION_PATHS)):
            raise BoundaryError("ready boundary has invalid activation metadata")

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


def _load_attestation(path: Path, current_revision: str) -> dict:
    attestation = _load_json(path)
    if set(attestation) != ATTESTATION_FIELDS or not _schema_one(attestation.get("schema_version")):
        raise BoundaryError("external H1 attestation has an invalid shape")
    expected_statement = (
        "H1 PASS BOUNDED EXCEPTIONS: approve activation candidate " + current_revision
        + "; activate exact closed boundary; create confidential metadata register controls "
        "only; H2/H3/H4 remain closed."
    )
    if (attestation["decision_owner"] != "Patrick Selamy"
            or not _string(attestation["decision_recorded_at"])
            or DATE.fullmatch(attestation["decision_recorded_at"]) is None
            or attestation["activation_candidate_revision"] != current_revision
            or attestation["decision_statement"] != expected_statement
            or not _string(attestation["decision_statement_sha256"])
            or SHA256.fullmatch(attestation["decision_statement_sha256"]) is None
            or hashlib.sha256(expected_statement.encode()).hexdigest()
            != attestation["decision_statement_sha256"]):
        raise BoundaryError("external H1 attestation is invalid or bound to another candidate")
    return attestation


def _require_external_attestation(root: Path, path: Path) -> Path:
    supplied = Path(os.path.abspath(path))
    if supplied.is_symlink():
        raise BoundaryError("external H1 attestation cannot be a symbolic link")
    resolved = path.resolve(strict=True)
    worktree = Path(_git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    common_raw = Path(_git(root, "rev-parse", "--git-common-dir").decode().strip())
    common = (common_raw if common_raw.is_absolute() else root / common_raw).resolve()
    if (supplied == worktree or supplied.is_relative_to(worktree)
            or resolved == worktree or resolved.is_relative_to(worktree)):
        raise BoundaryError("external H1 attestation must be outside the worktree")
    if (supplied == common or supplied.is_relative_to(common)
            or resolved == common or resolved.is_relative_to(common)):
        raise BoundaryError("external H1 attestation must be outside the Git common directory")
    if not resolved.is_file():
        raise BoundaryError("external H1 attestation must resolve to a regular file")
    return resolved


def _validate_current_candidate(
    root: Path,
    boundary: dict,
    boundary_path: Path,
    current_revision: str,
    attestation_path: Path | None,
) -> bool:
    if OID.fullmatch(current_revision) is None:
        raise BoundaryError("current revision must be a full lowercase commit OID")
    if _git(root, "cat-file", "-t", current_revision).decode("ascii").strip() != "commit":
        raise BoundaryError("current revision is not a commit")
    committed_boundary = _git(root, "show", f"{current_revision}:{BOUNDARY_RELATIVE}")
    if committed_boundary != boundary_path.read_bytes():
        raise BoundaryError("current revision does not contain the exact local boundary")
    if boundary["status"] == "pending_second_h1":
        if attestation_path is not None:
            raise BoundaryError("pending candidate cannot consume an H1 attestation")
        return False

    base = boundary["activation"]["policy_base_revision"]
    if _git(root, "cat-file", "-t", base).decode("ascii").strip() != "commit":
        raise BoundaryError("policy base revision is not a commit")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, current_revision],
        cwd=root, capture_output=True, check=False,
    )
    if ancestry.returncode != 0:
        raise BoundaryError("policy base is not an ancestor of ready candidate")
    changed = _git(root, "diff", "--name-only", "-z", base, current_revision).split(b"\0")
    changed_paths = sorted(item.decode("utf-8") for item in changed if item)
    if changed_paths != list(ALLOWED_ACTIVATION_PATHS):
        raise BoundaryError("ready candidate differs outside the exact activation path set")
    base_boundary_bytes = _git(root, "show", f"{base}:{BOUNDARY_RELATIVE}")
    try:
        base_boundary = json.loads(base_boundary_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BoundaryError("policy base lacks a valid pending boundary") from exc
    if (not isinstance(base_boundary, dict)
            or base_boundary.get("status") != "pending_second_h1"
            or base_boundary.get("activation") is not None):
        raise BoundaryError("policy base is not the reviewed pending boundary")
    if attestation_path is None:
        return False
    _load_attestation(_require_external_attestation(root, attestation_path), current_revision)
    return True


def compare(
    root: Path,
    remote: str,
    boundary_path: Path = BOUNDARY,
    *,
    current_revision: str | None = None,
    attestation_path: Path | None = None,
) -> Comparison:
    boundary, _ = load_boundary(root, boundary_path)
    with _replacement_objects_disabled():
        authorized = False
        if current_revision is not None:
            authorized = _validate_current_candidate(
                root, boundary, boundary_path, current_revision, attestation_path
            )
        elif attestation_path is not None:
            raise BoundaryError("attestation requires an explicit current revision")
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
    return Comparison(
        status=boundary["status"],
        authorized=authorized,
        current_revision=current_revision,
        remote_ref_count=len(refs),
        remote_ref_set_sha256=hashlib.sha256(canonical(refs)).hexdigest(),
        objects_scanned=result.objects_scanned,
        path_observations=result.paths_scanned,
        finding_count=len(findings),
        finding_set_sha256=finding_digest,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--remote", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--attestation", type=Path)
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        result = compare(
            root,
            args.remote,
            root / BOUNDARY_RELATIVE,
            current_revision=args.current,
            attestation_path=args.attestation.resolve() if args.attestation else None,
        )
    except BoundaryMismatch:
        print("Historical exception comparison REVISE: identity-set mismatch", file=sys.stderr)
        return 1
    except (BoundaryError, OSError, UnicodeDecodeError, ValueError, TypeError):
        print("Historical exception comparison failed closed: sanitized validation error", file=sys.stderr)
        return 2
    summary = (
        f"current={result.current_revision}, refs={result.remote_ref_count}, "
        f"ref_set_sha256={result.remote_ref_set_sha256}, objects={result.objects_scanned}, "
        f"path_observations={result.path_observations}, findings={result.finding_count}, "
        f"finding_set_sha256={result.finding_set_sha256}"
    )
    if not result.authorized:
        print(f"Historical exception identities MATCH BUT NOT EXTERNALLY AUTHORIZED: {summary}", file=sys.stderr)
        return 3
    print(f"PASS WITH RECORDED HISTORICAL EXCEPTIONS: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
