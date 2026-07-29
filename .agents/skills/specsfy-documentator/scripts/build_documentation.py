#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable
from urllib.parse import quote


START = "<!-- specsfy:documentator:start -->"
END = "<!-- specsfy:documentator:end -->"
IGNORED_PARTS = {
    ".git",
    ".venv",
    "build",
    "coverage",
    "dist",
    "docs",
    "node_modules",
    "storage",
    "vendor",
}
CODE_SUFFIXES = {
    ".astro",
    ".blade.php",
    ".go",
    ".js",
    ".jsx",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".ts",
    ".tsx",
    ".vue",
}
KNOWN_GITHUB = {
    "@astrojs/react": "https://github.com/withastro/astro",
    "@inertiajs/react": "https://github.com/inertiajs/inertia",
    "@vitejs/plugin-react": "https://github.com/vitejs/vite-plugin-react",
    "astro": "https://github.com/withastro/astro",
    "axios": "https://github.com/axios/axios",
    "laravel/framework": "https://github.com/laravel/framework",
    "next": "https://github.com/vercel/next.js",
    "pestphp/pest": "https://github.com/pestphp/pest",
    "phpunit/phpunit": "https://github.com/sebastianbergmann/phpunit",
    "react": "https://github.com/facebook/react",
    "react-dom": "https://github.com/facebook/react",
    "tailwindcss": "https://github.com/tailwindlabs/tailwindcss",
    "vite": "https://github.com/vitejs/vite",
    "vitest": "https://github.com/vitest-dev/vitest",
}


@dataclass(frozen=True)
class Package:
    category: str
    scope: str
    name: str
    version: str
    source: str
    github: str


@dataclass(frozen=True)
class Entity:
    name: str
    fields: tuple[str, ...]
    relations: tuple[str, ...]
    source: str


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def relative(path: Path, project: Path) -> str:
    return path.relative_to(project).as_posix()


def included(path: Path, project: Path) -> bool:
    try:
        parts = path.relative_to(project).parts
    except ValueError:
        return False
    return not any(part in IGNORED_PARTS for part in parts)


def project_files(project: Path) -> list[Path]:
    return sorted(
        path
        for path in project.rglob("*")
        if path.is_file() and included(path, project)
    )


def has_code_suffix(path: Path) -> bool:
    value = path.name.casefold()
    return any(value.endswith(suffix) for suffix in CODE_SUFFIXES)


def safe_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip() or "—"


def md_link(label: str, target: str) -> str:
    return f"[{safe_cell(label)}]({target})"


def mermaid_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not normalized or normalized[0].isdigit():
        normalized = f"N_{normalized}"
    return normalized[:80]


def symbol_name(path: Path) -> str:
    name = path.name
    for suffix in (".blade.php", ".test.tsx", ".test.ts", ".spec.ts", path.suffix):
        if suffix and name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name


def frameworks(project: Path) -> list[str]:
    observed: list[str] = []
    composer = load_json(project / "composer.json")
    composer_packages = {
        **composer.get("require", {}),
        **composer.get("require-dev", {}),
    }
    package = load_json(project / "package.json")
    npm_packages = {
        **package.get("dependencies", {}),
        **package.get("devDependencies", {}),
    }
    for dependency, label in (
        ("laravel/framework", "Laravel"),
        ("pestphp/pest", "Pest"),
    ):
        if dependency in composer_packages:
            observed.append(label)
    for dependency, label in (
        ("next", "Next.js"),
        ("astro", "Astro"),
        ("react", "React"),
        ("tailwindcss", "Tailwind CSS"),
        ("vitest", "Vitest"),
    ):
        if dependency in npm_packages:
            observed.append(label)
    return list(dict.fromkeys(observed))


