#!/usr/bin/env python3
"""Valida tarefas embutidas na seção 14 do spec.md integrado."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


SPEC_PATTERNS = {
    "US": re.compile(r"^#{4,6}\s+(US-\d{3,})\b", re.MULTILINE),
    "AC": re.compile(r"^#{4,6}\s+(AC-\d{3,})\b", re.MULTILINE),
    "FR": re.compile(r"^\s*-\s+\*\*(FR-\d{3,})\*\*\s*:", re.MULTILINE),
    "NFR": re.compile(r"^\s*-\s+\*\*(NFR-\d{3,})\*\*\s*:", re.MULTILINE),
}
HEADING = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
TASK_LINE = re.compile(r"^\s*-\s+\[([ xX])\]\s+(T\d{3,})\s+(.+)$")
CHECKLIST_LINE = re.compile(
    r"^\s{2,}-\s+\[([ xX])\]\s+\*\*"
    r"(PREP|EXECUTE|VERIFY|EVIDENCE|IMPROVE)"
    r"\*\*:\s+(.+?)\s*$"
)
NESTED_CHECKBOX = re.compile(r"^\s{2,}-\s+\[[ xX]\]\s+(.+?)\s*$")
CHECKLIST_KEYS = ("PREP", "EXECUTE", "VERIFY", "EVIDENCE", "IMPROVE")
MINIMUM_TDD_PREDECESSORS = 3
TAG = re.compile(r"\[([A-Z]+(?:-\d{3,})?)\]")
REFS_DEPENDS = re.compile(
    r"\s+[—-]\s+Refs:\s*(?P<refs>.*?)\s+[—-]\s+Depends:\s*(?P<depends>.+?)\s*$"
)
PATH_PATTERN = re.compile(
    r"(?:[\w.-]+/)+[\w.-]+|"
    r"\b[\w.-]+\.(?:cs|feature|go|html|java|js|jsx|json|kt|md|php|py|rb|rs|"
    r"sql|swift|ts|tsx|vue|yaml|yml)\b",
    re.IGNORECASE,
)


@dataclass
class ChecklistItem:
    key: str
    complete: bool
    text: str
    line_number: int


@dataclass
class Task:
    task_id: str
    complete: bool
    tags: set[str]
    refs: set[str]
    depends: set[str]
    line_number: int
    raw: str
    checklist: list[ChecklistItem] = field(default_factory=list)

    @property
    def is_tdd(self) -> bool:
        if "TEST" not in self.tags or ".feature" in self.raw.lower():
            return False
        if "TDD" in self.tags:
            return True
        lowered = self.raw.lower()
        return bool(re.search(r"\btests?[/_.]|\btest[_./]|\bspec[_./]", lowered))


def normalized_title(title: str) -> str:
    return re.sub(r"^\d+\.\s+", "", title).strip()


def section_body(text: str, title: str) -> str | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        heading = HEADING.match(line)
        if not heading:
            continue
        if normalized_title(heading.group("title")).casefold() != title.casefold():
            continue
        level = len(heading.group("marks"))
        body: list[str] = []
        for following in lines[index + 1 :]:
            next_heading = HEADING.match(following)
            if next_heading and len(next_heading.group("marks")) <= level:
                break
            body.append(following)
        return "\n".join(body).strip()
    return None


def metadata(text: str, key: str) -> str | None:
    match = re.search(
        rf"^\|\s*{re.escape(key)}\s*\|\s*(.+?)\s*\|\s*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def parse_list(value: str, pattern: str) -> set[str]:
    if value.strip().lower() == "none":
        return set()
    return set(re.findall(pattern, value))


def parse_tasks(body: str, errors: list[str], start_line: int) -> list[Task]:
    tasks: list[Task] = []
    active_task: Task | None = None
    for offset, line in enumerate(body.splitlines(), start=1):
        line_number = start_line + offset
        match = TASK_LINE.match(line)
        if match:
            task_id = match.group(2)
            rest = match.group(3)
            contract = REFS_DEPENDS.search(rest)
            if not contract:
                errors.append(
                    f"Linha {line_number} ({task_id}) não segue "
                    "'— Refs: ... — Depends: ...'."
                )
                refs: set[str] = set()
                depends: set[str] = set()
            else:
                refs = parse_list(
                    contract.group("refs"), r"\b(?:US|AC|FR|NFR)-\d{3,}\b"
                )
                depends = parse_list(contract.group("depends"), r"\bT\d{3,}\b")
            active_task = Task(
                task_id=task_id,
                complete=match.group(1).lower() == "x",
                tags=set(TAG.findall(rest)),
                refs=refs,
                depends=depends,
                line_number=line_number,
                raw=line,
            )
            tasks.append(active_task)
            continue

        if HEADING.match(line):
            active_task = None
            continue
        checklist = CHECKLIST_LINE.match(line)
        if checklist and active_task:
            active_task.checklist.append(
                ChecklistItem(
                    key=checklist.group(2),
                    complete=checklist.group(1).lower() == "x",
                    text=checklist.group(3).strip(),
                    line_number=line_number,
                )
            )
            continue
        nested = NESTED_CHECKBOX.match(line)
        if nested and active_task:
            errors.append(
                f"Linha {line_number} ({active_task.task_id}) possui item de "
                "checklist fora do formato canônico."
            )
    return tasks


def cyclic_nodes(tasks: dict[str, Task]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            cycles.add(task_id)
            return
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in tasks[task_id].depends:
            if dependency in tasks:
                visit(dependency)
                if dependency in cycles:
                    cycles.add(task_id)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in tasks:
        visit(task_id)
    return cycles


def ancestors(task: Task, tasks: dict[str, Task]) -> set[str]:
    found: set[str] = set()
    pending = list(task.depends)
    while pending:
        dependency = pending.pop()
        if dependency in found or dependency not in tasks:
            continue
        found.add(dependency)
        pending.extend(tasks[dependency].depends)
    return found


def validate(spec_path: Path, *, allow_draft: bool = False) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    if not spec_path.is_file():
        return {
            "errors": [f"Arquivo não encontrado: {spec_path}"],
            "warnings": [],
            "counts": {},
        }

    text = spec_path.read_text(encoding="utf-8")
    if metadata(text, "Formato") != "Specsfy/2.0":
        errors.append("spec.md não declara Formato | Specsfy/2.0 no cabeçalho.")
    if metadata(text, "Definition Gate") != "Passed":
        errors.append(
            "Definition Gate precisa estar Passed antes de validar tarefas."
        )
    status = metadata(text, "Status")
    if status not in {"Defined", "Planned", "Implementing", "Complete"}:
        errors.append(
            "Status precisa ser Defined, Planned, Implementing ou Complete."
        )
    plan_gate = metadata(text, "Plan Gate")
    if plan_gate not in {"Pending", "Failed", "Passed"}:
        errors.append("Plan Gate deve ser Pending, Failed ou Passed.")
    elif plan_gate != "Passed" and not allow_draft:
        errors.append("Plan Gate precisa estar Passed para validação estrita.")

    task_body = section_body(text, "Tarefas")
    if task_body is None:
        errors.append("Seção rígida 14. Tarefas ausente.")
        return {
            "errors": errors,
            "warnings": warnings,
            "status": plan_gate,
            "counts": {},
        }
    section_line_match = re.search(
        r"^###\s+14\.\s+Tarefas\s*$", text, re.MULTILINE | re.IGNORECASE
    )
    start_line = (
        text[: section_line_match.start()].count("\n") + 1
        if section_line_match
        else 0
    )

    spec_ids = {
        kind: set(pattern.findall(text)) for kind, pattern in SPEC_PATTERNS.items()
    }
    all_spec_ids = set().union(*spec_ids.values())
    tasks = parse_tasks(task_body, errors, start_line)
    if not tasks:
        errors.append("Nenhuma tarefa TNNN foi encontrada na seção 14.")
        return {
            "errors": errors,
            "warnings": warnings,
            "status": plan_gate,
            "counts": {},
        }

    duplicates = sorted(
        task_id
        for task_id, count in Counter(task.task_id for task in tasks).items()
        if count > 1
    )
    if duplicates:
        errors.append("IDs de tarefa duplicados: " + ", ".join(duplicates) + ".")
    task_map = {task.task_id: task for task in tasks}
    covered: set[str] = set()
    allowed_tags = {"P", "TEST", "TDD", "CODE", "DOC", "OPS"} | spec_ids["US"]

    for task in tasks:
        checklist_keys = [item.key for item in task.checklist]
        if checklist_keys != list(CHECKLIST_KEYS):
            errors.append(
                f"{task.task_id} deve declarar checklist canônico "
                + ", ".join(CHECKLIST_KEYS)
                + " nessa ordem."
            )
        duplicates = sorted(
            key
            for key, count in Counter(checklist_keys).items()
            if count > 1
        )
        if duplicates:
            errors.append(
                f"{task.task_id} possui itens de checklist duplicados: "
                + ", ".join(duplicates)
                + "."
            )
        open_items = [item.key for item in task.checklist if not item.complete]
        if task.complete and open_items:
            errors.append(
                f"{task.task_id} está concluída com itens de checklist abertos: "
                + ", ".join(open_items)
                + "."
            )
        if not task.complete and task.checklist and not open_items:
            errors.append(
                f"{task.task_id} está aberta, mas todos os itens do checklist "
                "estão concluídos."
            )
        unknown_tags = sorted(task.tags - allowed_tags)
        if unknown_tags:
            errors.append(
                f"{task.task_id} possui tags inválidas: {', '.join(unknown_tags)}."
            )
        types = task.tags & {"TEST", "CODE", "DOC", "OPS"}
        if len(types) != 1:
            errors.append(f"{task.task_id} deve possuir exatamente uma tag de tipo.")
        if "TDD" in task.tags and "TEST" not in task.tags:
            errors.append(f"{task.task_id} usa TDD sem a tag TEST.")
        if not PATH_PATTERN.search(task.raw):
            errors.append(f"{task.task_id} não declara caminho de arquivo exato.")
        if not task.refs:
            errors.append(f"{task.task_id} não possui referência de especificação.")
        unknown_refs = sorted(task.refs - all_spec_ids)
        if unknown_refs:
            errors.append(
                f"{task.task_id} referencia IDs inexistentes: {', '.join(unknown_refs)}."
            )
        covered.update(task.refs & all_spec_ids)
        unknown_deps = sorted(task.depends - set(task_map))
        if unknown_deps:
            errors.append(
                f"{task.task_id} depende de tarefas inexistentes: "
                + ", ".join(unknown_deps)
                + "."
            )
        if task.task_id in task.depends:
            errors.append(f"{task.task_id} depende de si mesma.")
        incomplete_dependencies = sorted(
            dependency
            for dependency in task.depends
            if dependency in task_map
            and task.complete
            and not task_map[dependency].complete
        )
        if incomplete_dependencies:
            errors.append(
                f"{task.task_id} está concluída com dependências abertas: "
                + ", ".join(incomplete_dependencies)
                + "."
            )
        checked_items = [item.key for item in task.checklist if item.complete]
        open_dependencies = sorted(
            dependency
            for dependency in task.depends
            if dependency in task_map and not task_map[dependency].complete
        )
        if checked_items and open_dependencies:
            errors.append(
                f"{task.task_id} possui progresso em checklist enquanto dependências "
                "estão abertas: "
                + ", ".join(open_dependencies)
                + "."
            )

    cycles = sorted(cyclic_nodes(task_map))
    if cycles:
        errors.append("Ciclo de dependências envolvendo: " + ", ".join(cycles) + ".")

    required_coverage = set().union(*spec_ids.values())
    uncovered = sorted(required_coverage - covered)
    if uncovered:
        errors.append("IDs da especificação sem tarefa: " + ", ".join(uncovered) + ".")

    for ac_id in sorted(spec_ids["AC"]):
        tdd = [task for task in tasks if task.is_tdd and ac_id in task.refs]
        if not tdd:
            errors.append(f"{ac_id} não possui tarefa TDD informada pelo BDD da spec.")

    tdd_tasks = [task for task in tasks if task.is_tdd]
    if len(tdd_tasks) < MINIMUM_TDD_PREDECESSORS:
        errors.append(
            "A feature possui "
            f"{len(tdd_tasks)} predecessor(es) TDD; mínimo exigido: "
            f"{MINIMUM_TDD_PREDECESSORS}."
        )
    for kind in ("US", "FR", "NFR"):
        for item in sorted(spec_ids[kind]):
            observed = sum(item in task.refs for task in tdd_tasks)
            if observed < MINIMUM_TDD_PREDECESSORS:
                errors.append(
                    f"{item} possui {observed} predecessor(es) TDD; mínimo exigido: "
                    f"{MINIMUM_TDD_PREDECESSORS}."
                )

    for task in tasks:
        if "CODE" not in task.tags:
            continue
        if not task.refs:
            errors.append(f"{task.task_id} é CODE sem referências.")
            continue
        prior_tests = [
            task_map[item]
            for item in ancestors(task, task_map)
            if item in task_map and "TEST" in task_map[item].tags
        ]
        matching_tdd = [test for test in prior_tests if test.is_tdd and test.refs & task.refs]
        if not matching_tdd:
            errors.append(
                f"{task.task_id} é CODE sem predecessor TDD cobrindo os mesmos IDs."
            )
        elif len(matching_tdd) < MINIMUM_TDD_PREDECESSORS:
            errors.append(
                f"{task.task_id} possui {len(matching_tdd)} predecessor(es) TDD "
                f"rastreáveis; mínimo exigido: {MINIMUM_TDD_PREDECESSORS}."
            )
        if plan_gate == "Passed":
            for predecessor in matching_tdd:
                if not predecessor.complete:
                    errors.append(
                        "Plan Gate exige predecessor TDD "
                        f"{predecessor.task_id} concluído antes de {task.task_id}."
                    )

    evidence_contract = metadata(text, "Evidence Contract")
    if evidence_contract:
        if evidence_contract != "1":
            errors.append(f"Evidence Contract não suportado: {evidence_contract}.")
        else:
            repository_root = next(
                (parent for parent in spec_path.parents if (parent / ".git").exists()),
                spec_path.parents[2] if len(spec_path.parents) > 2 else spec_path.parent,
            )
            verifier = (
                repository_root
                / ".agents/skills/specsfy-07-implement/scripts/verify_evidence.py"
            )
            if not verifier.is_file():
                errors.append("Evidence Contract 1 exige verify_evidence.py.")
            else:
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        str(verifier),
                        str(spec_path),
                        str(repository_root),
                        "--json",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if completed.returncode not in {0, 1}:
                    errors.append(
                        "Falha ao executar verify_evidence.py: "
                        + (completed.stderr.strip() or f"exit {completed.returncode}")
                    )
                elif completed.returncode == 1:
                    try:
                        evidence_result = json.loads(completed.stdout)
                    except json.JSONDecodeError:
                        errors.append("verify_evidence.py retornou JSON inválido.")
                    else:
                        errors.extend(
                            f"Evidência material: {message}"
                            for message in evidence_result.get("errors", [])
                        )

    return {
        "errors": errors,
        "warnings": warnings,
        "status": plan_gate,
        "counts": {
            "total": len(tasks),
            "complete": sum(task.complete for task in tasks),
            "tdd": sum(task.is_tdd for task in tasks),
            "code": sum("CODE" in task.tags for task in tasks),
            "checklist_items": sum(len(task.checklist) for task in tasks),
            "checklist_complete": sum(
                item.complete for task in tasks for item in task.checklist
            ),
            "covered_spec_ids": len(covered),
            "required_spec_ids": len(required_coverage),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="spec.md contendo a seção 14")
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Validar tarefas enquanto Plan Gate ainda está Pending/Failed",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate(args.spec.resolve(), allow_draft=args.allow_draft)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        counts = result["counts"]
        if counts:
            print("Contagens: " + " ".join(f"{key}={value}" for key, value in counts.items()))
        for error in result["errors"]:
            print(f"ERRO: {error}")
        for warning in result["warnings"]:
            print(f"AVISO: {warning}")
        if result["errors"]:
            print("RESULTADO: NOT READY")
        elif result.get("status") != "Passed":
            print("RESULTADO: VALID DRAFT")
        else:
            print("RESULTADO: READY")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
