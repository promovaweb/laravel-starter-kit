#!/usr/bin/env python3
"""Inicializa um item de backlog minimamente completo sob a raiz escolhida."""

from __future__ import annotations

import argparse
import fcntl
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path


FILE_PATTERN = re.compile(r"^(?P<number>\d{4})-.*\.md$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NUMBER = 9999
MODEL_PATH = Path(".specsfy/templates/Backlog.md")
CUSTOM_MODEL_PATH = Path(".specsfy/templates/custom/Backlog.md")
SOURCE_MODEL_PATH = Path(__file__).resolve().parents[2] / "templates" / "Backlog.md"


class InitializationError(ValueError):
    """Representa entrada ou estado que impede inicialização segura."""


def normalized_title(raw_title: str) -> str:
    title = raw_title.strip()
    if not title:
        raise InitializationError("o título não pode ficar vazio")
    if any(character in title for character in "\r\n"):
        raise InitializationError("o título deve ocupar uma única linha")
    return title


def required_text(raw_value: str, field: str) -> str:
    value = raw_value.strip()
    if not value:
        raise InitializationError(f"{field} não pode ficar vazio")
    return value


def slugify(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")
    if not slug:
        raise InitializationError(
            "o título deve conter ao menos um caractere alfanumérico"
        )
    return slug


def validated_slug(raw_slug: str | None, title: str) -> str:
    if raw_slug is None:
        return slugify(title)
    slug = raw_slug.strip()
    if not SLUG_PATTERN.fullmatch(slug):
        raise InitializationError(
            f"slug inválido {raw_slug!r}; utilize caracteres ASCII em kebab-case"
        )
    return slug


def project_root(raw_root: str | None) -> Path:
    root = Path.cwd() if raw_root is None else Path(raw_root).expanduser()
    root = root.resolve()
    if not root.exists():
        raise InitializationError(f"a raiz não existe: {root}")
    if not root.is_dir():
        raise InitializationError(f"a raiz não é um diretório: {root}")
    return root


def next_number(backlog_directory: Path) -> int:
    numbers = []
    for child in backlog_directory.iterdir():
        match = FILE_PATTERN.match(child.name)
        if child.is_file() and match:
            numbers.append(int(match.group("number")))
    number = max(numbers, default=0) + 1
    if number > MAX_NUMBER:
        raise InitializationError(
            f"a sequência em {backlog_directory} atingiu {MAX_NUMBER:04d}"
        )
    return number


def render_model(
    *,
    root: Path,
    number: int,
    title: str,
    idea: str,
    problem: str,
    person: str,
    result: str,
    context: str,
) -> str:
    installed_model = root / MODEL_PATH
    custom_model = root / CUSTOM_MODEL_PATH
    model_path = next(
        (
            candidate
            for candidate in (custom_model, installed_model, SOURCE_MODEL_PATH)
            if candidate.is_file()
        ),
        None,
    )
    if model_path is None:
        raise InitializationError(
            f"modelo não encontrado: {installed_model}; reinstale o framework"
        )
    content = model_path.read_text(encoding="utf-8")
    replacements = {
        "{{BACKLOG_ID}}": f"BACKLOG-{number:04d}",
        "{{BACKLOG_NAME}}": title,
        "{{CURRENT_DATE}}": date.today().isoformat(),
        "{{ORIGINAL_IDEA}}": idea,
        "{{PERCEIVED_PROBLEM}}": problem,
        "{{AFFECTED_PERSON}}": person,
        "{{EXPECTED_RESULT}}": result,
        "{{IDEA_CONTEXT}}": context,
    }
    for token, value in replacements.items():
        if token not in content:
            raise InitializationError(f"token obrigatório ausente: {token}")
        content = content.replace(token, value)
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", content)))
    if unresolved:
        raise InitializationError(
            f"tokens não preenchidos: {', '.join(unresolved)}"
        )
    return content


def initialize_backlog(
    *,
    title: str,
    slug: str,
    root: Path,
    idea: str,
    problem: str,
    person: str,
    result: str,
    context: str,
) -> Path:
    backlog_directory = root / "specs" / "backlog"
    backlog_directory.mkdir(parents=True, exist_ok=True)
    directory_fd = os.open(backlog_directory, os.O_RDONLY)
    temporary: Path | None = None
    try:
        fcntl.flock(directory_fd, fcntl.LOCK_EX)
        number = next_number(backlog_directory)
        destination = backlog_directory / f"{number:04d}-{slug}.md"
        if destination.exists():
            raise InitializationError(
                f"o destino já existe e não será sobrescrito: {destination}"
            )
        temporary = backlog_directory / f".{destination.name}.tmp"
        temporary.write_text(
            render_model(
                root=root,
                number=number,
                title=title,
                idea=idea,
                problem=problem,
                person=person,
                result=result,
                context=context,
            ),
            encoding="utf-8",
        )
        os.replace(temporary, destination)
        return destination.resolve()
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        fcntl.flock(directory_fd, fcntl.LOCK_UN)
        os.close(directory_fd)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Cria specs/backlog/NNNN-slug.md com a captura mínima, sem criar spec."
        )
    )
    parser.add_argument("--title", required=True, help="título curto da ideia")
    parser.add_argument(
        "--idea", required=True, help="formulação original fornecida pelo usuário"
    )
    parser.add_argument("--problem", required=True, help="problema percebido")
    parser.add_argument(
        "--person", required=True, help="pessoa afetada ou beneficiada"
    )
    parser.add_argument(
        "--result", required=True, help="resultado ou valor esperado"
    )
    parser.add_argument(
        "--context", required=True, help="contexto que distingue a ideia"
    )
    parser.add_argument("--slug", help="slug kebab-case opcional")
    parser.add_argument("--root", help="raiz de destino; padrão: diretório atual")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        title = normalized_title(args.title)
        idea = required_text(args.idea, "a ideia original")
        problem = required_text(args.problem, "o problema percebido")
        person = required_text(args.person, "a pessoa afetada ou beneficiada")
        result = required_text(args.result, "o resultado ou valor esperado")
        context = required_text(args.context, "o contexto")
        slug = validated_slug(args.slug, title)
        root = project_root(args.root)
        path = initialize_backlog(
            title=title,
            slug=slug,
            root=root,
            idea=idea,
            problem=problem,
            person=person,
            result=result,
            context=context,
        )
    except (InitializationError, OSError) as error:
        print(f"erro: {error}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
