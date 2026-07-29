#!/usr/bin/env python3
"""Inicializa uma spec ordenada sob a raiz escolhida."""

from __future__ import annotations

import argparse
import fcntl
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path


DIRECTORY_PATTERN = re.compile(r"^(?P<number>\d{4})-")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SPEC_NUMBER = 9999
INSTALLED_TEMPLATE_PATH = Path(".specsfy/templates/Spec.md")
CUSTOM_TEMPLATE_PATH = Path(".specsfy/templates/custom/Spec.md")
SOURCE_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "Spec.md"


class InitializationError(ValueError):
    """Representa uma entrada ou estado que impede inicialização segura."""


def normalized_title(raw_title: str) -> str:
    title = raw_title.strip()
    if not title:
        raise InitializationError("o título não pode ficar vazio")
    if any(character in title for character in "\r\n"):
        raise InitializationError("o título deve ocupar uma única linha")
    return title


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


def next_number(specs_directory: Path) -> int:
    existing_numbers = []
    for child in specs_directory.iterdir():
        match = DIRECTORY_PATTERN.match(child.name)
        if child.is_dir() and match:
            existing_numbers.append(int(match.group("number")))
    number = max(existing_numbers, default=0) + 1
    if number > MAX_SPEC_NUMBER:
        raise InitializationError(
            f"a sequência em {specs_directory} atingiu o limite {MAX_SPEC_NUMBER:04d}"
        )
    return number


def template_path(root: Path) -> Path:
    for candidate in (
        root / CUSTOM_TEMPLATE_PATH,
        root / INSTALLED_TEMPLATE_PATH,
        SOURCE_TEMPLATE_PATH,
    ):
        if candidate.is_file():
            return candidate
    raise InitializationError(
        "template não encontrado; execute `specsfy install` para publicar "
        f"{INSTALLED_TEMPLATE_PATH}"
    )


def render_model(*, number: int, title: str, slug: str, root: Path) -> str:
    source = template_path(root)
    content = source.read_text(encoding="utf-8")
    replacements = {
        "{{SPEC_ID}}": f"SPEC-{number:04d}",
        "{{SPEC_NUMBER}}": f"{number:04d}",
        "{{SPEC_NAME}}": title,
        "{{SPEC_SLUG}}": slug,
        "{{CURRENT_DATE}}": date.today().isoformat(),
    }
    for token, value in replacements.items():
        if token not in content:
            raise InitializationError(f"token obrigatório ausente no modelo: {token}")
        content = content.replace(token, value)
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", content)))
    if unresolved:
        raise InitializationError(
            f"tokens não preenchidos no modelo: {', '.join(unresolved)}"
        )
    return content


def initialize_spec(*, title: str, slug: str, root: Path) -> Path:
    specs_directory = root / "specs" / "specs"
    try:
        specs_directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise InitializationError(
            f"não foi possível preparar {specs_directory}: {error}"
        ) from error

    directory_fd = os.open(specs_directory, os.O_RDONLY)
    destination: Path | None = None
    temporary: Path | None = None
    try:
        fcntl.flock(directory_fd, fcntl.LOCK_EX)
        number = next_number(specs_directory)
        content = render_model(number=number, title=title, slug=slug, root=root)
        destination = specs_directory / f"{number:04d}-{slug}"
        try:
            destination.mkdir()
        except FileExistsError as error:
            raise InitializationError(
                f"o destino já existe e não será sobrescrito: {destination}"
            ) from error

        spec_path = destination / "spec.md"
        temporary = destination / ".spec.md.tmp"
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, spec_path)
        return spec_path.resolve()
    except (InitializationError, OSError):
        if temporary is not None and temporary.exists():
            temporary.unlink()
        if destination is not None and destination.exists():
            try:
                destination.rmdir()
            except OSError:
                pass
        raise
    finally:
        fcntl.flock(directory_fd, fcntl.LOCK_UN)
        os.close(directory_fd)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Cria specs/specs/NNNN-slug/spec.md a partir do template Specsfy."
        )
    )
    parser.add_argument("--title", required=True, help="nome humano da especificação")
    parser.add_argument("--slug", help="slug kebab-case opcional")
    parser.add_argument(
        "--root",
        help="raiz de destino; por padrão usa o diretório atual do processo",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        title = normalized_title(args.title)
        slug = validated_slug(args.slug, title)
        root = project_root(args.root)
        path = initialize_spec(title=title, slug=slug, root=root)
    except (InitializationError, OSError) as error:
        print(f"erro: {error}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
