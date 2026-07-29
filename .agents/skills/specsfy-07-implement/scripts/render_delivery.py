#!/usr/bin/env python3
"""Renderiza resumo de entrega para stdout sem criar uma nova fonte."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def metadata(text: str, key: str) -> str:
    match = re.search(
        rf"^\|\s*{re.escape(key)}\s*\|\s*(.+?)\s*\|\s*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    return match.group(1).strip() if match else "Unknown"


def ids(text: str) -> list[str]:
    return sorted(
        set(
            re.findall(
                r"(?:^\s*-\s+\*\*|^#{4,6}\s+)((?:FR|NFR|AC)-\d{3,})\b",
                text,
                re.MULTILINE,
            )
        )
    )


def build(text: str, preview: bool) -> dict[str, object]:
    gates = {
        "definition": metadata(text, "Definition Gate"),
        "plan": metadata(text, "Plan Gate"),
        "delivery": metadata(text, "Delivery Gate"),
    }
    tasks = [
        {"id": task, "complete": mark.lower() == "x", "summary": summary.strip()}
        for mark, task, summary in re.findall(
            r"^-\s+\[([ xX])\]\s+(T\d{3,})\b(.+)$", text, re.MULTILINE
        )
    ]
    risks_match = re.search(
        r"^####\s+Riscos\s*$\n(.*?)(?=^####\s+|^###\s+|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    evidence: list[dict[str, object]] = []
    for raw in re.findall(
        r"^\s*<!--\s*specsfy:evidence\s+(\{.*\})\s*-->\s*$",
        text,
        re.MULTILINE,
    ):
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        evidence.append(item)
    evidence.sort(key=lambda item: str(item.get("task", "")))
    return {
        "schema_version": 1,
        "preview": preview,
        "status": metadata(text, "Status"),
        "gates": gates,
        "delivered_ids": ids(text),
        "tasks": tasks,
        "evidence": evidence,
        "risks_and_rollback": risks_match.group(1).strip() if risks_match else "",
    }


def markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Resumo de entrega Specsfy",
        "",
        f"- Status: {payload['status']}",
        f"- Definition Gate: {payload['gates']['definition']}",
        f"- Plan Gate: {payload['gates']['plan']}",
        f"- Delivery Gate: {payload['gates']['delivery']}",
        "",
        "## IDs entregues",
        "",
        ", ".join(payload["delivered_ids"]) or "Nenhum.",
        "",
        "## Tarefas",
        "",
    ]
    lines.extend(
        f"- [{'x' if task['complete'] else ' '}] {task['id']}{task['summary']}"
        for task in payload["tasks"]
    )
    lines.extend(["", "## Evidências", ""])
    lines.extend(
        f"- {item.get('task', 'sem task')}: "
        + ", ".join(
            str(command.get("run", ""))
            for command in item.get("commands", [])
            if isinstance(command, dict)
        )
        for item in payload["evidence"]
    )
    lines.extend(
        [
            "",
            "## Riscos e rollback",
            "",
            payload["risks_and_rollback"] or "Nenhum risco/rollback registrado.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    if not args.spec.is_file():
        print("ERRO: spec inexistente.", file=sys.stderr)
        return 2
    text = args.spec.read_text(encoding="utf-8")
    payload = build(text, args.preview)
    open_tasks = [task["id"] for task in payload["tasks"] if not task["complete"]]
    if not args.preview and (
        payload["gates"]["delivery"] != "Passed" or open_tasks
    ):
        error = "resumo final exige Delivery Gate Passed e nenhuma tarefa aberta"
        if args.format == "json":
            payload["result"] = "failed"
            payload["errors"] = [error]
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"ERRO: {error}", file=sys.stderr)
        return 1
    payload["result"] = "passed"
    payload["errors"] = []
    print(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if args.format == "json"
        else markdown(payload)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
