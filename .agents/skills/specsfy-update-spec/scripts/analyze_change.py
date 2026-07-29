#!/usr/bin/env python3
"""Projeta o impacto de uma atualização entre uma spec no Git e o worktree."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path


ID_LINE = re.compile(
    r"^\s*(?:-\s+\*\*|#{4,6}\s+)((?:US|FR|NFR|AC)-\d{3,})\b(?:\*\*)?[^\n]*",
    re.MULTILINE,
)
SECTION = re.compile(r"^###\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)

AREA_TITLES = {
    "definition": {
        "problema e resultado",
        "research e esclarecimentos",
        "escopo e atores",
        "principios e restricoes do projeto",
        "historias de usuario",
        "cenarios bdd de aceite",
        "requisitos",
        "decisoes",
        "definition of done",
    },
    "plan": {
        "plano tecnico",
        "modelo de dados",
        "interfaces e contratos",
        "tarefas",
        "ordem de execucao",
        "dependencias, riscos e suposicoes",
    },
    "evidence": {
        "estrategia tdd",
        "plano de testes e rastreabilidade",
        "validacoes",
    },
}


def id_map(text: str) -> dict[str, str]:
    return {
        match.group(1): " ".join(match.group(0).split())
        for match in ID_LINE.finditer(text)
    }


def normalized_title(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value).casefold()
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", without_marks).split())


def section_area(title: str) -> str:
    normalized = normalized_title(title)
    for area, titles in AREA_TITLES.items():
        if normalized in titles:
            return area
    return "unknown"


def sections(text: str) -> dict[str, tuple[int, str, str]]:
    matches = list(SECTION.finditer(text))
    result: dict[str, tuple[int, str, str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        title = normalized_title(match.group(2))
        body = text[match.end() : end].strip()
        result[title] = (int(match.group(1)), match.group(2).strip(), body)
    return result


def git_root(spec: Path) -> Path | None:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=spec.parent,
        text=True,
        capture_output=True,
        check=False,
    )
    return Path(completed.stdout.strip()).resolve() if completed.returncode == 0 else None


def base_text(spec: Path, reference: str) -> tuple[str | None, str | None]:
    root = git_root(spec)
    if root is None or not spec.is_relative_to(root):
        return None, "repositório Git indisponível"
    relative = spec.relative_to(root).as_posix()
    completed = subprocess.run(
        ["git", "show", f"{reference}:{relative}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None, f"referência-base indisponível: {reference}:{relative}"
    return completed.stdout, None


def analyze(old: str, new: str, mode: str, reference: str) -> dict[str, object]:
    before_ids = id_map(old)
    after_ids = id_map(new)
    added = sorted(set(after_ids) - set(before_ids))
    removed = sorted(set(before_ids) - set(after_ids))
    changed = sorted(
        item
        for item in set(before_ids) & set(after_ids)
        if before_ids[item] != after_ids[item]
    )
    old_sections = sections(old)
    new_sections = sections(new)
    changed_titles = sorted(
        title
        for title in set(old_sections) | set(new_sections)
        if (old_sections.get(title) or (None, None, None))[2]
        != (new_sections.get(title) or (None, None, None))[2]
    )
    changed_sections = sorted(
        {
            record[0]
            for title in changed_titles
            for record in (old_sections.get(title), new_sections.get(title))
            if record is not None
        }
    )
    changed_areas = sorted(
        {
            section_area(
                (new_sections.get(title) or old_sections.get(title) or (0, title, ""))[1]
            )
            for title in changed_titles
        }
    )
    if "definition" in changed_areas or "unknown" in changed_areas:
        reopen = "Ato I"
        invalidated = ["Definition Gate", "Plan Gate", "Delivery Gate"]
    elif "plan" in changed_areas:
        reopen = "Ato II"
        invalidated = ["Plan Gate", "Delivery Gate"]
    else:
        reopen = "Nenhum"
        invalidated = []
    common = {
        "schema_version": 1,
        "mode": mode,
        "base": reference,
        "result": "passed",
        "added": added,
        "removed": removed,
        "changed": changed,
        "errors": [],
    }
    if mode == "impact":
        common.update(
            {
                "changed_sections": changed_sections,
                "changed_areas": changed_areas,
                "reopen_from": reopen,
                "invalidated_gates": invalidated,
            }
        )
    return common


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--mode", choices=("impact", "changelog"), default="impact")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.spec.is_file():
        print("ERRO: spec inexistente.", file=sys.stderr)
        return 2
    old, error = base_text(args.spec.resolve(), args.base)
    if error:
        payload = {
            "schema_version": 1,
            "mode": args.mode,
            "result": "error",
            "base": args.base,
            "errors": [error],
        }
        print(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
            if args.json
            else f"ERRO: {error}"
        )
        return 2
    payload = analyze(old or "", args.spec.read_text(encoding="utf-8"), args.mode, args.base)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.mode == "impact":
        print(f"Impacto: reabrir de {payload['reopen_from']}")
        print("Gates: " + (", ".join(payload["invalidated_gates"]) or "nenhum"))
    else:
        for key in ("added", "removed", "changed"):
            print(f"{key}: " + (", ".join(payload[key]) or "nenhum"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
