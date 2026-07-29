#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path, PurePosixPath


STACK_DOCUMENT = ".specsfy/STACK.md"
RULES_DOCUMENT = ".specsfy/RULES.md"
DATABASE_DOCUMENT = ".specsfy/DATABASE.md"
PROJECT_DOCUMENT = "PROJECT.md"
CONTEXT_DOCUMENTS = {
    STACK_DOCUMENT,
    RULES_DOCUMENT,
    DATABASE_DOCUMENT,
    PROJECT_DOCUMENT,
}
SYSTEM_DOCUMENTATION_PREFIX = "docs/"


def git_paths(project: Path) -> list[str]:
    commands = (
        ["git", "diff", "--name-only", "-z"],
        ["git", "diff", "--cached", "--name-only", "-z"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    observed: set[str] = set()
    for command in commands:
        result = subprocess.run(
            command,
            cwd=project,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            message = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(message or f"falha ao executar {' '.join(command)}")
        observed.update(
            item.decode("utf-8", errors="replace")
            for item in result.stdout.split(b"\0")
            if item
        )
    return sorted(observed)


def normalized_paths(paths: list[str]) -> list[str]:
    return sorted(
        {
            PurePosixPath(path.replace("\\", "/")).as_posix().removeprefix("./")
            for path in paths
            if path.strip()
        }
    )


def is_stack_change(path: str) -> bool:
    name = PurePosixPath(path).name.casefold()
    structural_names = {
        "composer.json",
        "composer.lock",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lock",
        "bun.lockb",
        "pyproject.toml",
        "uv.lock",
        "requirements.txt",
        "go.mod",
        "go.sum",
        "cargo.toml",
        "cargo.lock",
        "dockerfile",
        "compose.yaml",
        "compose.yml",
        "docker-compose.yml",
    }
    return (
        name in structural_names
        or name.startswith("next.config.")
        or name.startswith("astro.config.")
        or name.startswith("vite.config.")
    )


def is_database_change(path: str) -> bool:
    pure = PurePosixPath(path)
    parts = {part.casefold() for part in pure.parts}
    name = pure.name.casefold()
    persistence_parts = {
        "db",
        "database",
        "databases",
        "migration",
        "migrations",
        "prisma",
    }
    model_parts = {"models", "entities"}
    return (
        bool(parts & persistence_parts)
        or name == "schema.prisma"
        or name.startswith("drizzle.config.")
        or path.casefold().endswith(".sql")
        or (
            bool(parts & model_parts)
            and pure.parts[0].casefold() in {"app", "src", "server"}
        )
        or (
            len(pure.parts) >= 2
            and pure.parts[0].casefold() == "app"
            and pure.parts[1].casefold() == "models"
        )
    )


def is_application_change(path: str) -> bool:
    pure = PurePosixPath(path)
    if not pure.parts:
        return False
    parts = {part.casefold() for part in pure.parts}
    if parts & {"test", "tests", "spec", "specs", "fixtures"}:
        return False
    roots = {
        "api",
        "app",
        "components",
        "lib",
        "pages",
        "resources",
        "routes",
        "server",
        "src",
    }
    code_suffixes = {
        ".php",
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".vue",
        ".astro",
        ".rb",
        ".go",
        ".rs",
    }
    return pure.parts[0].casefold() in roots and pure.suffix.casefold() in code_suffixes


def is_rules_change(path: str) -> bool:
    name = PurePosixPath(path).name.casefold()
    return (
        name in {"agents.md", "claude.md", ".editorconfig"}
        or name.startswith(("eslint.config.", "biome.json", "phpstan.", "pint.json"))
    )


def analyze(
    paths: list[str],
    *,
    acknowledge_project_no_change: bool,
    acknowledge_rules_no_change: bool,
) -> dict[str, object]:
    changed = normalized_paths(paths)
    inspected = [path for path in changed if path not in CONTEXT_DOCUMENTS]
    stack_changes = [path for path in inspected if is_stack_change(path)]
    database_changes = [path for path in inspected if is_database_change(path)]
    application_changes = [path for path in inspected if is_application_change(path)]
    rules_changes = [path for path in inspected if is_rules_change(path)]
    documentation_changes = [
        path for path in changed if path.startswith(SYSTEM_DOCUMENTATION_PREFIX)
    ]

    pending: list[dict[str, object]] = []
    if stack_changes and STACK_DOCUMENT not in changed:
        pending.append(
            {
                "document": STACK_DOCUMENT,
                "skill": "specsfy-aux-stack",
                "reason": "stack estrutural alterado",
                "evidence": stack_changes,
            }
        )
    if database_changes and DATABASE_DOCUMENT not in changed:
        pending.append(
            {
                "document": DATABASE_DOCUMENT,
                "skill": "specsfy-aux-database",
                "reason": "persistência alterada",
                "evidence": database_changes,
            }
        )
    project_review_required = bool(application_changes)
    if (
        project_review_required
        and PROJECT_DOCUMENT not in changed
        and not acknowledge_project_no_change
    ):
        pending.append(
            {
                "document": PROJECT_DOCUMENT,
                "skill": "specsfy-setup",
                "reason": "mudança de aplicação exige revisão narrativa",
                "evidence": application_changes,
            }
        )
    rules_review_required = bool(rules_changes)
    if (
        rules_review_required
        and RULES_DOCUMENT not in changed
        and not acknowledge_rules_no_change
    ):
        pending.append(
            {
                "document": RULES_DOCUMENT,
                "skill": "specsfy-aux-rules",
                "reason": "instrução ou convenção alterada exige revisão",
                "evidence": rules_changes,
            }
        )
    documentation_review_required = bool(application_changes or database_changes)
    if documentation_review_required and not documentation_changes:
        pending.append(
            {
                "document": "docs/",
                "skill": "specsfy-documentator",
                "reason": "aplicação ou persistência alterada exige reconstrução documental",
                "evidence": sorted(set(application_changes + database_changes)),
            }
        )
    return {
        "changed_paths": changed,
        "stack_changes": stack_changes,
        "database_changes": database_changes,
        "application_changes": application_changes,
        "rules_changes": rules_changes,
        "documentation_changes": documentation_changes,
        "project_review_required": project_review_required,
        "project_review_acknowledged": acknowledge_project_no_change,
        "rules_review_required": rules_review_required,
        "rules_review_acknowledged": acknowledge_rules_no_change,
        "documentation_review_required": documentation_review_required,
        "pending": pending,
        "status": "pending" if pending else "current",
    }


def render_human(report: dict[str, object]) -> str:
    lines = [f"Context monitor: {str(report['status']).upper()}"]
    pending = report["pending"]
    assert isinstance(pending, list)
    if not pending:
        lines.append("Documentação compatível com os caminhos alterados.")
    for item in pending:
        assert isinstance(item, dict)
        evidence = ", ".join(str(path) for path in item["evidence"])
        lines.append(
            f"- {item['document']} via ${item['skill']}: {item['reason']} "
            f"({evidence})"
        )
    if report["project_review_required"]:
        lines.append(
            "- PROJECT.md foi revisado ou a ausência de impacto deve ser "
            "registrada na evidência da tarefa."
        )
    if report["rules_review_required"]:
        lines.append(
            "- RULES.md foi revisado ou a ausência de nova regra deve ser "
            "registrada na evidência da tarefa."
        )
    if report["documentation_review_required"]:
        lines.append(
            "- docs/ foi reconstruído por $specsfy-documentator após a mudança."
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--paths", nargs="*")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--acknowledge-project-no-change", action="store_true")
    parser.add_argument("--acknowledge-rules-no-change", action="store_true")
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    try:
        paths = args.paths if args.paths is not None else git_paths(project)
    except RuntimeError as error:
        parser.error(str(error))
    report = analyze(
        paths,
        acknowledge_project_no_change=args.acknowledge_project_no_change,
        acknowledge_rules_no_change=args.acknowledge_rules_no_change,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_human(report))
    return 1 if args.check and report["pending"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
