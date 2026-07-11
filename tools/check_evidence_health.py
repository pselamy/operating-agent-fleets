#!/usr/bin/env python3
"""Report evidence staleness and deduplicated public-link health."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # pragma: no cover - direct-script bootstrap
    sys.path.insert(0, str(ROOT))  # pragma: no cover

from tools.validate_evidence import EvidenceValidationError, load_json, validate_atlas


@dataclass(frozen=True)
class LinkHealth:
    url: str
    status: str
    http_status: int | None
    final_url: str | None


def revalidation_state(record: dict[str, Any], today: dt.date) -> dict[str, str]:
    verified = dt.date.fromisoformat(record["verified_at"])
    due = verified + dt.timedelta(days=record["reverify_after_days"])
    return {
        "evidence_id": record["id"],
        "verified_at": verified.isoformat(),
        "due_at": due.isoformat(),
        "status": "stale" if today > due else "current",
    }


def _open(opener: Any, request: urllib.request.Request, timeout: float) -> LinkHealth:
    with opener.open(request, timeout=timeout) as response:
        code = int(response.getcode())
        final_url = response.geturl()
        return LinkHealth(
            url=request.full_url,
            status="redirect" if final_url != request.full_url else "current",
            http_status=code,
            final_url=final_url,
        )


def check_url(url: str, opener: Any, timeout: float = 10.0) -> LinkHealth:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "operating-agent-fleets-evidence/1"})
    try:
        return _open(opener, request, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code == 405:
            get_request = urllib.request.Request(
                url, method="GET", headers={"User-Agent": "operating-agent-fleets-evidence/1"}
            )
            try:
                return _open(opener, get_request, timeout)
            except urllib.error.HTTPError as retry_exc:
                exc = retry_exc
        if exc.code in {404, 410}:
            status = "missing"
        elif exc.code == 429 or exc.code >= 500:
            status = "transient"
        else:
            status = "error"
        return LinkHealth(url=url, status=status, http_status=exc.code, final_url=None)
    except (urllib.error.URLError, TimeoutError, socket.timeout):
        return LinkHealth(url=url, status="transient", http_status=None, final_url=None)


def evaluate(root: Path, today: dt.date, *, check_links: bool, opener: Any | None = None) -> dict[str, Any]:
    validate_atlas(root)
    manifest = load_json(root / "evidence" / "manifest.yaml")
    records = [load_json(root / relative) for relative in manifest["records"]]
    record_health = [revalidation_state(record, today) for record in records]
    urls = sorted({url for record in records for url in record["public_sources"]})
    link_health = []
    if check_links:
        active_opener = opener or urllib.request.build_opener()
        link_health = [asdict(check_url(url, active_opener)) for url in urls]
    counts = {
        "records": len(records),
        "stale": sum(item["status"] == "stale" for item in record_health),
        "unique_links": len(urls),
        "missing": sum(item["status"] == "missing" for item in link_health),
        "transient": sum(item["status"] == "transient" for item in link_health),
        "errors": sum(item["status"] == "error" for item in link_health),
        "redirects": sum(item["status"] == "redirect" for item in link_health),
    }
    return {
        "checked_at": today.isoformat(),
        "network_checked": check_links,
        "summary": counts,
        "records": record_health,
        "links": link_health,
    }


def exit_code(report: dict[str, Any]) -> int:
    summary = report["summary"]
    if summary["stale"] or summary["missing"] or summary["errors"]:
        return 1
    if summary["transient"]:
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    try:
        report = evaluate(args.root.resolve(), args.today, check_links=not args.no_network)
    except (EvidenceValidationError, OSError, ValueError) as exc:
        print(f"evidence health check failed closed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