def classify_files(project: Path, files: list[Path]) -> dict[str, list[Path]]:
    groups = {
        "Controllers": [],
        "Models": [],
        "Serviços": [],
        "Jobs": [],
        "Policies": [],
        "Rotas e APIs": [],
        "Views": [],
        "Páginas": [],
        "Componentes": [],
        "Testes": [],
        "Outras fontes": [],
    }
    for path in files:
        rel = relative(path, project)
        folded = rel.casefold()
        parts = {part.casefold() for part in PurePosixPath(rel).parts}
        target: str | None = None
        if "tests" in parts or "test" in parts or re.search(r"\.(test|spec)\.", folded):
            target = "Testes"
        elif "controllers" in parts:
            target = "Controllers"
        elif "models" in parts or "entities" in parts:
            target = "Models"
        elif "services" in parts:
            target = "Serviços"
        elif "jobs" in parts:
            target = "Jobs"
        elif "policies" in parts:
            target = "Policies"
        elif rel.startswith("routes/") or "/api/" in folded or path.name.startswith("route."):
            target = "Rotas e APIs"
        elif ".blade.php" in folded or "views" in parts:
            target = "Views"
        elif "pages" in parts or path.name.startswith(("page.", "layout.")):
            target = "Páginas"
        elif "components" in parts:
            target = "Componentes"
        elif has_code_suffix(path):
            target = "Outras fontes"
        if target:
            groups[target].append(path)
    return groups


def github_from_repository(value: object) -> str | None:
    if isinstance(value, dict):
        value = value.get("url")
    if not isinstance(value, str) or "github.com" not in value:
        return None
    normalized = value.removeprefix("git+").replace("git@github.com:", "https://github.com/")
    normalized = normalized.replace("git://github.com/", "https://github.com/")
    if normalized.startswith("ssh://git@github.com/"):
        normalized = normalized.replace("ssh://git@github.com/", "https://github.com/", 1)
    return normalized.removesuffix(".git")


def github_for_npm(project: Path, name: str) -> tuple[str, str]:
    installed = project / "node_modules" / name / "package.json"
    metadata = load_json(installed)
    declared = github_from_repository(metadata.get("repository"))
    if declared:
        return declared, f"`{relative(installed, project)}`"
    if name in KNOWN_GITHUB:
        return KNOWN_GITHUB[name], "catálogo conhecido do documentador"
    search = f"https://github.com/search?q={quote(name)}&type=repositories"
    return search, "busca GitHub; repositório não declarado localmente"


def packages(project: Path) -> list[Package]:
    result: list[Package] = []
    composer = load_json(project / "composer.json")
    composer_lock = load_json(project / "composer.lock")
    locked_composer = {}
    for scope, key in (("produção", "packages"), ("desenvolvimento", "packages-dev")):
        for item in composer_lock.get(key, []):
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                locked_composer[item["name"]] = (item, scope)
    composer_scopes = (
        ("produção", composer.get("require", {})),
        ("desenvolvimento", composer.get("require-dev", {})),
    )
    if composer:
        result.append(
            Package(
                "Nativo",
                "runtime",
                "PHP",
                str(composer.get("require", {}).get("php", "detectada pelo manifest")),
                "`composer.json`",
                "https://github.com/php/php-src",
            )
        )
    for scope, dependencies in composer_scopes:
        for name, constraint in sorted(dependencies.items()):
            if name == "php":
                continue
            locked, _ = locked_composer.get(name, ({}, scope))
            github = github_from_repository(locked.get("source"))
            if not github:
                github = KNOWN_GITHUB.get(name)
            source = "`composer.lock`" if locked else "`composer.json`"
            if not github:
                github = f"https://github.com/search?q={quote(name)}&type=repositories"
                source += "; busca GitHub"
            category = (
                "Framework"
                if name in {"laravel/framework"}
                else "Integrado"
                if scope == "produção"
                else "Terceiro"
            )
            result.append(
                Package(
                    category,
                    scope,
                    name,
                    str(locked.get("version", constraint)),
                    source,
                    github,
                )
            )

    package = load_json(project / "package.json")
    package_lock = load_json(project / "package-lock.json")
    lock_packages = package_lock.get("packages", {})
    if package:
        result.append(
            Package(
                "Nativo",
                "runtime",
                "Node.js",
                str(package.get("engines", {}).get("node", "versão do ambiente")),
                "`package.json`",
                "https://github.com/nodejs/node",
            )
        )
    npm_scopes = (
        ("produção", package.get("dependencies", {})),
        ("desenvolvimento", package.get("devDependencies", {})),
    )
    framework_names = {"next", "astro", "react", "react-dom", "tailwindcss", "vite"}
    for scope, dependencies in npm_scopes:
        for name, constraint in sorted(dependencies.items()):
            locked = lock_packages.get(f"node_modules/{name}", {})
            github, github_source = github_for_npm(project, name)
            source = "`package-lock.json`" if locked else "`package.json`"
            if "busca GitHub" in github_source:
                source += "; busca GitHub"
            category = (
                "Framework"
                if name in framework_names
                else "Integrado"
                if scope == "produção"
                else "Terceiro"
            )
            result.append(
                Package(
                    category,
                    scope,
                    name,
                    str(locked.get("version", constraint)),
                    source,
                    github,
                )
            )
    unique = {(item.name, item.scope): item for item in result}
    return sorted(unique.values(), key=lambda item: (item.category, item.name, item.scope))


