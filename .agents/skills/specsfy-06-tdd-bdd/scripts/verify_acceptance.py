#!/usr/bin/env python3
"""Audita se cada AC possui resultado de QA na matriz de rastreabilidade."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def section(text: str) -> str:
    match = re.search(
        r"^###\s+12\.\s+Plano de testes e rastreabilidade\s*$\n(.*?)(?=^###\s+13\.|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else ""


def analyze(text: str, attestation_path: Path | None = None) -> dict[str, object]:
    criteria = sorted(set(re.findall(r"^####\s+(AC-\d{3,})\b", text, re.MULTILINE)))
    rows: dict[str, dict[str, str]] = {}
    for line in section(text).splitlines():
        if not line.lstrip().startswith("|") or re.match(r"^\s*\|\s*-", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0].casefold() == "requisito":
            continue
        for criterion in re.findall(r"\bAC-\d{3,}\b", cells[1]):
            rows.setdefault(
                criterion,
                {
                    "level": cells[2],
                    "command": cells[3],
                    "evidence": cells[4],
                },
            )
    missing = [
        criterion
        for criterion in criteria
        if criterion not in rows
        or not re.search(r"\bPassed\b", rows[criterion]["evidence"], re.IGNORECASE)
    ]
    errors: list[str] = []
    attested = False
    if attestation_path is not None:
        attested = True
        try:
            attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"atestação inválida: {error}")
            attestation = {}
        slug_match = re.search(
            r"^\|\s*Slug\s*\|\s*(\S+)\s*\|\s*$",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
        slug = slug_match.group(1) if slug_match else ""
        expected_name = f"acceptance:{slug}"
        if attestation.get("schema_version") != 2:
            errors.append("atestação exige schema_version 2")
        if attestation.get("result") != "passed":
            errors.append("atestação não possui result passed")
        checks = attestation.get("checks")
        matches = (
            [
                check
                for check in checks
                if isinstance(check, dict) and check.get("name") == expected_name
            ]
            if isinstance(checks, list)
            else []
        )
        if len(matches) != 1:
            errors.append(f"{expected_name}: check atestado ausente ou duplicado")
        else:
            check = matches[0]
            if check.get("status") != "passed" or check.get("code") != 0:
                errors.append(f"{expected_name}: check atestado não passou")
            try:
                detail = json.loads(str(check.get("detail", "")))
            except json.JSONDecodeError:
                errors.append(f"{expected_name}: detail não contém JSON válido")
                detail = {}
            observed = detail.get("criteria")
            if (
                detail.get("result") != "passed"
                or detail.get("missing")
                or not isinstance(observed, list)
                or sorted(observed) != criteria
            ):
                errors.append(f"{expected_name}: cobertura atestada dos ACs diverge")
    all_missing = sorted(set(missing + criteria if errors and not missing else missing))
    return {
        "schema_version": 1,
        "result": "passed" if not missing and not errors else "failed",
        "criteria": criteria,
        "results": rows,
        "missing": all_missing,
        "attested": attested,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("root", type=Path)
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.spec.is_file() or not args.root.is_dir():
        print("ERRO: spec ou raiz inexistente.", file=sys.stderr)
        return 2
    payload = analyze(
        args.spec.read_text(encoding="utf-8"),
        args.attestation.resolve() if args.attestation else None,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"QA: {payload['result'].upper()}")
        if payload["missing"]:
            print("AC SEM RESULTADO: " + ", ".join(payload["missing"]))
        for error in payload["errors"]:
            print("ERRO: " + error)
    return 0 if payload["result"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
