#!/usr/bin/env python3
"""Registra uma entrada na Inbox usando o template instalado no consumidor."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path


TEMPLATE_PATH = Path(".specsfy/templates/Inbox.md")
CUSTOM_TEMPLATE_PATH = Path(".specsfy/templates/custom/Inbox.md")
SOURCE_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "Inbox.md"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOKEN_PATTERN = re.compile(r"\{\{[A-Z0-9_]+\}\}")
UNKNOWN = "Não identificado no texto original."


class CaptureError(ValueError):
    """Representa uma entrada ou estado incompatível com captura segura."""


def template_path(root: Path) -> Path:
    """Resolve o template respeitando customização, instalação e fallback."""

    for candidate in (
        root / CUSTOM_TEMPLATE_PATH,
        root / TEMPLATE_PATH,
        SOURCE_TEMPLATE_PATH,
    ):
        if candidate.is_file():
            return candidate
    raise CaptureError(
        "template não encontrado; execute `specsfy install` para publicar "
        f"{TEMPLATE_PATH}"
    )


def required_text(raw_value: str, field: str) -> str:
    value = raw_value.strip()
    if not value:
        raise CaptureError(f"{field} não pode ficar vazio")
    return value


def normalized_title(raw_title: str) -> str:
    title = required_text(raw_title, "o título")
    if any(character in title for character in "\r\n"):
        raise CaptureError("o título deve ocupar uma única linha")
    return title


def slugify(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")
    if not slug:
        raise CaptureError(
            "o título deve conter ao menos um caractere alfanumérico"
        )
    return slug


def validated_slug(raw_slug: str | None, title: str) -> str:
    if raw_slug is None:
        return slugify(title)
    slug = raw_slug.strip()
    if not SLUG_PATTERN.fullmatch(slug):
        raise CaptureError(
            f"slug inválido {raw_slug!r}; "
            "utilize caracteres ASCII em kebab-case"
        )
    return slug


def project_root(raw_root: str | None) -> Path:
    root = Path.cwd() if raw_root is None else Path(raw_root).expanduser()
    root = root.resolve()
    if not root.exists():
        raise CaptureError(f"a raiz não existe: {root}")
    if not root.is_dir():
        raise CaptureError(f"a raiz não é um diretório: {root}")
    return root


def render_template(
    *,
    template: Path,
    title: str,
    slug: str,
    captured_at: datetime,
    original_input: str,
    summary: str,
    problem: str,
    people: str,
    value: str,
    signals: str,
    risks: str,
    directions: str,
    review: str,
) -> str:
    if not template.is_file():
        raise CaptureError(
            f"template não encontrado: {template}; reinstale o framework"
        )
    content = template.read_text(encoding="utf-8")
    replacements = {
        "{{INBOX_NAME}}": title,
        "{{INBOX_SLUG}}": slug,
        "{{CAPTURED_AT}}": captured_at.isoformat(timespec="seconds"),
        "{{ORIGINAL_INPUT_SHA256}}": hashlib.sha256(
            original_input.encode("utf-8")
        ).hexdigest(),
        "{{ORIGINAL_INPUT}}": original_input,
        "{{SUMMARY}}": summary,
        "{{PROBLEM_OR_OPPORTUNITY}}": problem,
        "{{AFFECTED_PEOPLE}}": people,
        "{{EXPECTED_VALUE}}": value,
        "{{EXTRACTED_SIGNALS}}": signals,
        "{{RISKS_AND_DEPENDENCIES}}": risks,
        "{{FUTURE_DIRECTIONS}}": directions,
        "{{FUTURE_REVIEW}}": review,
    }
    for token, value in replacements.items():
        if token not in content:
            raise CaptureError(f"token obrigatório ausente: {token}")
        content = content.replace(token, value)
    unresolved = sorted(set(TOKEN_PATTERN.findall(content)))
    if unresolved:
        raise CaptureError(f"tokens não preenchidos: {', '.join(unresolved)}")
    return content


def capture_inbox(
    *,
    root: Path,
    title: str,
    slug: str,
    original_input: str,
    summary: str,
    problem: str,
    people: str,
    value: str,
    signals: str,
    risks: str,
    directions: str,
    review: str,
) -> Path:
    destination_directory = root / "specs" / "inbox"
    destination_directory.mkdir(parents=True, exist_ok=True)
    directory_fd = os.open(destination_directory, os.O_RDONLY)
    temporary: Path | None = None
    try:
        fcntl.flock(directory_fd, fcntl.LOCK_EX)
        captured_at = datetime.now().astimezone().replace(microsecond=0)
        prefix = captured_at.strftime("%Y-%m-%d-%H%M%S")
        destination = destination_directory / f"{prefix}-{slug}.md"
        collision = 2
        while destination.exists():
            destination = destination_directory / f"{prefix}-{slug}-{collision}.md"
            collision += 1
        temporary = destination_directory / f".{destination.name}.tmp"
        temporary.write_text(
            render_template(
                template=template_path(root),
                title=title,
                slug=slug,
                captured_at=captured_at,
                original_input=original_input,
                summary=summary,
                problem=problem,
                people=people,
                value=value,
                signals=signals,
                risks=risks,
                directions=directions,
                review=review,
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
        description="Registra uma entrada sem interação em specs/inbox/."
    )
    parser.add_argument("--input", required=True, help="texto original integral")
    parser.add_argument("--title", required=True, help="título curto derivado")
    parser.add_argument("--summary", default=UNKNOWN)
    parser.add_argument("--problem", default=UNKNOWN)
    parser.add_argument("--people", default=UNKNOWN)
    parser.add_argument("--value", default=UNKNOWN)
    parser.add_argument("--signals", default=UNKNOWN)
    parser.add_argument("--risks", default=UNKNOWN)
    parser.add_argument("--directions", default=UNKNOWN)
    parser.add_argument("--review", default="Revisar as lacunas antes da promoção.")
    parser.add_argument("--slug", help="slug kebab-case opcional")
    parser.add_argument("--root", help="raiz do projeto; padrão: diretório atual")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        original_input = required_text(args.input, "o texto original")
        title = normalized_title(args.title)
        path = capture_inbox(
            root=project_root(args.root),
            title=title,
            slug=validated_slug(args.slug, title),
            original_input=original_input,
            summary=required_text(args.summary, "o resumo"),
            problem=required_text(args.problem, "o problema ou oportunidade"),
            people=required_text(args.people, "as pessoas afetadas"),
            value=required_text(args.value, "o valor esperado"),
            signals=required_text(args.signals, "os sinais extraídos"),
            risks=required_text(args.risks, "os riscos e dependências"),
            directions=required_text(args.directions, "as direções futuras"),
            review=required_text(args.review, "os pontos a revisar"),
        )
    except (CaptureError, OSError) as error:
        print(f"erro: {error}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
