#!/usr/bin/env python3
"""Valida findings de produto, arquitetura e segurança registrados na spec."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
from pathlib import Path


FINDING = re.compile(
    r"^-\s+\*\*(FIND-(PROD|ARCH|SEC)-\d{3,})\*\*"
    r"\s+\[(P[123])\]\s+\[(Open|Resolved|Accepted)\]\s+(.+?)"
    r"\s+—\s+Refs:\s+(.+?)"
    r"\s+—\s+Evidence:\s+(.+?)"
    r"\s+—\s+Effect:\s+(.+?)"
    r"\s+—\s+Suggestion:\s+(.+?)\s*$",
    re.MULTILINE,
)
DEFINED = re.compile(
    r"^(?:####\s+((?:US|AC)-\d{3,})\b|-\s+\*\*((?:FR|NFR)-\d{3,})\*\*\s*:)",
    re.MULTILINE,
)


def has_symlink(path: Path, root: Path) -> bool:
    current = path
    while current != root and current.is_relative_to(root):
        if current.is_symlink():
            return True
        current = current.parent
    return False


def analyze(text: str, root: Path | None = None) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    for match in FINDING.finditer(text):
        findings.append(
            {
                "id": match.group(1),
                "lens": match.group(2).lower(),
                "severity": match.group(3),
                "status": match.group(4),
                "description": match.group(5),
                "refs": match.group(6),
                "evidence": match.group(7),
                "effect": match.group(8),
                "suggestion": match.group(9),
            }
        )
    declared = set(
        re.findall(
            r"^\s*-\s+\*\*(FIND-(?:PROD|ARCH|SEC)-\d{3,})\*\*",
            text,
            re.MULTILINE,
        )
    )
    parsed = {item["id"] for item in findings}
    errors = [f"{item}: formato inválido" for item in sorted(declared - parsed)]
    counts = Counter(str(item["id"]) for item in findings)
    errors.extend(
        f"{finding_id}: ID duplicado"
        for finding_id, count in sorted(counts.items())
        if count > 1
    )
    definitions = {
        value
        for match in DEFINED.finditer(text)
        for value in match.groups()
        if value
    }
    root_real = root.resolve() if root is not None else None
    for item in findings:
        refs = sorted(set(re.findall(r"\b(?:US|FR|NFR|AC)-\d{3,}\b", item["refs"])))
        invalid_refs = sorted(set(refs) - definitions)
        if not refs:
            errors.append(f"{item['id']}: refs ausentes")
        elif invalid_refs:
            errors.append(
                f"{item['id']}: refs inexistentes: {', '.join(invalid_refs)}"
            )
        if root_real is not None:
            locator = item["evidence"].strip()
            path_text = re.sub(r"(?::\d+|#.+)$", "", locator)
            raw_candidate = root_real / path_text
            candidate = raw_candidate.resolve()
            if (
                "://" in locator
                or locator.startswith("manual:")
                or not candidate.is_relative_to(root_real)
                or has_symlink(raw_candidate, root_real)
                or not candidate.is_file()
            ):
                errors.append(
                    f"{item['id']}: evidence local inexistente ou insegura: {locator}"
                )
    blocking = [
        item["id"]
        for item in findings
        if item["severity"] == "P1" and item["status"] == "Open"
    ]
    return {
        "schema_version": 1,
        "result": "passed" if not errors and not blocking else "failed",
        "findings": findings,
        "blocking": blocking,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.spec.is_file():
        print("ERRO: spec inexistente.", file=sys.stderr)
        return 2
    spec = args.spec.resolve()
    inferred_root = next(
        (parent.parent for parent in spec.parents if parent.name == "specs"),
        spec.parent,
    )
    payload = analyze(
        spec.read_text(encoding="utf-8"),
        args.root.resolve() if args.root else inferred_root.resolve(),
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Reviews: {payload['result'].upper()}")
        for item in payload["findings"]:
            print(f"- {item['id']} [{item['severity']}] [{item['status']}]")
        for item in payload["blocking"]:
            print(f"BLOCKER: {item}")
        for error in payload["errors"]:
            print(f"ERRO: {error}")
    return 0 if payload["result"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