def laravel_entities(project: Path) -> list[Entity]:
    entities: list[Entity] = []
    migrations = project / "database" / "migrations"
    if not migrations.is_dir():
        return entities
    for path in sorted(migrations.glob("*.php")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for table in re.findall(r"Schema::(?:create|table)\(\s*['\"]([^'\"]+)", text):
            fields: list[str] = []
            relations: list[str] = []
            if "$table->id()" in text:
                fields.append("id")
            for kind, name in re.findall(
                r"\$table->([A-Za-z_][A-Za-z0-9_]*)\(\s*['\"]([^'\"]+)",
                text,
            ):
                fields.append(f"{name}:{kind}")
                if kind in {"foreignId", "foreignUuid"}:
                    related = name.removesuffix("_id")
                    relations.append(f"{related}s")
            entities.append(
                Entity(
                    table,
                    tuple(dict.fromkeys(fields)),
                    tuple(dict.fromkeys(relations)),
                    relative(path, project),
                )
            )
    return entities


def prisma_entities(project: Path) -> list[Entity]:
    entities: list[Entity] = []
    for path in sorted(project.rglob("*.prisma")):
        if not included(path, project):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"model\s+(\w+)\s*\{(.*?)\}", text, re.DOTALL):
            fields = []
            relations = []
            for line in match.group(2).splitlines():
                field = re.match(r"\s*(\w+)\s+([\w\[\]?]+)", line)
                if not field:
                    continue
                fields.append(f"{field.group(1)}:{field.group(2)}")
                if field.group(2).rstrip("[]?")[0:1].isupper():
                    relations.append(field.group(2).rstrip("[]?"))
            entities.append(
                Entity(
                    match.group(1),
                    tuple(fields),
                    tuple(relations),
                    relative(path, project),
                )
            )
    return entities


def entities(project: Path) -> list[Entity]:
    observed = laravel_entities(project) + prisma_entities(project)
    unique = {(item.name, item.source): item for item in observed}
    return sorted(unique.values(), key=lambda item: (item.name, item.source))


def routes(project: Path, files: list[Path]) -> list[tuple[str, str, str]]:
    observed: list[tuple[str, str, str]] = []
    route_root = project / "routes"
    if route_root.is_dir():
        for path in sorted(route_root.glob("*.php")):
            text = path.read_text(encoding="utf-8", errors="replace")
            for method, uri, target in re.findall(
                r"Route::(\w+)\(\s*['\"]([^'\"]+)['\"]\s*,\s*(.*?)\);",
                text,
            ):
                observed.append((method.upper(), uri, safe_cell(target)))
    for path in files:
        rel = relative(path, project)
        folded = rel.casefold()
        if "/api/" in folded and path.name.startswith("route."):
            text = path.read_text(encoding="utf-8", errors="replace")
            methods = re.findall(
                r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE)",
                text,
            )
            parent = rel.rsplit("/route.", 1)[0].removeprefix("app/")
            observed.extend((method, f"/{parent}", rel) for method in methods)
        elif path.name.startswith("page.") and has_code_suffix(path):
            parent = PurePosixPath(rel).parent.as_posix()
            uri = "/" if parent == "app" else "/" + parent.removeprefix("app/")
            observed.append(("PAGE", uri, rel))
    return list(dict.fromkeys(observed))


