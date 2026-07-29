#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


def add_rule(content: str, section: str, rule: str) -> str:
    normalized_rule = rule.strip().removeprefix("-").strip()
    if not normalized_rule:
        raise ValueError("a regra não pode estar vazia")
    if normalized_rule.casefold() in content.casefold():
        return content
    if not content.strip():
        content = "# Regras do sistema\n"
    heading = f"## {section.strip()}"
    match = re.search(
        rf"(?m)^{re.escape(heading)}\s*$",
        content,
        flags=re.IGNORECASE,
    )
    line = f"- {normalized_rule}"
    if match is None:
        return content.rstrip() + f"\n\n{heading}\n\n{line}\n"
    next_heading = re.search(r"(?m)^##\s+", content[match.end():])
    insertion = (
        match.end() + next_heading.start()
        if next_heading is not None
        else len(content)
    )
    before = content[:insertion].rstrip()
    after = content[insertion:].lstrip("\n")
    result = before + f"\n\n{line}\n"
    if after:
        result += "\n" + after
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--section", required=True)
    parser.add_argument("--rule", required=True)
    args = parser.parse_args()
    target = args.project.expanduser().resolve() / ".specsfy" / "RULES.md"
    existing = target.read_text(encoding="utf-8") if target.is_file() else ""
    try:
        updated = add_rule(existing, args.section, args.rule)
    except ValueError as error:
        parser.error(str(error))
    if updated != existing:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(updated, encoding="utf-8")
        print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
