#!/usr/bin/env python3
"""Lista e carrega somente research local indexado pela especificação."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path


def section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^####\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^####\s+|^###\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group("body") if match else ""


def project_root(spec: Path) -> Path:
    for parent in spec.parents:
        if parent.name == "specs":
            return parent.parent
    return spec.parent.parent


def markdown_anchor(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    filtered = "".join(
        character
        for character in normalized
        if character.isalnum() or character in {" ", "-", "_"}
    )
    return re.sub(r"[\s-]+", "-", filtered).strip("-")


def document_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: Counter[str] = Counter()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return anchors
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE):
        base = markdown_anchor(heading)
        suffix = counts[base]
        anchors.add(base if suffix == 0 else f"{base}-{suffix}")
        counts[base] += 1
    return anchors


def has_symlink(path: Path, root: Path) -> bool:
    current = path
    while current != root and current.is_relative_to(root):
        if current.is_symlink():
            return True
        current = current.parent
    return False


def analyze(spec: Path, emit_content: bool, max_bytes: int) -> dict[str, object]:
    text = spec.read_text(encoding="utf-8")
    root = project_root(spec).resolve()
    research = (spec.parent / "research").resolve()
    index = section(text, "Artefatos de pesquisa armazenados")
    indexed = sorted(set(re.findall(r"`([^`]*research/[^`]*)`", index)))
    errors: list[str] = []
    artifacts: list[dict[str, object]] = []
    seen: set[Path] = set()
    for raw in indexed:
        candidate = (root / raw).resolve()
        raw_candidate = root / raw
        if raw_candidate.is_symlink() or not candidate.is_relative_to(research):
            errors.append(f"caminho inseguro ou symlink: {raw}")
            continue
        paths = (
            sorted(path for path in candidate.rglob("*") if path.is_file())
            if candidate.is_dir()
            else [candidate]
        )
        for path in paths:
            if path in seen:
                continue
            seen.add(path)
            if path.is_symlink() or not path.is_relative_to(research) or not path.is_file():
                errors.append(f"artefato inexistente ou inseguro: {path}")
                continue
            size = path.stat().st_size
            item: dict[str, object] = {
                "path": str(path.relative_to(root)),
                "bytes": size,
                "truncated": size > max_bytes,
            }
            if emit_content:
                data = path.read_bytes()[:max_bytes]
                try:
                    item["content"] = data.decode("utf-8")
                except UnicodeDecodeError:
                    errors.append(f"artefato não textual: {path.relative_to(root)}")
                    item["content"] = ""
            artifacts.append(item)

    claims = []
    budgets: list[tuple[int, int]] = []
    critical_blockers: list[str] = []
    claim_pattern = re.compile(
        r"^-\s+\*\*(R-\d{3,})\*\*\s+\[(critical|high|medium|low)\]\s+(.+?)"
        r"\s+—\s+Verdict:\s+(verified|refuted|unverifiable)"
        r"\s+—\s+Confidence:\s+(high|medium|low)"
        r"\s+—\s+Evidence:\s+(\S+)"
        r"\s+—\s+Budget:\s+(\d+/\d+)\.?\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    for match in claim_pattern.finditer(section(text, "Researchs executados")):
        claim = {
            "id": match.group(1),
            "criticality": match.group(2).lower(),
            "claim": match.group(3),
            "verdict": match.group(4).lower(),
            "confidence": match.group(5).lower(),
            "evidence": match.group(6),
            "budget": match.group(7),
        }
        claims.append(claim)
        evidence_value = str(claim["evidence"])
        evidence_path, separator, anchor = evidence_value.partition("#")
        raw_evidence_candidate = spec.parent / evidence_path
        evidence_candidate = raw_evidence_candidate.resolve()
        if (
            not evidence_candidate.is_relative_to(research)
            or has_symlink(raw_evidence_candidate, spec.parent.resolve())
            or not evidence_candidate.is_file()
        ):
            errors.append(
                f"{claim['id']}: evidence local inexistente ou insegura: {evidence_path}"
            )
        elif separator and anchor not in document_anchors(evidence_candidate):
            errors.append(
                f"{claim['id']}: âncora inexistente na evidence: #{anchor}"
            )
        used_text, limit_text = str(claim["budget"]).split("/", 1)
        used, limit = int(used_text), int(limit_text)
        budgets.append((used, limit))
        if limit <= 0:
            errors.append(f"{claim['id']}: orçamento inválido ({used}/{limit})")
        elif used > limit:
            errors.append(f"{claim['id']}: orçamento excedido ({used}/{limit})")
        if claim["criticality"] == "critical" and claim["verdict"] != "verified":
            critical_blockers.append(
                f"{claim['id']}: critical claim não verificado ({claim['verdict']})"
            )
    claim_counts = Counter(str(claim["id"]) for claim in claims)
    errors.extend(
        f"{claim_id}: ID duplicado"
        for claim_id, count in sorted(claim_counts.items())
        if count > 1
    )
    budget_limits = {limit for _, limit in budgets}
    if len(budget_limits) > 1:
        errors.append("claims possuem limites de orçamento divergentes")
    elif budget_limits:
        total_limit = next(iter(budget_limits))
        total_used = sum(used for used, _ in budgets)
        if total_limit > 0 and total_used > total_limit:
            errors.append(
                f"orçamento total excedido ({total_used}/{total_limit})"
            )
    if "[critical]" in text and not claims:
        errors.append("critical claim não segue o contrato ResearchClaim")
    errors.extend(critical_blockers)
    if not indexed:
        errors.append("nenhum artefato de research indexado")
    return {
        "schema_version": 1,
        "result": "passed" if not errors else "failed",
        "artifacts": artifacts,
        "claims": claims,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--emit-content", action="store_true")
    parser.add_argument("--max-bytes", type=int, default=65536)
    args = parser.parse_args()
    if not args.spec.is_file() or args.max_bytes <= 0:
        print("ERRO: spec inexistente ou max-bytes inválido.", file=sys.stderr)
        return 2
    payload = analyze(args.spec.resolve(), args.emit_content, args.max_bytes)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Research: {payload['result'].upper()}")
        for item in payload["artifacts"]:
            suffix = " (truncado)" if item["truncated"] else ""
            print(f"- {item['path']}: {item['bytes']} bytes{suffix}")
        for error in payload["errors"]:
            print(f"ERRO: {error}")
    return 0 if payload["result"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