def test_runner(project: Path) -> tuple[str, list[str]]:
    composer = load_json(project / "composer.json")
    package = load_json(project / "package.json")
    composer_packages = {
        **composer.get("require", {}),
        **composer.get("require-dev", {}),
    }
    npm_packages = {
        **package.get("dependencies", {}),
        **package.get("devDependencies", {}),
    }
    commands: list[str] = []
    if "pestphp/pest" in composer_packages:
        runner = "Pest"
        commands.append("php artisan test")
    elif "phpunit/phpunit" in composer_packages:
        runner = "PHPUnit"
        commands.append("vendor/bin/phpunit")
    elif "vitest" in npm_packages:
        runner = "Vitest"
    elif "jest" in npm_packages:
        runner = "Jest"
    elif package:
        runner = "Node Test ou runner definido no projeto"
    else:
        runner = "Não identificado"
    for name, command in sorted(package.get("scripts", {}).items()):
        if "test" in name.casefold():
            commands.append(f"npm run {name}  # {command}")
    for name, command in sorted(composer.get("scripts", {}).items()):
        if "test" in name.casefold() and isinstance(command, str):
            commands.append(f"composer {name}  # {command}")
    return runner, list(dict.fromkeys(commands))


def env_keys(project: Path) -> list[str]:
    path = project / ".env.example"
    if not path.is_file():
        return []
    keys = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"\s*([A-Z][A-Z0-9_]+)\s*=", line)
        if match:
            keys.append(match.group(1))
    return sorted(set(keys))


def project_title(project: Path) -> str:
    package = load_json(project / "package.json")
    composer = load_json(project / "composer.json")
    return str(package.get("name") or composer.get("name") or project.name)


def table(headers: tuple[str, ...], rows: Iterable[tuple[object, ...]]) -> str:
    materialized = list(rows)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    if materialized:
        lines.extend(
            "| " + " | ".join(safe_cell(cell) for cell in row) + " |"
            for row in materialized
        )
    else:
        lines.append("| " + " | ".join("Não identificado" for _ in headers) + " |")
    return "\n".join(lines)


def generated_block(content: str) -> str:
    return f"{START}\n{content.rstrip()}\n{END}"


def merge_document(existing: str, title: str, generated: str) -> str:
    block = generated_block(generated)
    if START in existing and END in existing:
        before, remainder = existing.split(START, 1)
        _, after = remainder.split(END, 1)
        return f"{before}{block}{after}".rstrip() + "\n"
    prefix = existing.rstrip()
    if not prefix:
        prefix = f"# {title}"
    return f"{prefix}\n\n{block}\n"


def render_readme(project: Path, framework_names: list[str], stats: dict[str, int]) -> str:
    navigation = (
        ("Arquitetura", "architecture.md"),
        ("Aplicação", "application.md"),
        ("Banco de dados", "database.md"),
        ("Fluxos", "flows.md"),
        ("Testes", "testing.md"),
        ("Frontend", "frontend.md"),
        ("Pacotes", "packages.md"),
        ("Integrações", "integrations.md"),
        ("Decisões", "decisions.md"),
    )
    return f"""## Visão geral

Documentação técnica reconstruída a partir do código de **{safe_cell(project_title(project))}**.
Serve como mapa de entrada para humanos e agentes; fontes executáveis continuam
prevalecendo quando houver divergência.

- Stack observada: {", ".join(framework_names) or "não identificada"}
- Arquivos de código mapeados: {stats["code"]}
- Testes mapeados: {stats["tests"]}
- Entidades persistentes mapeadas: {stats["entities"]}
- Pacotes mapeados: {stats["packages"]}

## Ordem de leitura

{table(("Assunto", "Documento"), ((name, md_link(path, path)) for name, path in navigation))}

## Fontes de contexto

- [`PROJECT.md`](../PROJECT.md), quando existir.
- [`.specsfy/STACK.md`](../.specsfy/STACK.md), quando existir.
- [`.specsfy/RULES.md`](../.specsfy/RULES.md), quando existir.
- [`.specsfy/DATABASE.md`](../.specsfy/DATABASE.md), quando existir.
"""


