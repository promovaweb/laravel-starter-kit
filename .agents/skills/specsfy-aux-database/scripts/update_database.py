#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path


START = "<!-- specsfy:database:start -->"
END = "<!-- specsfy:database:end -->"


@dataclass
class Structure:
    name: str
    kind: str
    source: str
    fields: list[str] = field(default_factory=list)
    relations: list[str] = field(default_factory=list)


def relative(path: Path, project: Path) -> str:
    return path.relative_to(project).as_posix()


def scan_laravel(project: Path) -> list[Structure]:
    structures: list[Structure] = []
    for path in sorted((project / "database" / "migrations").glob("*.php")):
        text = path.read_text(encoding="utf-8", errors="replace")
        names = re.findall(r"Schema::(?:create|table)\(\s*['\"]([^'\"]+)", text)
        for name in names:
            structure = Structure(name, "Tabela", relative(path, project))
            for column_type, column in re.findall(
                r"\$table->([A-Za-z_][A-Za-z0-9_]*)\(\s*['\"]([^'\"]+)",
                text,
            ):
                structure.fields.append(f"{column}:{column_type}")
                if column_type in {"foreignId", "foreignUuid"}:
                    structure.relations.append(column)
            if "$table->id()" in text:
                structure.fields.insert(0, "id:id")
            structures.append(structure)
    return structures


def scan_sql(project: Path) -> list[Structure]:
    structures: list[Structure] = []
    candidates = sorted(project.glob("**/*.sql"))
    for path in candidates:
        if any(part in {".git", "node_modules", "vendor"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`]?([\w.]+)[\"`]?\s*\((.*?)\);",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            structure = Structure(match.group(1), "Tabela SQL", relative(path, project))
            for line in match.group(2).split(","):
                column = re.match(r"\s*[\"`]?(\w+)[\"`]?\s+([\w()]+)", line)
                if column and column.group(1).upper() not in {"PRIMARY", "FOREIGN", "CONSTRAINT"}:
                    structure.fields.append(f"{column.group(1)}:{column.group(2)}")
            structures.append(structure)
    return structures


def scan_prisma(project: Path) -> list[Structure]:
    structures: list[Structure] = []
    for path in sorted(project.glob("**/*.prisma")):
        if "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"model\s+(\w+)\s*\{(.*?)\}", text, re.DOTALL):
            structure = Structure(match.group(1), "Model Prisma", relative(path, project))
            for line in match.group(2).splitlines():
                field_match = re.match(r"\s*(\w+)\s+([\w\[\]?]+)", line)
                if field_match:
                    structure.fields.append(
                        f"{field_match.group(1)}:{field_match.group(2)}"
                    )
            structures.append(structure)
    return structures


def scan(project: Path) -> list[Structure]:
    observed = scan_laravel(project) + scan_sql(project) + scan_prisma(project)
    unique: dict[tuple[str, str], Structure] = {}
    for structure in observed:
        key = (structure.name, structure.source)
        if key not in unique:
            unique[key] = structure
            continue
        unique[key].fields.extend(structure.fields)
        unique[key].relations.extend(structure.relations)
    return list(unique.values())


def scan_sources(project: Path) -> list[tuple[str, str, str]]:
    sources: list[tuple[str, str, str]] = []
    environment = project / ".env.example"
    if environment.is_file():
        text = environment.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"(?m)^DB_CONNECTION\s*=\s*([A-Za-z0-9_-]+)", text)
        if match:
            drivers = {
                "pgsql": "PostgreSQL",
                "postgres": "PostgreSQL",
                "postgresql": "PostgreSQL",
                "mysql": "MySQL",
                "mariadb": "MariaDB",
                "sqlite": "SQLite",
                "sqlsrv": "SQL Server",
            }
            technology = drivers.get(match.group(1).casefold(), match.group(1))
            sources.append(
                (
                    "Principal",
                    technology,
                    "`.env.example` (`DB_CONNECTION`)",
                )
            )
    for path in sorted(project.glob("**/*.prisma")):
        if "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for provider in re.findall(
            r"datasource\s+\w+\s*\{.*?provider\s*=\s*['\"]([^'\"]+)",
            text,
            flags=re.DOTALL,
        ):
            sources.append(
                (
                    "Principal",
                    provider,
                    f"`{relative(path, project)}` (`datasource`)",
                )
            )
    return list(dict.fromkeys(sources))


def safe_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def managed_block(
    structures: list[Structure],
    detected_sources: list[tuple[str, str, str]],
) -> str:
    structural_sources = sorted({structure.source for structure in structures})
    source_rows = list(detected_sources)
    source_rows.extend(
        ("Estrutura", "Schema/migration", f"`{source}`")
        for source in structural_sources
    )
    if source_rows:
        sources = "\n".join(
            f"| {safe_cell(name)} | {safe_cell(technology)} | {evidence} |"
            for name, technology, evidence in source_rows
        )
    else:
        sources = "| A confirmar | Nenhuma estrutura reconhecida | A confirmar |"
    if structures:
        rows = []
        for structure in structures:
            fields = ", ".join(dict.fromkeys(structure.fields)) or "A confirmar"
            relations = ", ".join(dict.fromkeys(structure.relations)) or "Não detectadas"
            rows.append(
                f"| {safe_cell(structure.name)} | {safe_cell(structure.kind)} | "
                f"{safe_cell(fields)} | {safe_cell(relations)} | "
                f"`{safe_cell(structure.source)}` |"
            )
        structures_table = "\n".join(rows)
    else:
        structures_table = "| A confirmar | A confirmar | A confirmar | A confirmar | A confirmar |"
    return f"""{START}
| Fonte | Tecnologia/forma | Evidência |
| --- | --- | --- |
{sources}

## Estruturas detectadas

| Estrutura | Tipo | Campos | Relações | Fonte |
| --- | --- | --- | --- | --- |
{structures_table}
{END}"""


def merge(content: str, block: str) -> str:
    if START in content and END in content:
        before, remainder = content.split(START, 1)
        _, after = remainder.split(END, 1)
        return f"{before}{block}{after}".rstrip() + "\n"
    if not content.strip():
        content = "# Banco de dados\n"
    return content.rstrip() + "\n\n## Inventário detectado\n\n" + block + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    target = project / ".specsfy" / "DATABASE.md"
    existing = target.read_text(encoding="utf-8") if target.is_file() else ""
    updated = merge(
        existing,
        managed_block(scan(project), scan_sources(project)),
    )
    if updated != existing:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(updated, encoding="utf-8")
        print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
