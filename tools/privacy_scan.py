#!/usr/bin/env python3
"""Fail closed on high-confidence restricted data in publishable text files."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".css", ".html", ".js", ".json", ".md", ".mmd", ".py", ".svg",
    ".toml", ".ts", ".txt", ".yaml", ".yml",
}


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


def _rx(*parts: str, flags: int = 0) -> re.Pattern[str]:
    return re.compile("".join(parts), flags)


RULES = (
    Rule("private-key material", _rx("-----BEGIN ", "(?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    Rule("GitHub credential", _rx(r"\bgh", r"(?:p_[A-Za-z0-9]{20,}|o_[A-Za-z0-9]{20,}|u_[A-Za-z0-9]{20,}|s_[A-Za-z0-9]{20,}|r_[A-Za-z0-9]{20,}|pat_[A-Za-z0-9_]{20,})\b")),
    Rule("AWS access key", _rx(r"\bAK", r"IA[0-9A-Z]{16}\b")),
    Rule("local macOS path", _rx(r"/", r"Users/[A-Za-z0-9._-]+/")),
    Rule("local Linux path", _rx(r"/", r"home/[A-Za-z0-9._-]+/")),
    Rule("local file URL", _rx(r"\bfi", r"le://", flags=re.IGNORECASE)),
    Rule("private hostname", _rx(r"\b[A-Za-z0-9-]+\.(?:internal|local|lan)\b", flags=re.IGNORECASE)),
    Rule("private IPv4 address", _rx(r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b")),
    Rule("embedded URL credential", _rx(r"https://[^\s/:]+:[^\s/@]+@", flags=re.IGNORECASE)),
    Rule("US taxpayer identifier", _rx(r"(?<!\d)(?:\d{3}-\d{2}-\d{4}|\d{2}-\d{7})(?!\d)")),
    Rule("Ethereum address", _rx(r"\b0x[a-fA-F0-9]{40}\b")),
    Rule("Telegram locator", _rx(r"\b(?:https://t\.me/|https://api\.telegram\.org/)", flags=re.IGNORECASE)),
    Rule("Telegram chat identifier", _rx(r"\bchat[_-]?id\s*[:=]\s*-?\d{5,}\b", flags=re.IGNORECASE)),
    Rule("raw transcript envelope", _rx(r"\bBEGIN RAW TRANSCRIPT\b", flags=re.IGNORECASE)),
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str


def tracked_text_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True
    )
    files = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = root / raw.decode("utf-8", errors="strict")
        if path.suffix.lower() in TEXT_SUFFIXES and path.is_file():
            files.append(path)
    return files


def scan_paths(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ValueError(f"cannot scan {path}: {exc}") from exc
        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule in RULES:
                if rule.pattern.search(line):
                    findings.append(Finding(path=path, line=line_number, rule=rule.name))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    paths = [path.resolve() for path in args.paths] if args.paths else tracked_text_files(root)
    try:
        findings = scan_paths(paths)
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"privacy scan failed closed: {exc}", file=sys.stderr)
        return 2
    if findings:
        for finding in findings:
            try:
                display = finding.path.relative_to(root)
            except ValueError:
                display = finding.path
            print(f"{display}:{finding.line}: restricted pattern: {finding.rule}", file=sys.stderr)
        print(f"privacy scan failed: {len(findings)} finding(s); matched values are intentionally redacted", file=sys.stderr)
        return 1
    print(f"privacy scan passed: {len(paths)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