def render_architecture(
    framework_names: list[str],
    groups: dict[str, list[Path]],
    project: Path,
    entity_items: list[Entity],
) -> str:
    class_names = []
    for category in ("Controllers", "Models", "Serviços", "Componentes"):
        class_names.extend(symbol_name(path) for path in groups[category][:20])
    class_lines = [f"  class {mermaid_id(name)}" for name in dict.fromkeys(class_names)]
    if not class_lines:
        class_lines = ["  class Application"]
    db_node = "Database" if entity_items else "Persistence_not_identified"
    return f"""## Contexto arquitetural

- Frameworks e superfícies observadas: {", ".join(framework_names) or "não identificadas"}.
- A topologia abaixo é inferida de manifests e caminhos; confirme limites não
  expressos no código.

```mermaid
flowchart LR
  Human[Pessoa usuária] --> UI[Interface / API]
  Agent[Agente de código] --> Docs[docs/]
  UI --> App[Aplicação]
  App --> {db_node}[Persistência]
  App --> Integrations[Integrações externas]
  Docs --> App
```

## UML de componentes implementados

```mermaid
classDiagram
{chr(10).join(class_lines)}
```

## Evidência por camada

{table(("Camada", "Quantidade", "Exemplos"), (
    (
        category,
        len(paths),
        ", ".join(f"`{relative(path, project)}`" for path in paths[:5]) or "—",
    )
    for category, paths in groups.items()
))}
"""


def render_application(groups: dict[str, list[Path]], project: Path) -> str:
    rows = []
    for category, paths in groups.items():
        for path in paths:
            rows.append((category, symbol_name(path), f"`{relative(path, project)}`"))
    return f"""## Inventário implementado

O inventário inclui código anterior à adoção do Specsfy e mudanças recentes.
Nomes representam símbolos ou arquivos observados, não responsabilidades
inventadas.

{table(("Tipo", "Implementação", "Fonte"), rows)}

## Mapa de responsabilidades

{table(("Área", "Leitura recomendada"), (
    ("Controllers e APIs", "Entradas HTTP, validação e orquestração"),
    ("Models e entidades", "Estado persistente, relações e invariantes"),
    ("Serviços e jobs", "Casos de uso, integrações e processamento assíncrono"),
    ("Views, páginas e componentes", "Apresentação e interação"),
))}
"""


def render_database(entity_items: list[Entity]) -> str:
    rows = [
        (
            item.name,
            ", ".join(item.fields) or "campos não inferidos",
            ", ".join(item.relations) or "não inferidas",
            f"`{item.source}`",
        )
        for item in entity_items
    ]
    diagram_lines = ["erDiagram"]
    if not entity_items:
        diagram_lines.append("  PERSISTENCE_NOT_IDENTIFIED")
    for item in entity_items:
        entity_id = mermaid_id(item.name).upper()
        diagram_lines.append(f"  {entity_id} {{")
        for field in item.fields[:30]:
            name, _, kind = field.partition(":")
            diagram_lines.append(
                f"    {mermaid_id(kind or 'value')} {mermaid_id(name)}"
            )
        diagram_lines.append("  }")
        for related in item.relations:
            diagram_lines.append(
                f"  {mermaid_id(related).upper()} ||--o{{ {entity_id} : relaciona"
            )
    return f"""## Mapa de persistência

{table(("Entidade/Tabela", "Campos", "Relações", "Fonte"), rows)}

```mermaid
{chr(10).join(diagram_lines)}
```

## Fonte complementar

Consulte [`.specsfy/DATABASE.md`](../.specsfy/DATABASE.md) para decisões,
ownership, retenção e detalhes humanos não inferíveis.
"""


def render_flows(route_items: list[tuple[str, str, str]]) -> str:
    flow_lines = ["flowchart LR", "  Client[Cliente] --> Entry[Rota / Página]"]
    if route_items:
        for index, (method, uri, target) in enumerate(route_items[:30], 1):
            flow_lines.append(
                f'  Entry --> R{index}["{safe_cell(method)} {safe_cell(uri)}"]'
            )
            flow_lines.append(f'  R{index} --> T{index}["{safe_cell(target)}"]')
    else:
        flow_lines.append("  Entry --> Unknown[Fluxos não identificados]")
    sequence_target = safe_cell(route_items[0][2]) if route_items else "Aplicação"
    return f"""## Entradas observadas

{table(("Método/Tipo", "Caminho", "Destino observado"), route_items)}

## Fluxo de navegação e requisição

```mermaid
{chr(10).join(flow_lines)}
```

## Sequência representativa

```mermaid
sequenceDiagram
  actor User as Pessoa usuária
  participant UI as Interface/API
  participant App as {sequence_target}
  participant DB as Persistência
  User->>UI: inicia ação
  UI->>App: envia entrada
  App->>DB: consulta ou persiste
  DB-->>App: retorna estado
  App-->>UI: produz resposta
  UI-->>User: apresenta resultado
```
"""


