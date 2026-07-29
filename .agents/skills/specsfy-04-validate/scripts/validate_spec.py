#!/usr/bin/env python3
"""Valida o formato rígido Specsfy/2.0 e a coerência interna de spec.md."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from review_findings import analyze as analyze_findings


FORMAT_VERSION = "Specsfy/2.0"
MINIMUM_CONTEXT_SCENARIOS = 3
ACTS = (
    "Ato I — Definir",
    "Ato II — Projetar e provar",
    "Ato III — Entregar e validar",
)
SECTIONS = (
    "Problema e resultado",
    "Research e esclarecimentos",
    "Escopo e atores",
    "Princípios e restrições do projeto",
    "Histórias de usuário",
    "Cenários BDD de aceite",
    "Requisitos",
    "Plano técnico",
    "Modelo de dados",
    "Interfaces e contratos",
    "Estratégia TDD",
    "Plano de testes e rastreabilidade",
    "Validações",
    "Tarefas",
    "Ordem de execução",
    "Dependências, riscos e suposições",
    "Decisões",
    "Definition of Done",
)
STRUCTURE = (
    (ACTS[0], 2),
    *((section, 3) for section in SECTIONS[0:7]),
    (ACTS[1], 2),
    *((section, 3) for section in SECTIONS[7:15]),
    (ACTS[2], 2),
    *((section, 3) for section in SECTIONS[15:18]),
)
REQUIRED_SUBHEADINGS = (
    "Researchs executados",
    "Fontes e contexto consultados",
    "Documentação consultada",
    "Artefatos de pesquisa armazenados",
    "Dúvidas respondidas",
    "Dúvidas abertas",
    "Contexto existente",
    "Arquitetura e módulos",
    "Migrations",
    "Models",
    "Controllers e casos de uso",
    "Views e experiência",
    "Queries e repositórios",
    "Jobs e processamento assíncrono",
    "Estrutura de arquivos",
    "Entidades",
    "Estados e transições",
    "Migração e retenção",
    "APIs expostas",
    "APIs externas utilizadas",
    "Documentação das APIs consultadas",
    "Eventos e outros contratos",
    "Evidência RED-GREEN-REFACTOR",
    "Gate do Ato I — Definição",
    "Gate do Ato II — Plano",
    "Gate do Ato III — Entrega",
)
ALLOWED_PACKAGE_ENTRIES = {"spec.md", "research"}
HEADING = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
DEFINITION_PATTERNS = {
    "US": re.compile(r"^#{4,6}\s+(US-\d{3,})\b", re.MULTILINE),
    "AC": re.compile(r"^#{4,6}\s+(AC-\d{3,})\b", re.MULTILINE),
    "FR": re.compile(r"^\s*-\s+\*\*(FR-\d{3,})\*\*\s*:", re.MULTILINE),
    "NFR": re.compile(r"^\s*-\s+\*\*(NFR-\d{3,})\*\*\s*:", re.MULTILINE),
    "DEC": re.compile(r"^\s*-\s+\*\*(DEC-\d{3,})\*\*\s*:", re.MULTILINE),
}
UNRESOLVED_PATTERNS = (
    re.compile(r"\b(?:TODO|TBD|FIXME)\b"),
    re.compile(r"\[NEEDS CLARIFICATION[^\]]*\]", re.IGNORECASE),
    re.compile(
        r"\[(?:nome|título|ator|ação|capacidade|valor|métrica|"
        r"comportamento|estado inicial|resultado observável|fato confirmado|"
        r"arquivo::teste|tests/arquivo|stack|abordagem|restrição|"
        r"default assumido|Pending\.)[^\]]*\]",
        re.IGNORECASE,
    ),
)


def normalized_title(title: str) -> str:
    return re.sub(r"^\d+\.\s+", "", title).strip()


def headings(text: str) -> list[tuple[int, int, str]]:
    found: list[tuple[int, int, str]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        match = HEADING.match(line)
        if match:
            found.append(
                (
                    line_number,
                    len(match.group("marks")),
                    normalized_title(match.group("title")),
                )
            )
    return found


def section_body(text: str, title: str) -> str | None:
    lines = text.splitlines()
    target_index: int | None = None
    target_level = 0
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if match and normalized_title(match.group("title")).casefold() == title.casefold():
            target_index = index
            target_level = len(match.group("marks"))
            break
    if target_index is None:
        return None
    body: list[str] = []
    for line in lines[target_index + 1 :]:
        match = HEADING.match(line)
        if match and len(match.group("marks")) <= target_level:
            break
        body.append(line)
    return "\n".join(body).strip()


def heading_blocks(text: str, id_prefix: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    result: list[tuple[str, str]] = []
    pattern = re.compile(rf"^({re.escape(id_prefix)}-\d{{3,}})\b")
    for index, line in enumerate(lines):
        heading = HEADING.match(line)
        if not heading:
            continue
        title = normalized_title(heading.group("title"))
        id_match = pattern.match(title)
        if not id_match:
            continue
        level = len(heading.group("marks"))
        body: list[str] = []
        for following in lines[index + 1 :]:
            next_heading = HEADING.match(following)
            if next_heading and len(next_heading.group("marks")) <= level:
                break
            body.append(following)
        result.append((id_match.group(1), "\n".join(body).strip()))
    return result


def metadata(text: str, key: str) -> str | None:
    match = re.search(
        rf"^\|\s*{re.escape(key)}\s*\|\s*(.+?)\s*\|\s*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def minimum_bdd_coverage_errors(text: str) -> list[str]:
    """Exige três ACs distintos por feature, história e requisito."""
    definitions = {
        kind: set(pattern.findall(text))
        for kind, pattern in DEFINITION_PATTERNS.items()
    }
    acceptance_ids = definitions["AC"]
    errors: list[str] = []
    if len(acceptance_ids) < MINIMUM_CONTEXT_SCENARIOS:
        errors.append(
            "A feature possui "
            f"{len(acceptance_ids)} cenários BDD; mínimo exigido: "
            f"{MINIMUM_CONTEXT_SCENARIOS}."
        )

    coverage: dict[str, set[str]] = {}
    for ac_id, body in heading_blocks(text, "AC"):
        covers = re.search(r"^\*\*Cobre\*\*:\s*(.+)$", body, re.MULTILINE)
        if not covers:
            continue
        for item in re.findall(r"\b(?:US|FR|NFR)-\d{3,}\b", covers.group(1)):
            coverage.setdefault(item, set()).add(ac_id)

    for kind in ("US", "FR", "NFR"):
        for item in sorted(definitions[kind]):
            observed = len(coverage.get(item, set()))
            if observed < MINIMUM_CONTEXT_SCENARIOS:
                errors.append(
                    f"{item} possui {observed} cenários BDD; mínimo exigido: "
                    f"{MINIMUM_CONTEXT_SCENARIOS}."
                )
    return errors


def validate(path: Path, *, allow_draft: bool = False) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {
            "path": str(path),
            "status": None,
            "counts": {},
            "errors": [f"Arquivo não encontrado: {path}"],
            "warnings": [],
        }

    text = path.read_text(encoding="utf-8")
    format_value = metadata(text, "Formato")
    slug = metadata(text, "Slug")
    status = metadata(text, "Status")
    definition_gate = metadata(text, "Definition Gate")
    plan_gate = metadata(text, "Plan Gate")
    delivery_gate = metadata(text, "Delivery Gate")

    if format_value != FORMAT_VERSION:
        errors.append(
            f"O cabeçalho tabular deve declarar Formato como {FORMAT_VERSION}."
        )
    if not slug or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        errors.append("Slug deve ser kebab-case na linha Slug do cabeçalho.")
    if path.name != "spec.md" or path.parent.parent.name != "specs":
        errors.append("A spec deve viver em specs/specs/<NNNN>-<slug>/spec.md.")
    elif slug and path.parent.name != slug:
        errors.append(f"Slug {slug!r} difere do diretório {path.parent.name!r}.")
    if status not in {"Draft", "Defined", "Planned", "Implementing", "Complete"}:
        errors.append(
            "Status deve ser Draft, Defined, Planned, Implementing ou Complete."
        )
    if definition_gate not in {"Pending", "Failed", "Passed"}:
        errors.append("Definition Gate deve ser Pending, Failed ou Passed.")
    if plan_gate not in {"Pending", "Failed", "Passed"}:
        errors.append("Plan Gate deve ser Pending, Failed ou Passed.")
    if delivery_gate not in {"Pending", "In Progress", "Failed", "Passed"}:
        errors.append(
            "Delivery Gate deve ser Pending, In Progress, Failed ou Passed."
        )
    allowed_states = {
        "Draft": {
            ("Pending", "Pending", "Pending"),
            ("Failed", "Pending", "Pending"),
        },
        "Defined": {
            ("Passed", "Pending", "Pending"),
            ("Passed", "Failed", "Pending"),
        },
        "Planned": {("Passed", "Passed", "Pending")},
        "Implementing": {
            ("Passed", "Passed", "In Progress"),
            ("Passed", "Passed", "Failed"),
        },
        "Complete": {("Passed", "Passed", "Passed")},
    }
    gate_state = (definition_gate, plan_gate, delivery_gate)
    if status == "Draft" and definition_gate == "Passed":
        errors.append("Status Draft não pode declarar Definition Gate: Passed.")
    if status in allowed_states and gate_state not in allowed_states[status]:
        expected = " ou ".join(
            "/".join(state) for state in sorted(allowed_states[status])
        )
        errors.append(
            f"Status {status} é incompatível com os gates "
            f"{'/'.join(str(value) for value in gate_state)}; esperado {expected}."
        )
    if not allow_draft:
        if status == "Draft":
            errors.append(
                "Status Draft: a fonte ainda não atravessou o Definition Gate."
            )
        if definition_gate != "Passed":
            errors.append(
                "Definition Gate precisa estar Passed para validação estrita."
            )

    declared_gates = (
        ("Gate do Ato I — Definição", "Definition Gate", definition_gate),
        ("Gate do Ato II — Plano", "Plan Gate", plan_gate),
        ("Gate do Ato III — Entrega", "Delivery Gate", delivery_gate),
    )
    for section_title, metadata_name, metadata_value in declared_gates:
        gate_body = section_body(text, section_title) or ""
        result_match = re.search(
            r"^\s*-\s+\*\*Resultado\*\*:\s*(.+?)\s*$",
            gate_body,
            re.MULTILINE,
        )
        if not result_match:
            errors.append(f"{section_title} não declara **Resultado**.")
        elif metadata_value and result_match.group(1).strip() != metadata_value:
            errors.append(
                f"{section_title} diverge do metadata {metadata_name}: "
                f"{result_match.group(1).strip()} != {metadata_value}."
            )

    document_headings = headings(text)
    ordered_contract = list(STRUCTURE)
    locations: dict[str, list[tuple[int, int]]] = {}
    for line_number, level, title in document_headings:
        locations.setdefault(title.casefold(), []).append((line_number, level))
    for title, expected_level in ordered_contract:
        matches = locations.get(title.casefold(), [])
        if not matches:
            errors.append(f"Heading obrigatório ausente: {title}.")
        elif len(matches) > 1:
            errors.append(f"Heading duplicado: {title}.")
        elif matches[0][1] != expected_level:
            errors.append(
                f"Heading {title} deve usar nível H{expected_level}, "
                f"não H{matches[0][1]}."
            )
    for title in REQUIRED_SUBHEADINGS:
        matches = locations.get(title.casefold(), [])
        if not matches:
            errors.append(f"Subseção rígida ausente: {title}.")
        elif len(matches) > 1:
            errors.append(f"Subseção rígida duplicada: {title}.")
        elif matches[0][1] != 4:
            errors.append(
                f"Subseção {title} deve usar nível H4, não H{matches[0][1]}."
            )

    sequence = [
        locations[title.casefold()][0][0]
        for title, _ in ordered_contract
        if len(locations.get(title.casefold(), [])) == 1
    ]
    if len(sequence) == len(ordered_contract) and sequence != sorted(sequence):
        errors.append("Atos ou seções estão fora da ordem canônica Specsfy/2.0.")

    for title in SECTIONS:
        body = section_body(text, title)
        if body is not None and not body:
            errors.append(f"Seção vazia: {title}.")

    unexpected_entries = sorted(
        sibling.name
        for sibling in path.parent.iterdir()
        if sibling.name not in ALLOWED_PACKAGE_ENTRIES
    )
    if unexpected_entries:
        errors.append(
            "Pacote da especificação possui entradas fora de spec.md/research/: "
            + ", ".join(unexpected_entries)
            + "."
        )

    research_root = path.parent / "research"
    research_body = section_body(text, "Artefatos de pesquisa armazenados") or ""
    if research_root.is_symlink():
        errors.append(
            "research não pode ser symlink; o pacote deve preservar evidências locais."
        )
    elif research_root.exists() and not research_root.is_dir():
        errors.append("research deve ser um diretório dentro do pacote da especificação.")
    elif research_root.is_dir():
        symlinks = sorted(
            str(item.relative_to(path.parent))
            for item in research_root.rglob("*")
            if item.is_symlink()
        )
        if symlinks:
            errors.append(
                "Artefatos de research não podem ser symlinks: "
                + ", ".join(symlinks)
                + "."
            )
        for artifact in sorted(research_root.iterdir(), key=lambda item: item.name):
            relative = f"research/{artifact.name}"
            full_relative = f"specs/{path.parent.name}/{relative}"
            if relative not in research_body and full_relative not in research_body:
                errors.append(
                    f"Artefato {relative} não está indexado em "
                    "`Artefatos de pesquisa armazenados`."
                )

    research_context = "\n".join(
        section_body(text, title) or ""
        for title in (
            "Fontes e contexto consultados",
            "Documentação consultada",
            "Artefatos de pesquisa armazenados",
        )
    )
    external_documentation = re.search(r"https?://", research_context)
    has_research_artifact = (
        research_root.is_dir()
        and not research_root.is_symlink()
        and any(research_root.iterdir())
    )
    if external_documentation and not has_research_artifact:
        errors.append(
            "Documentação externa consultada exige cópia ou evidência em research/."
        )

    definitions = {
        kind: pattern.findall(text) for kind, pattern in DEFINITION_PATTERNS.items()
    }
    for kind in ("US", "AC", "FR", "NFR"):
        if not definitions[kind]:
            errors.append(f"Nenhuma definição {kind}-NNN encontrada.")
    for kind, items in definitions.items():
        duplicates = sorted(
            item for item, count in Counter(items).items() if count > 1
        )
        if duplicates:
            errors.append(f"IDs {kind} duplicados: {', '.join(duplicates)}.")

    all_defined = {item for items in definitions.values() for item in items}
    referenced = set(re.findall(r"\b(?:US|AC|FR|NFR|DEC)-\d{3,}\b", text))
    unknown = sorted(referenced - all_defined)
    if unknown:
        errors.append(f"Referências para IDs não definidos: {', '.join(unknown)}.")

    ac_refs: set[str] = set()
    for ac_id, body in heading_blocks(text, "AC"):
        covers = re.search(r"^\*\*Cobre\*\*:\s*(.+)$", body, re.MULTILINE)
        if not covers:
            errors.append(f"{ac_id} não declara **Cobre**.")
            cover_ids: set[str] = set()
        else:
            cover_ids = set(
                re.findall(r"\b(?:US|FR|NFR)-\d{3,}\b", covers.group(1))
            )
            if not cover_ids:
                errors.append(f"{ac_id} não referencia US/FR/NFR em **Cobre**.")
            ac_refs.update(cover_ids)

        gherkin = re.search(
            r"```gherkin\s*(?P<content>.*?)```", body, re.DOTALL | re.IGNORECASE
        )
        if not gherkin:
            errors.append(f"{ac_id} não contém bloco ```gherkin executável.")
            continue
        scenario = gherkin.group("content")
        tags = set(re.findall(r"@((?:US|AC|FR|NFR)-\d{3,})\b", scenario))
        if ac_id not in tags:
            errors.append(f"{ac_id} não possui tag @{ac_id} no Gherkin.")
        if not any(item.startswith("US-") for item in tags):
            errors.append(f"{ac_id} não possui tag @US-NNN no Gherkin.")
        if not any(item.startswith(("FR-", "NFR-")) for item in tags):
            errors.append(f"{ac_id} não possui tag @FR-NNN ou @NFR-NNN no Gherkin.")
        for keyword in ("Feature:", "Given ", "When ", "Then "):
            if not re.search(rf"^\s*{re.escape(keyword)}", scenario, re.MULTILINE):
                errors.append(f"{ac_id} não possui `{keyword.strip()}` em Gherkin.")
        if not re.search(
            r"^\s*Scenario(?: Outline)?:", scenario, re.MULTILINE
        ):
            errors.append(f"{ac_id} não possui Scenario ou Scenario Outline.")

    for fr_id in definitions["FR"]:
        if fr_id not in ac_refs:
            errors.append(f"{fr_id} não é coberto por nenhum cenário BDD AC.")
    errors.extend(minimum_bdd_coverage_errors(text))

    requirements_body = section_body(text, "Requisitos") or ""
    for nfr_id in definitions["NFR"]:
        line = re.search(
            rf"^\s*-\s+\*\*{re.escape(nfr_id)}\*\*\s*:(.+)$",
            requirements_body,
            re.MULTILINE,
        )
        if not line or "verificação" not in line.group(1).lower():
            errors.append(f"{nfr_id} não declara método de Verificação.")

    unresolved = sorted(
        {
            match.group(0)
            for pattern in UNRESOLVED_PATTERNS
            for match in pattern.finditer(text)
        }
    )
    if unresolved:
        message = "Marcadores não resolvidos: " + ", ".join(unresolved[:8]) + "."
        if status == "Draft" and allow_draft:
            warnings.append(message)
        else:
            errors.append(message)

    problem_body = section_body(text, "Problema e resultado") or ""
    if not re.search(r"\d", problem_body):
        warnings.append("Métricas de sucesso parecem não conter alvo numérico.")
    dod_body = section_body(text, "Definition of Done") or ""
    if not re.search(r"^\s*-\s+\[[ xX]\]", dod_body, re.MULTILINE):
        errors.append("Definition of Done não contém checklist.")
    if status == "Complete":
        task_body = section_body(text, "Tarefas") or ""
        if re.search(r"^\s*-\s+\[ \]\s+T\d{3,}\b", task_body, re.MULTILINE):
            errors.append("Status Complete não permite tarefas abertas na seção 14.")
        if re.search(r"^\s*-\s+\[ \]", dod_body, re.MULTILINE):
            errors.append("Status Complete exige toda a Definition of Done concluída.")

    if re.search(
        r"^\s*-\s+\*\*FIND-(?:PROD|ARCH|SEC)-\d{3,}\*\*",
        text,
        re.MULTILINE,
    ):
        review = analyze_findings(text)
        errors.extend(
            f"Finding inválido: {message}" for message in review["errors"]
        )
        errors.extend(
            f"Finding P1 aberto bloqueia o gate: {finding}"
            for finding in review["blocking"]
        )

    return {
        "path": str(path),
        "format": format_value,
        "slug": slug,
        "status": status,
        "gates": {
            "definition": definition_gate,
            "plan": plan_gate,
            "delivery": delivery_gate,
        },
        "counts": {kind: len(items) for kind, items in definitions.items()},
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Caminho para spec.md")
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Validar estrutura intermediária sem promover Draft a READY",
    )
    parser.add_argument("--json", action="store_true", help="Emitir JSON")
    args = parser.parse_args()
    result = validate(args.spec.resolve(), allow_draft=args.allow_draft)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Spec: {result['path']}")
        print(f"Formato: {result.get('format') or 'inválido'}")
        print(f"Status: {result.get('status') or 'inválido'}")
        counts = result.get("counts", {})
        if counts:
            print("Contagens: " + " ".join(f"{key}={value}" for key, value in counts.items()))
        for error in result["errors"]:
            print(f"ERRO: {error}")
        for warning in result["warnings"]:
            print(f"AVISO: {warning}")
        if result["errors"]:
            print("RESULTADO: NOT READY")
        elif result.get("status") == "Draft":
            print("RESULTADO: VALID DRAFT")
        else:
            print("RESULTADO: READY")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
