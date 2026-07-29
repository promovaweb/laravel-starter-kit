#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


START = "<!-- specsfy:stack:start -->"
END = "<!-- specsfy:stack:end -->"


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def scan(project: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    composer = load_json(project / "composer.json")
    composer_packages = {**composer.get("require", {}), **composer.get("require-dev", {})}
    composer_map = {
        "laravel/framework": ("Framework", "Laravel"),
        "php": ("Linguagem", "PHP"),
        "pestphp/pest": ("Testes", "Pest"),
        "phpunit/phpunit": ("Testes", "PHPUnit"),
    }
    for package, (kind, label) in composer_map.items():
        if package in composer_packages:
            rows.append((kind, label, f"`composer.json` (`{package}`)"))
    if composer and not any(row[1] == "PHP" for row in rows):
        rows.append(("Linguagem", "PHP", "`composer.json`"))

    package = load_json(project / "package.json")
    packages = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    package_map = {
        "next": ("Framework", "Next.js"),
        "astro": ("Framework", "Astro"),
        "react": ("Biblioteca", "React"),
        "typescript": ("Linguagem", "TypeScript"),
        "vitest": ("Testes", "Vitest"),
        "prisma": ("Persistência", "Prisma"),
        "@prisma/client": ("Persistência", "Prisma Client"),
        "drizzle-orm": ("Persistência", "Drizzle ORM"),
    }
    for dependency, (kind, label) in package_map.items():
        if dependency in packages:
            rows.append((kind, label, f"`package.json` (`{dependency}`)"))
    if package:
        rows.append(("Runtime", "Node.js", "`package.json`"))
    if (project / "docker-compose.yml").is_file() or (project / "compose.yaml").is_file():
        rows.append(("Infraestrutura", "Containers", "arquivo Compose"))
    return list(dict.fromkeys(rows))


def managed_block(rows: list[tuple[str, str, str]]) -> str:
    if not rows:
        rows = [("Framework", "A confirmar", "Nenhum manifest reconhecido")]
    body = "\n".join(
        f"| {kind} | {technology} | {evidence} |"
        for kind, technology, evidence in rows
    )
    return (
        f"{START}\n"
        "| Camada | Tecnologia | Evidência |\n"
        "| --- | --- | --- |\n"
        f"{body}\n{END}"
    )


def existing_rows(content: str) -> list[tuple[str, str, str]]:
    if START not in content or END not in content:
        return []
    section = content.split(START, 1)[1].split(END, 1)[0]
    rows: list[tuple[str, str, str]] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if len(cells) != 3:
            continue
        if cells[0] in {"Camada", "---"}:
            continue
        rows.append(cells)
    return rows


def merge(content: str, block: str) -> str:
    if START in content and END in content:
        before, remainder = content.split(START, 1)
        _, after = remainder.split(END, 1)
        return f"{before}{block}{after}".rstrip() + "\n"
    if not content.strip():
        content = "# Stack do sistema\n"
    return (
        content.rstrip()
        + "\n\n## Inventário detectado\n\n"
        + block
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    target = project / ".specsfy" / "STACK.md"
    existing = target.read_text(encoding="utf-8") if target.is_file() else ""
    rows = list(dict.fromkeys([*scan(project), *existing_rows(existing)]))
    updated = merge(existing, managed_block(rows))
    if updated != existing:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(updated, encoding="utf-8")
        print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
