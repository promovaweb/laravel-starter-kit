#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


START = "<!-- specsfy:framework:start -->"
END = "<!-- specsfy:framework:end -->"
SPEC_PATH_TOKEN = "{{SPECSFY_SPEC_PATH}}"


def json_object(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def detected_stack(project: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    composer = json_object(project / "composer.json")
    composer_packages = {
        **composer.get("require", {}),
        **composer.get("require-dev", {}),
    }
    if "laravel/framework" in composer_packages:
        rows.append(("Framework", "Laravel", "`composer.json`"))
    if composer:
        rows.append(("Linguagem", "PHP", "`composer.json`"))

    package = json_object(project / "package.json")
    packages = {
        **package.get("dependencies", {}),
        **package.get("devDependencies", {}),
    }
    if "next" in packages:
        rows.append(("Framework", "Next.js", "`package.json`"))
    if "astro" in packages:
        rows.append(("Framework", "Astro", "`package.json`"))
    if "react" in packages:
        rows.append(("Biblioteca", "React", "`package.json`"))
    if package:
        rows.append(("Runtime", "Node.js", "`package.json`"))
    return list(dict.fromkeys(rows))


def stack_label(rows: list[tuple[str, str, str]]) -> str:
    frameworks = [technology for kind, technology, _ in rows if kind == "Framework"]
    return ", ".join(frameworks) if frameworks else "stack ainda não identificado"


def model_guidance(rows: list[tuple[str, str, str]]) -> str:
    frameworks = {technology for kind, technology, _ in rows if kind == "Framework"}
    guidance: list[str] = []
    if "Laravel" in frameworks:
        guidance.append(
            "Para Laravel, descreva módulos de domínio, fronteiras HTTP/console e "
            "use `database/migrations` como primeira evidência do mapa de dados."
        )
    if "Next.js" in frameworks:
        guidance.append(
            "Para Next.js, explicite App Router, Server Components, Client "
            "Components e fronteiras entre servidor e navegador."
        )
    if "Astro" in frameworks:
        guidance.append(
            "Para Astro, explicite páginas, conteúdo, integrações e as ilhas "
            "interativas hidratadas no cliente."
        )
    if not guidance:
        guidance.append(
            "Confirme os manifests e as fronteiras principais antes de completar "
            "o modelo genérico."
        )
    return "\n\n".join(guidance)


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def merge_block(path: Path, block: str) -> bool:
    content = path.read_text(encoding="utf-8") if path.is_file() else ""
    if START in content and END in content:
        before, remainder = content.split(START, 1)
        _, after = remainder.split(END, 1)
        updated = f"{before}{block}{after}".rstrip() + "\n"
    else:
        updated = content.rstrip()
        if updated:
            updated += "\n\n"
        updated += block.rstrip() + "\n"
    if updated == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")
    return True


def framework_blocks() -> tuple[str, str]:
    reference = (
        Path(__file__).resolve().parents[1]
        / "references"
        / "framework-instructions.md"
    )
    reference_content = reference.read_text(encoding="utf-8")
    agents = (
        START
        + reference_content.split(START, 1)[1].split(END, 1)[0]
        + END
    ).replace(
        SPEC_PATH_TOKEN,
        ".specsfy/Spec.md",
    )
    claude = f"{START}\n@.specsfy/Spec.md\n{END}"
    return agents, claude


PROJECT_TEMPLATE_PATH = Path(".specsfy/templates/Project.md")
STACK_TEMPLATE_PATH = Path(".specsfy/templates/Stack.md")
RULES_TEMPLATE_PATH = Path(".specsfy/templates/Rules.md")
DATABASE_TEMPLATE_PATH = Path(".specsfy/templates/Database.md")
SOURCE_TEMPLATES = Path(__file__).resolve().parents[2] / "templates"
CUSTOM_TEMPLATES = Path(".specsfy/templates/custom")


def render_template(
    project: Path,
    installed_path: Path,
    replacements: dict[str, str],
) -> str:
    installed = project / installed_path
    custom = project / CUSTOM_TEMPLATES / installed_path.name
    source = SOURCE_TEMPLATES / installed_path.name
    template = next(
        (
            candidate
            for candidate in (custom, installed, source)
            if candidate.is_file()
        ),
        None,
    )
    if template is None:
        raise FileNotFoundError(
            f"template não encontrado: {installed}; execute `specsfy install`"
        )
    content = template.read_text(encoding="utf-8")
    for token, value in replacements.items():
        if token not in content:
            raise ValueError(f"token obrigatório ausente em {template}: {token}")
        content = content.replace(token, value)
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", content)))
    if unresolved:
        raise ValueError(
            f"tokens não preenchidos em {template}: {', '.join(unresolved)}"
        )
    return content


def project_template(project: Path, label: str, guidance: str) -> str:
    return render_template(
        project,
        PROJECT_TEMPLATE_PATH,
        {"{{STACK_LABEL}}": label, "{{STACK_GUIDANCE}}": guidance},
    )


def stack_template(project: Path, rows: list[tuple[str, str, str]]) -> str:
    rendered = rows or [
        ("Framework", "A confirmar", "Nenhum manifest reconhecido"),
    ]
    table = "\n".join(f"| {kind} | {technology} | {source} |" for kind, technology, source in rendered)
    return render_template(project, STACK_TEMPLATE_PATH, {"{{STACK_ROWS}}": table})


def rules_template(project: Path, label: str, guidance: str) -> str:
    return render_template(
        project,
        RULES_TEMPLATE_PATH,
        {"{{STACK_LABEL}}": label, "{{STACK_GUIDANCE}}": guidance},
    )


def database_template(project: Path, label: str, guidance: str) -> str:
    return render_template(
        project,
        DATABASE_TEMPLATE_PATH,
        {"{{STACK_LABEL}}": label, "{{STACK_GUIDANCE}}": guidance},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    project.mkdir(parents=True, exist_ok=True)
    rows = detected_stack(project)
    label = stack_label(rows)
    guidance = model_guidance(rows)
    targets = {
        project / "PROJECT.md": project_template(project, label, guidance),
        project / ".specsfy" / "STACK.md": stack_template(project, rows),
        project / ".specsfy" / "RULES.md": rules_template(project, label, guidance),
        project / ".specsfy" / "DATABASE.md": database_template(
            project, label, guidance
        ),
    }
    changed = [path for path, content in targets.items() if write_if_missing(path, content)]
    agents_block, claude_block = framework_blocks()
    if merge_block(project / "AGENTS.md", agents_block):
        changed.append(project / "AGENTS.md")
    if merge_block(project / "CLAUDE.md", claude_block):
        changed.append(project / "CLAUDE.md")
    for path in changed:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
