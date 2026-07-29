#!/usr/bin/env python3
"""Seleciona tarefas prontas na seção 14 do spec.md integrado."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


HEADING = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
TASK_LINE = re.compile(r"^\s*-\s+\[([ xX])\]\s+(T\d{3,})\s+(.+)$")
CHECKLIST_LINE = re.compile(
    r"^\s{2,}-\s+\[([ xX])\]\s+\*\*"
    r"(PREP|EXECUTE|VERIFY|EVIDENCE|IMPROVE)"
    r"\*\*:\s+(.+?)\s*$"
)
NESTED_CHECKBOX = re.compile(r"^\s{2,}-\s+\[[ xX]\]\s+(.+?)\s*$")
CHECKLIST_KEYS = ("PREP", "EXECUTE", "VERIFY", "EVIDENCE", "IMPROVE")
DEPENDS = re.compile(r"\s+[—-]\s+Depends:\s*(?P<depends>.+?)\s*$")


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
    depends: set[str]
    line: str
    line_number: int
    checklist: list[ChecklistItem] = field(default_factory=list)


def metadata(text: str, key: str) -> str | None:
    match = re.search(
        rf"^\|\s*{re.escape(key)}\s*\|\s*(.+?)\s*\|\s*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def task_section(text: str) -> tuple[str | None, int]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        heading = HEADING.match(line)
        if not heading:
            continue
        title = re.sub(r"^\d+\.\s+", "", heading.group("title")).strip()
        if title.casefold() != "tarefas":
            continue
        level = len(heading.group("marks"))
        body: list[str] = []
        for following in lines[index + 1 :]:
            next_heading = HEADING.match(following)
            if next_heading and len(next_heading.group("marks")) <= level:
                break
            body.append(following)
        return "\n".join(body), index + 1
    return None, 0


def parse(path: Path) -> tuple[list[Task], list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if metadata(text, "Formato") != "Specsfy/2.0":
        errors.append("spec.md não declara Formato | Specsfy/2.0 no cabeçalho.")
    if metadata(text, "Definition Gate") != "Passed":
        errors.append("Definition Gate precisa estar Passed.")
    if metadata(text, "Plan Gate") != "Passed":
        errors.append("Plan Gate precisa estar Passed.")
    if metadata(text, "Status") not in {"Planned", "Implementing", "Complete"}:
        errors.append("Status precisa ser Planned, Implementing ou Complete.")

    body, start_line = task_section(text)
    if body is None:
        errors.append("Seção 14. Tarefas ausente.")
        return [], errors

    tasks: list[Task] = []
    active_task: Task | None = None
    for offset, line in enumerate(body.splitlines(), 1):
        match = TASK_LINE.match(line)
        if match:
            contract = DEPENDS.search(match.group(3))
            if not contract:
                errors.append(f"{match.group(2)} não declara Depends.")
                dependencies: set[str] = set()
            elif contract.group("depends").strip().lower() == "none":
                dependencies = set()
            else:
                dependencies = set(
                    re.findall(r"\bT\d{3,}\b", contract.group("depends"))
                )
            active_task = Task(
                task_id=match.group(2),
                complete=match.group(1).lower() == "x",
                depends=dependencies,
                line=line.strip(),
                line_number=start_line + offset,
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
                    line_number=start_line + offset,
                )
            )
            continue
        if NESTED_CHECKBOX.match(line) and active_task:
            errors.append(
                f"{active_task.task_id} possui item de checklist fora do formato canônico."
            )

    if len({task.task_id for task in tasks}) != len(tasks):
        errors.append("A seção 14 contém IDs de tarefa duplicados.")
    for task in tasks:
        keys = [item.key for item in task.checklist]
        if keys != list(CHECKLIST_KEYS):
            errors.append(
                f"{task.task_id} deve declarar checklist canônico "
                + ", ".join(CHECKLIST_KEYS)
                + " nessa ordem."
            )
            continue
        open_items = [item.key for item in task.checklist if not item.complete]
        if task.complete and open_items:
            errors.append(
                f"{task.task_id} está concluída com checklist aberto: "
                + ", ".join(open_items)
                + "."
            )
        if not task.complete and not open_items:
            errors.append(
                f"{task.task_id} está aberta, mas seu checklist está concluído."
            )
    return tasks, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--all", action="store_true", help="Listar todas as prontas")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = args.spec.resolve()
    if not path.is_file():
        print(f"ERRO: arquivo não encontrado: {path}", file=sys.stderr)
        return 2
    tasks, errors = parse(path)
    text = path.read_text(encoding="utf-8")
    if metadata(text, "Evidence Contract") == "1":
        repository_root = next(
            (parent for parent in path.parents if (parent / ".git").exists()),
            path.parents[2] if len(path.parents) > 2 else path.parent,
        )
        verifier = (
            repository_root
            / ".agents/skills/specsfy-07-implement/scripts/verify_evidence.py"
        )
        if not verifier.is_file():
            errors.append("Evidence Contract 1 exige verify_evidence.py.")
        else:
            evidence = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(verifier),
                    str(path),
                    str(repository_root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if evidence.returncode == 1:
                try:
                    payload = json.loads(evidence.stdout)
                except json.JSONDecodeError:
                    errors.append("verify_evidence.py retornou JSON inválido.")
                else:
                    errors.extend(
                        f"Evidência material: {message}"
                        for message in payload.get("errors", [])
                    )
            elif evidence.returncode != 0:
                errors.append(
                    "Falha ao executar verify_evidence.py: "
                    + (evidence.stderr.strip() or f"exit {evidence.returncode}")
                )
    if not tasks:
        errors.append("Nenhuma tarefa encontrada na seção 14.")
    elif all(task.complete for task in tasks):
        if metadata(text, "Delivery Gate") != "Passed":
            errors.append(
                "Todas as tarefas estão concluídas, mas Delivery Gate precisa estar Passed."
            )
        if metadata(text, "Status") != "Complete":
            errors.append(
                "Todas as tarefas estão concluídas, mas Status precisa estar Complete."
            )
    elif metadata(text, "Status") == "Complete":
        errors.append("Status Complete é inválido enquanto existirem tarefas abertas.")
    task_map = {task.task_id: task for task in tasks}
    for task in tasks:
        unknown = sorted(task.depends - set(task_map))
        if unknown:
            errors.append(
                f"{task.task_id} depende de IDs inexistentes: {', '.join(unknown)}."
            )
        open_dependencies = sorted(
            dependency
            for dependency in task.depends
            if dependency in task_map and not task_map[dependency].complete
        )
        if any(item.complete for item in task.checklist) and open_dependencies:
            errors.append(
                f"{task.task_id} possui progresso em checklist enquanto aguarda "
                + ", ".join(open_dependencies)
                + "."
            )
    if errors:
        for error in errors:
            print(f"ERRO: {error}", file=sys.stderr)
        return 2

    completed = {task.task_id for task in tasks if task.complete}
    open_tasks = [task for task in tasks if not task.complete]
    ready = [task for task in open_tasks if task.depends <= completed]
    selected = ready if args.all else ready[:1]
    blocked = [
        {
            "id": task.task_id,
            "waiting_for": sorted(task.depends - completed),
            "line_number": task.line_number,
        }
        for task in open_tasks
        if task not in ready
    ]
    result = {
        "state": "complete" if not open_tasks else ("ready" if ready else "blocked"),
        "ready": [
            {
                "id": task.task_id,
                "line_number": task.line_number,
                "line": task.line,
                "progress": {
                    "complete": sum(item.complete for item in task.checklist),
                    "total": len(task.checklist),
                },
                "next_item": (
                    {
                        "key": next(
                            item.key for item in task.checklist if not item.complete
                        ),
                        "line_number": next(
                            item.line_number
                            for item in task.checklist
                            if not item.complete
                        ),
                        "text": next(
                            item.text for item in task.checklist if not item.complete
                        ),
                    }
                    if any(not item.complete for item in task.checklist)
                    else None
                ),
            }
            for task in selected
        ],
        "blocked": blocked,
        "complete_count": len(completed),
        "total_count": len(tasks),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Estado: {result['state']} ({len(completed)}/{len(tasks)} concluídas)")
        for task in selected:
            print(f"PRÓXIMA: linha {task.line_number}: {task.line}")
            complete_items = sum(item.complete for item in task.checklist)
            print(f"Progresso: {complete_items}/{len(task.checklist)}")
            next_item = next(
                (item for item in task.checklist if not item.complete),
                None,
            )
            if next_item:
                print(
                    f"PRÓXIMO ITEM: {task.task_id} {next_item.key} "
                    f"(linha {next_item.line_number}): {next_item.text}"
                )
        if result["state"] == "blocked":
            for item in blocked:
                print(f"BLOQUEADA: {item['id']} aguarda {', '.join(item['waiting_for'])}")
    return 1 if result["state"] == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
