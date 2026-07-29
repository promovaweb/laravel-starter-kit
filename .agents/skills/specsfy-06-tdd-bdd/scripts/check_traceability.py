#!/usr/bin/env python3
"""Compara IDs definidos em spec.md com marcadores presentes nos testes."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


SKIP_DIRS = {
    ".agents",
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "build",
    "coverage",
    "dist",
    "examples",
    "fixture",
    "fixtures",
    "node_modules",
    "research",
    "samples",
    "target",
    "vendor",
}
TEST_SUFFIXES = {
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".ts",
    ".tsx",
}
ID_PATTERN = re.compile(r"\b(?:US|AC|FR|NFR)-\d{3,}\b")
TAG_PATTERN = re.compile(r"@((?:US|AC|FR|NFR)-\d{3,})\b")
TASK_PATTERN = re.compile(
    r"^- \[[ xX]\] (T\d{3,})\b.+?— Refs: (.+?) — Depends:",
    re.MULTILINE,
)
EVIDENCE_PATTERN = re.compile(
    r"^\s*<!--\s*specsfy:evidence\s+(\{.*?\})\s*-->\s*$",
    re.MULTILINE,
)
DEFINITION_PATTERNS = {
    "US": re.compile(r"^#{4,6}\s+(US-\d{3,})\b", re.MULTILINE),
    "AC": re.compile(r"^#{4,6}\s+(AC-\d{3,})\b", re.MULTILINE),
    "FR": re.compile(r"^\s*-\s+\*\*(FR-\d{3,})\*\*\s*:", re.MULTILINE),
    "NFR": re.compile(r"^\s*-\s+\*\*(NFR-\d{3,})\*\*\s*:", re.MULTILINE),
}
DEFAULT_MINIMUM_TESTS = 3


def looks_like_test(path: Path) -> bool:
    if path.suffix.lower() not in TEST_SUFFIXES:
        return False
    lowered_parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    return (
        "test" in lowered_parts
        or "tests" in lowered_parts
        or "spec" in lowered_parts
        or name.startswith("test_")
        or ".test." in name
        or ".spec." in name
        or name.endswith("_test.py")
        or name.endswith("_test.go")
    )


def test_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(directory for directory in dirs if directory not in SKIP_DIRS)
        current_path = Path(current)
        for name in sorted(names):
            path = current_path / name
            if looks_like_test(path.relative_to(root)):
                files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("test_root", type=Path)
    parser.add_argument(
        "--kinds",
        default="US,FR,NFR,AC",
        help="Tipos obrigatórios separados por vírgula (padrão: US,FR,NFR,AC)",
    )
    parser.add_argument(
        "--minimum-tests",
        type=int,
        default=DEFAULT_MINIMUM_TESTS,
        help=(
            "Casos TDD mínimos por feature, US, FR e NFR "
            f"(padrão: {DEFAULT_MINIMUM_TESTS}; AC exige um)"
        ),
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--full-chain",
        action="store_true",
        help="Exigir requisito → teste → tarefa → evidência estruturada.",
    )
    args = parser.parse_args()

    spec_path = args.spec.resolve()
    root = args.test_root.resolve()
    if not spec_path.is_file() or not root.is_dir():
        print("ERRO: spec ou raiz de testes inexistente.", file=sys.stderr)
        return 2

    kinds = [kind.strip().upper() for kind in args.kinds.split(",") if kind.strip()]
    invalid_kinds = [kind for kind in kinds if kind not in DEFINITION_PATTERNS]
    if invalid_kinds:
        print(f"ERRO: tipos inválidos: {', '.join(invalid_kinds)}", file=sys.stderr)
        return 2
    if args.minimum_tests < 1:
        print("ERRO: --minimum-tests deve ser maior que zero.", file=sys.stderr)
        return 2

    spec_text = spec_path.read_text(encoding="utf-8")
    defined_by_kind = {
        kind: set(pattern.findall(spec_text))
        for kind, pattern in DEFINITION_PATTERNS.items()
    }
    required = set().union(*(defined_by_kind[kind] for kind in kinds))
    all_defined = set().union(*defined_by_kind.values())

    locations: dict[str, list[str]] = {}
    case_records: list[tuple[str, int, set[str]]] = []
    scanned = test_files(root)
    for path in scanned:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            marked: set[str] = set()
            marker = re.search(r"SPECSFY\s*:\s*(.*)$", line, re.IGNORECASE)
            if marker:
                marked.update(ID_PATTERN.findall(marker.group(1)))
            marked.update(TAG_PATTERN.findall(line))
            if not marked:
                continue
            relative = str(path.relative_to(root))
            case_records.append((relative, line_number, marked))
            location = f"{relative}:{line_number}"
            for item in marked:
                locations.setdefault(item, []).append(location)

    covered = set(locations)
    effectively_covered = covered
    uncovered = sorted(required - effectively_covered)
    required_case_counts = {
        item: 1 if item.startswith("AC-") else args.minimum_tests
        for item in required
    }
    case_counts = {item: len(locations.get(item, [])) for item in sorted(required)}
    insufficient_cases = {
        item: required_case_counts[item] - case_counts[item]
        for item in sorted(required)
        if case_counts[item] < required_case_counts[item]
    }
    feature_cases = sum(
        1 for _, _, marked in case_records if marked & all_defined
    )
    feature_cases_missing = max(0, args.minimum_tests - feature_cases)
    globally_defined = set(all_defined)
    candidate_specs = {
        candidate
        for pattern in ("specs/specs/*/spec.md", "specs/*/spec.md")
        for candidate in root.glob(pattern)
        if candidate.is_file()
    }
    for candidate_spec in sorted(candidate_specs):
        try:
            candidate_text = candidate_spec.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for pattern in DEFINITION_PATTERNS.values():
            globally_defined.update(pattern.findall(candidate_text))
    orphan = sorted(covered - globally_defined)
    task_locations: dict[str, list[str]] = {}
    for task_id, refs_text in TASK_PATTERN.findall(spec_text):
        for item in ID_PATTERN.findall(refs_text):
            task_locations.setdefault(item, []).append(task_id)
    evidence_locations: dict[str, list[str]] = {}
    evidence_errors: list[str] = []
    for raw in EVIDENCE_PATTERN.findall(spec_text):
        try:
            evidence = json.loads(raw)
        except json.JSONDecodeError as error:
            evidence_errors.append(f"JSON inválido: {error.msg}")
            continue
        task_id = evidence.get("task")
        refs = evidence.get("refs")
        if not isinstance(task_id, str) or not isinstance(refs, list):
            evidence_errors.append("evidence sem task/refs válidos")
            continue
        for item in refs:
            if isinstance(item, str):
                evidence_locations.setdefault(item, []).append(task_id)
    broken_chains: list[dict[str, object]] = []
    if args.full_chain:
        for item in sorted(required):
            missing: list[str] = []
            if item in insufficient_cases:
                if case_counts[item] == 0:
                    missing.append("test")
                else:
                    missing.append(f"test-cases:{insufficient_cases[item]}")
            if item not in task_locations:
                missing.append("task")
            if item not in evidence_locations:
                missing.append("evidence")
            if missing:
                broken_chains.append({"id": item, "missing": missing})
        broken_chains.extend(
            {"id": "evidence", "missing": [error]} for error in evidence_errors
        )
    result = {
        "spec": str(spec_path),
        "root": str(root),
        "kinds": kinds,
        "files_scanned": len(scanned),
        "required_cases": args.minimum_tests,
        "feature_cases": feature_cases,
        "feature_cases_missing": feature_cases_missing,
        "required": len(required),
        "covered": len(required & effectively_covered),
        "uncovered": uncovered,
        "case_counts": case_counts,
        "insufficient_cases": insufficient_cases,
        "orphan_markers": orphan,
        "task_locations": {
            key: sorted(set(value)) for key, value in sorted(task_locations.items())
        },
        "evidence_locations": {
            key: sorted(set(value))
            for key, value in sorted(evidence_locations.items())
        },
        "broken_chains": broken_chains,
        "locations": {key: sorted(value) for key, value in sorted(locations.items())},
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"Rastreabilidade: {result['covered']}/{result['required']} IDs cobertos "
            f"em {result['files_scanned']} arquivos de teste."
        )
        if uncovered:
            print("SEM TESTE: " + ", ".join(uncovered))
        for item, missing in insufficient_cases.items():
            print(
                f"CASOS TDD INSUFICIENTES {item}: "
                f"{case_counts[item]}/{required_case_counts[item]} "
                f"(faltam {missing})"
            )
        if feature_cases_missing:
            print(
                "CASOS TDD INSUFICIENTES FEATURE: "
                f"{feature_cases}/{args.minimum_tests} "
                f"(faltam {feature_cases_missing})"
            )
        if orphan:
            print("MARCADORES ÓRFÃOS: " + ", ".join(orphan))
        for broken in broken_chains:
            print(
                f"CADEIA QUEBRADA {broken['id']}: "
                + ", ".join(broken["missing"])
            )
        print(
            "RESULTADO: OK"
            if not insufficient_cases
            and not feature_cases_missing
            and not orphan
            and not broken_chains
            else "RESULTADO: GAPS"
        )
    return (
        1
        if insufficient_cases
        or feature_cases_missing
        or orphan
        or broken_chains
        else 0
    )


if __name__ == "__main__":
    sys.exit(main())
