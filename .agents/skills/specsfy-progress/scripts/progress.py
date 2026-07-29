#!/usr/bin/env python3
"""Consolida o progresso do Specsfy sem alterar o estado do repositório."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


METADATA_RE = re.compile(
    r"^\|\s*(Formato|Slug|Status|Definition Gate|Plan Gate|Delivery Gate)\s*\|"
    r"\s*(.+?)\s*\|\s*$",
    re.MULTILINE | re.IGNORECASE,
)
TASK_SECTION_RE = re.compile(
    r"(?ms)^### 14\. Tarefas\s*$\n(.*?)(?=^### 15\. Ordem de execução\s*$)"
)
TASK_RE = re.compile(
    r"(?ms)^- \[([ xX])\] (T\d{3,})\s+(.+?)"
    r"\s+— Refs:\s*(.+?)\s+— Depends:\s*(.+?)\s*$"
    r"(.*?)(?=^- \[[ xX]\] T\d{3,}\b|\Z)"
)
CHECKLIST_RE = re.compile(
    r"(?m)^\s{2}- \[([ xX])\] "
    r"\*\*(PREP|EXECUTE|VERIFY|EVIDENCE|IMPROVE)\*\*:\s*(.+?)\s*$"
)
ID_RE = re.compile(r"\b(?:US|FR|NFR|AC)-\d{3,}\b")
EXPECTED_ITEMS = ("PREP", "EXECUTE", "VERIFY", "EVIDENCE", "IMPROVE")


@dataclass(frozen=True)
class ChecklistItem:
    name: str
    complete: bool
    description: str


@dataclass(frozen=True)
class Task:
    task_id: str
    complete: bool
    description: str
    dependencies: tuple[str, ...]
    checklist: tuple[ChecklistItem, ...]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resume o progresso de specs/specs/*/spec.md sem modificar arquivos."
    )
    parser.add_argument("root", nargs="?", default=".", help="Raiz do repositório")
    parser.add_argument("--slug", help="Limita o relatório a uma especificação")
    parser.add_argument("--json", action="store_true", help="Emite JSON")
    return parser.parse_args(argv)


def percentage(complete: int, total: int) -> float:
    return round((complete / total) * 100, 1) if total else 0.0


def metric(complete: int, total: int) -> dict[str, int | float]:
    return {
        "complete": complete,
        "total": total,
        "percent": percentage(complete, total),
    }


def discover_specs(root: Path, slug: str | None) -> list[Path]:
    paths = sorted(
        {
            path
            for pattern in ("specs/specs/*/spec.md", "specs/*/spec.md")
            for path in root.glob(pattern)
            if path.is_file()
        }
    )
    if slug is not None:
        paths = [path for path in paths if path.parent.name == slug]
    return paths


def parse_tasks(text: str) -> tuple[list[Task], list[str]]:
    section_match = TASK_SECTION_RE.search(text)
    if not section_match:
        return [], ["Seção `### 14. Tarefas` ausente ou sem limite `### 15`."]

    tasks: list[Task] = []
    issues: list[str] = []
    for match in TASK_RE.finditer(section_match.group(1)):
        parent_complete = match.group(1).lower() == "x"
        task_id = match.group(2)
        dependencies_text = match.group(5).strip()
        dependencies = (
            ()
            if dependencies_text.lower() == "none"
            else tuple(re.findall(r"\bT\d{3,}\b", dependencies_text))
        )
        checklist = tuple(
            ChecklistItem(
                name=item.group(2),
                complete=item.group(1).lower() == "x",
                description=item.group(3).strip(),
            )
            for item in CHECKLIST_RE.finditer(match.group(6))
        )
        names = tuple(item.name for item in checklist)
        if names != EXPECTED_ITEMS:
            issues.append(
                f"{task_id}: checklist deve ser "
                f"{'/'.join(EXPECTED_ITEMS)}; encontrado "
                f"{'/'.join(names) if names else 'nenhum'}."
            )
        if parent_complete and any(not item.complete for item in checklist):
            issues.append(f"{task_id}: tarefa concluída possui item de checklist aberto.")
        if not parent_complete and checklist and all(item.complete for item in checklist):
            issues.append(f"{task_id}: tarefa aberta possui checklist totalmente concluído.")
        tasks.append(
            Task(
                task_id=task_id,
                complete=parent_complete,
                description=match.group(3).strip(),
                dependencies=dependencies,
                checklist=checklist,
            )
        )

    return tasks, issues


def find_next(
    tasks: list[Task],
    *,
    definition_gate: str,
    plan_gate: str,
) -> dict[str, object] | None:
    if definition_gate != "Passed" or plan_gate != "Passed":
        return None
    completed = {task.task_id for task in tasks if task.complete}
    for task in tasks:
        if task.complete or not set(task.dependencies).issubset(completed):
            continue
        next_item = next((item for item in task.checklist if not item.complete), None)
        if next_item is None:
            continue
        return {
            "task": task.task_id,
            "item": next_item.name,
            "description": next_item.description,
            "waiting_for": [],
        }
    return None


def analyze_spec(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    metadata = dict(METADATA_RE.findall(text))
    tasks, issues = parse_tasks(text)
    slug = metadata.get("Slug", path.parent.name)
    status = metadata.get("Status", "Unknown")
    gates = {
        "definition": metadata.get("Definition Gate", "Missing"),
        "plan": metadata.get("Plan Gate", "Missing"),
        "delivery": metadata.get("Delivery Gate", "Missing"),
    }
    blockers = list(issues)
    if metadata.get("Formato") != "Specsfy/2.0":
        blockers.append("Formato deve ser Specsfy/2.0.")
    if gates["plan"] == "Passed" and not tasks:
        blockers.append("Plan Gate está Passed, mas nenhuma tarefa foi reconhecida.")
    for name, value in gates.items():
        if value in {"Failed", "Missing"}:
            blockers.append(f"{name.title()} Gate: {value}.")

    completed_ids = {task.task_id for task in tasks if task.complete}
    open_tasks = [task for task in tasks if not task.complete]
    ready_tasks = [
        task
        for task in open_tasks
        if set(task.dependencies).issubset(completed_ids)
    ]
    if (
        open_tasks
        and gates["definition"] == "Passed"
        and gates["plan"] == "Passed"
        and not ready_tasks
    ):
        blockers.append("Há tarefas abertas, mas nenhuma possui dependências satisfeitas.")

    next_item = find_next(
        tasks,
        definition_gate=gates["definition"],
        plan_gate=gates["plan"],
    )
    task_complete = sum(task.complete for task in tasks)
    checklist_total = sum(len(task.checklist) for task in tasks)
    checklist_complete = sum(
        item.complete for task in tasks for item in task.checklist
    )
    ids = {
        kind: len(set(re.findall(rf"\b{kind}-\d{{3,}}\b", text)))
        for kind in ("US", "FR", "NFR", "AC")
    }

    if status == "Complete" and not blockers:
        health = "complete"
    elif blockers:
        health = "blocked"
    else:
        health = "in_progress"

    acts = {
        "Draft": "Ato I — Definir",
        "Defined": "Ato II — Projetar e provar",
        "Planned": "Ato III — Entregar e validar",
        "Implementing": "Ato III — Entregar e validar",
        "Complete": "Ato III — Entregar e validar",
    }
    next_skill = {
        "Draft": "specsfy-02-backlog",
        "Defined": "specsfy-05-tasks" if not tasks else "specsfy-06-tdd-bdd",
        "Planned": "specsfy-07-implement",
        "Implementing": "specsfy-07-implement",
        "Complete": None,
    }.get(status)

    return {
        "slug": slug,
        "path": str(path),
        "status": status,
        "health": health,
        "act": acts.get(status, "Unknown"),
        "next_skill": next_skill,
        "gates": gates,
        "tasks": metric(task_complete, len(tasks)),
        "checklists": metric(checklist_complete, checklist_total),
        "ids": ids,
        "blockers": blockers,
        "next": next_item,
    }


def build_report(root: Path, paths: list[Path]) -> dict[str, object]:
    specs = [analyze_spec(path) for path in paths]
    complete_specs = sum(spec["status"] == "Complete" for spec in specs)
    passed_gates = sum(
        value == "Passed"
        for spec in specs
        for value in spec["gates"].values()
    )
    tasks_complete = sum(int(spec["tasks"]["complete"]) for spec in specs)
    tasks_total = sum(int(spec["tasks"]["total"]) for spec in specs)
    checklist_complete = sum(int(spec["checklists"]["complete"]) for spec in specs)
    checklist_total = sum(int(spec["checklists"]["total"]) for spec in specs)
    ids = {
        kind: sum(int(spec["ids"][kind]) for spec in specs)
        for kind in ("US", "FR", "NFR", "AC")
    }
    blocker_count = sum(len(spec["blockers"]) for spec in specs)
    return {
        "root": str(root),
        "summary": {
            "total_specs": len(specs),
            "complete_specs": complete_specs,
            "gates": metric(passed_gates, len(specs) * 3),
            "tasks": metric(tasks_complete, tasks_total),
            "checklists": metric(checklist_complete, checklist_total),
            "ids": ids,
            "blockers": blocker_count,
        },
        "specs": specs,
    }


def ratio(values: dict[str, int | float]) -> str:
    return f"{values['complete']}/{values['total']} ({values['percent']:.1f}%)"


def render_human(report: dict[str, object]) -> str:
    summary = report["summary"]
    lines = [
        "Progresso geral",
        (
            f"Especificações: {summary['complete_specs']}/"
            f"{summary['total_specs']} completas"
        ),
        f"Gates: {ratio(summary['gates'])}",
        f"Tarefas: {ratio(summary['tasks'])}",
        f"Checklists: {ratio(summary['checklists'])}",
        f"Blockers: {summary['blockers']}",
        "",
        "Por especificação",
    ]
    for spec in report["specs"]:
        next_item = spec["next"]
        next_text = (
            f"{next_item['task']}/{next_item['item']}" if next_item else "—"
        )
        handoff = f"${spec['next_skill']}" if spec["next_skill"] else "—"
        passed = sum(value == "Passed" for value in spec["gates"].values())
        lines.append(
            f"- {spec['slug']} [{spec['status']}] "
            f"{spec['act']} | "
            f"Gates {passed}/3 | Tarefas {ratio(spec['tasks'])} | "
            f"Checklists {ratio(spec['checklists'])} | Próximo: {next_text} | "
            f"Handoff: {handoff}"
        )

    blocked = [spec for spec in report["specs"] if spec["blockers"]]
    if blocked:
        lines.extend(["", "Bloqueios"])
        for spec in blocked:
            for blocker in spec["blockers"]:
                lines.append(f"- {spec['slug']}: {blocker}")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    paths = discover_specs(root, args.slug)
    if not paths:
        scope = f" para o slug `{args.slug}`" if args.slug else ""
        print(
            "Nenhuma especificação encontrada"
            f"{scope}. Crie `specs/specs/<NNNN>-<slug>/spec.md` com `$specsfy-03-specify`.",
            file=sys.stderr,
        )
        return 2

    report = build_report(root, paths)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_human(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