def render_testing(
    runner: str,
    commands: list[str],
    test_files: list[Path],
    project: Path,
) -> str:
    kinds = Counter()
    for path in test_files:
        folded = relative(path, project).casefold()
        if "feature" in folded:
            kinds["Feature/integração"] += 1
        elif "unit" in folded:
            kinds["Unidade"] += 1
        elif any(token in folded for token in ("browser", "e2e", "playwright", "cypress")):
            kinds["Browser/E2E"] += 1
        else:
            kinds["Outros"] += 1
    return f"""## Runner e comandos

- Runner observado: **{runner}**

{table(("Comando", "Origem"), ((f"`{command}`", "manifest ou padrão do framework") for command in commands))}

## Resumo dos testes

{table(("Classe", "Quantidade"), sorted(kinds.items()))}

## Inventário

{table(("Teste", "Caminho"), (
    (symbol_name(path), f"`{relative(path, project)}`") for path in test_files
))}

## Guia

1. Executar primeiro o teste focal da mudança.
2. Executar a suíte relacionada e depois a regressão completa.
3. Registrar RED/GREEN e comandos na spec quando o projeto usar Specsfy.
4. Não considerar erro de ambiente ou fixture como RED válido.
"""


def render_frontend(groups: dict[str, list[Path]], project: Path, files: list[Path]) -> str:
    frontend_paths = [
        *groups["Views"],
        *groups["Páginas"],
        *groups["Componentes"],
    ]
    tailwind_files = [
        path
        for path in files
        if path.name.startswith("tailwind.config.")
        or (
            path.suffix.casefold() == ".css"
            and "tailwind" in path.read_text(encoding="utf-8", errors="replace").casefold()
        )
    ]
    tokens: set[str] = set()
    patterns: Counter[str] = Counter()
    for path in files:
        if path.suffix.casefold() not in {".css", ".js", ".jsx", ".ts", ".tsx", ".vue", ".astro"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        tokens.update(re.findall(r"--[A-Za-z0-9_-]+", text))
        for class_value in re.findall(r"(?:className|class)\s*=\s*[\"']([^\"']+)", text):
            for item in class_value.split():
                patterns[item] += 1
    return f"""## Views, páginas e componentes

{table(("Tipo", "Nome", "Fonte"), (
    (
        "View" if path in groups["Views"] else "Página" if path in groups["Páginas"] else "Componente",
        symbol_name(path),
        f"`{relative(path, project)}`",
    )
    for path in frontend_paths
))}

## Tailwind CSS

{table(("Configuração", "Fonte"), (
    ("Tailwind", f"`{relative(path, project)}`") for path in tailwind_files
))}

### Tokens observados

{", ".join(f"`{token}`" for token in sorted(tokens)) or "Nenhum token CSS identificado."}

### Padrões utilitários mais usados

{table(("Classe", "Ocorrências"), patterns.most_common(30))}

## Convenções de leitura

- Blade vive normalmente em `resources/views/`.
- React é mapeado por componentes JSX/TSX e suas páginas consumidoras.
- Tailwind é derivado de configuração, imports, tokens e classes observadas;
  este mapa não inventa design tokens ausentes.
"""


def render_packages(package_items: list[Package]) -> str:
    return f"""## Catálogo de runtime e dependências

{table(("Categoria", "Escopo", "Pacote", "Versão", "Fonte", "GitHub"), (
    (
        item.category,
        item.scope,
        item.name,
        item.version,
        item.source,
        md_link("repositório", item.github),
    )
    for item in package_items
))}

## Classificação

- **Nativo:** runtime estrutural da linguagem/plataforma.
- **Framework:** base arquitetural ou de interface.
- **Integrado:** dependência de produção ligada diretamente à aplicação.
- **Terceiro:** biblioteca complementar ou de desenvolvimento.

Links rotulados por busca indicam que manifests, locks e pacote instalado não
declararam um repositório GitHub confiável.
"""


def render_integrations(package_items: list[Package], keys: list[str]) -> str:
    integration_packages = [
        item for item in package_items
        if any(token in item.name.casefold() for token in ("sdk", "stripe", "sentry", "aws", "google", "github"))
    ]
    return f"""## Integrações observadas

{table(("Sinal", "Tipo", "Fonte segura"), (
    *((item.name, "pacote", item.source) for item in integration_packages),
    *((key, "variável de ambiente", "`.env.example` (somente nome)") for key in keys),
))}

## Mapa

```mermaid
flowchart LR
  App[Aplicação] --> Config[Configuração por ambiente]
  Config --> External[Serviços externos]
  Docs[docs/integrations.md] --> Config
```

Valores de ambiente, credenciais e endpoints privados não são publicados.
Confirme autenticação, timeout, retry e ownership quando não estiverem
expressos no código.
"""


def source_excerpt(path: Path, project: Path) -> tuple[str, str]:
    if not path.is_file():
        return relative(path, project), "Fonte ausente"
    text = path.read_text(encoding="utf-8", errors="replace")
    headings = re.findall(r"(?m)^#{1,3}\s+(.+)$", text)
    bullets = re.findall(r"(?m)^-\s+(.+)$", text)
    summary = "; ".join([*headings[:4], *bullets[:6]]) or "Sem decisões estruturadas detectadas"
    return relative(path, project), summary


def render_decisions(project: Path) -> str:
    candidates = (
        project / "PROJECT.md",
        project / ".specsfy" / "RULES.md",
        project / ".specsfy" / "STACK.md",
        project / ".specsfy" / "DATABASE.md",
    )
    rows = [source_excerpt(path, project) for path in candidates if path.is_file()]
    return f"""## Fontes explícitas

{table(("Fonte", "Decisões e tópicos observados"), rows)}

## Política

- Decisão explícita prevalece sobre inferência deste documentador.
- Histórico detalhado deve usar ADR ou mecanismo já adotado pelo projeto.
- Ausência de uma decisão é registrada como lacuna, não preenchida por
  preferência do agente.
"""


def build_documents(project: Path) -> dict[str, str]:
    files = project_files(project)
    groups = classify_files(project, files)
    framework_names = frameworks(project)
    entity_items = entities(project)
    package_items = packages(project)
    route_items = routes(project, files)
    runner, commands = test_runner(project)
    test_files = groups["Testes"]
    stats = {
        "code": sum(len(paths) for name, paths in groups.items() if name != "Testes"),
        "tests": len(test_files),
        "entities": len(entity_items),
        "packages": len(package_items),
    }
    return {
        "README.md": render_readme(project, framework_names, stats),
        "architecture.md": render_architecture(
            framework_names, groups, project, entity_items
        ),
        "application.md": render_application(groups, project),
        "database.md": render_database(entity_items),
        "flows.md": render_flows(route_items),
        "testing.md": render_testing(runner, commands, test_files, project),
        "frontend.md": render_frontend(groups, project, files),
        "packages.md": render_packages(package_items),
        "integrations.md": render_integrations(package_items, env_keys(project)),
        "decisions.md": render_decisions(project),
    }


def documentation_digest(documents: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name, content in sorted(documents.items()):
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(content.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        parser.error(f"projeto inexistente: {project}")
    docs = project / "docs"
    generated = build_documents(project)
    planned: dict[Path, str] = {}
    for name, content in generated.items():
        target = docs / name
        existing = target.read_text(encoding="utf-8") if target.is_file() else ""
        title = {
            "README.md": "Documentação técnica",
            "architecture.md": "Arquitetura",
            "application.md": "Aplicação e implementações",
            "database.md": "Banco de dados",
            "flows.md": "Fluxos",
            "testing.md": "Testes",
            "frontend.md": "Frontend e design system",
            "packages.md": "Pacotes e bibliotecas",
            "integrations.md": "Integrações",
            "decisions.md": "Decisões técnicas",
        }[name]
        planned[target] = merge_document(existing, title, content)
    changed = [
        path
        for path, content in planned.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]
    if args.check:
        if changed:
            print("Documentação desatualizada:", file=sys.stderr)
            for path in changed:
                print(f"- {relative(path, project)}", file=sys.stderr)
            return 1
        print(f"Documentação atual: {documentation_digest(generated)}")
        return 0
    docs.mkdir(parents=True, exist_ok=True)
    for path in changed:
        path.write_text(planned[path], encoding="utf-8")
        print(path)
    print(f"Documentação construída: {documentation_digest(generated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
