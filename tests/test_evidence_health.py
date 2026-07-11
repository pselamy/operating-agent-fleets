from __future__ import annotations

import datetime as dt
import io
import json
import unittest
import urllib.error
from unittest import mock

from tools.check_evidence_health import LinkHealth, check_url, evaluate, exit_code, main, revalidation_state
from tools.validate_evidence import ROOT


class FakeResponse:
    def __init__(self, code: int = 200, final_url: str = "https://example.com/source") -> None:
        self.code = code
        self.final_url = final_url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self) -> int:
        return self.code

    def geturl(self) -> str:
        return self.final_url


class FakeOpener:
    def __init__(self, *results) -> None:
        self.results = list(results)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.com/source", code, "synthetic", {}, None)


class EvidenceHealthTests(unittest.TestCase):
    def test_revalidation_current_and_stale(self) -> None:
        record = {"id": "artifact.synthetic", "verified_at": "2026-07-01", "reverify_after_days": 7}
        self.assertEqual(revalidation_state(record, dt.date(2026, 7, 8))["status"], "current")
        self.assertEqual(revalidation_state(record, dt.date(2026, 7, 9))["status"], "stale")

    def test_current_and_redirect_links(self) -> None:
        current = check_url("https://example.com/source", FakeOpener(FakeResponse()))
        redirected = check_url(
            "https://example.com/old", FakeOpener(FakeResponse(final_url="https://example.com/new"))
        )
        self.assertEqual(current.status, "current")
        self.assertEqual(redirected.status, "redirect")

    def test_head_not_allowed_retries_get(self) -> None:
        opener = FakeOpener(http_error(405), FakeResponse())
        self.assertEqual(check_url("https://example.com/source", opener).status, "current")
        self.assertEqual([request.method for request, _ in opener.requests], ["HEAD", "GET"])

    def test_missing_transient_and_permanent_errors(self) -> None:
        cases = ((404, "missing"), (410, "missing"), (429, "transient"), (503, "transient"), (403, "error"))
        for code, expected in cases:
            with self.subTest(code=code):
                self.assertEqual(check_url("https://example.com/source", FakeOpener(http_error(code))).status, expected)

    def test_network_exception_is_transient(self) -> None:
        error = urllib.error.URLError("synthetic outage")
        self.assertEqual(check_url("https://example.com/source", FakeOpener(error)).status, "transient")

    def test_evaluate_without_network_deduplicates_links(self) -> None:
        report = evaluate(ROOT, dt.date(2026, 7, 11), check_links=False)
        expected = {
            url
            for relative in json.loads((ROOT / "evidence" / "manifest.yaml").read_text())["records"]
            for url in json.loads((ROOT / relative).read_text())["public_sources"]
        }
        self.assertEqual(report["summary"]["unique_links"], len(expected))
        self.assertEqual(report["summary"]["stale"], 0)

    def test_exit_codes_distinguish_transient_from_confirmed_failure(self) -> None:
        base = {"stale": 0, "missing": 0, "errors": 0, "transient": 0}
        self.assertEqual(exit_code({"summary": base}), 0)
        self.assertEqual(exit_code({"summary": {**base, "transient": 1}}), 2)
        self.assertEqual(exit_code({"summary": {**base, "missing": 1}}), 1)

    def test_cli_offline_passes(self) -> None:
        output = io.StringIO()
        with mock.patch("sys.argv", ["check_evidence_health.py", "--root", str(ROOT), "--today", "2026-07-11", "--no-network"]), mock.patch("sys.stdout", output):
            self.assertEqual(main(), 0)
        self.assertFalse(json.loads(output.getvalue())["network_checked"])


if __name__ == "__main__":
    unittest.main()
