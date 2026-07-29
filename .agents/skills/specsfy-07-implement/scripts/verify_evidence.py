#!/usr/bin/env python3
"""Valida evidência material de tarefas concluídas no contrato opt-in."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


TASK = re.compile(
    r"^- \[x\] (?P<id>T\d{3,})\b(?P<body>.+?)— Refs: (?P<refs>.+?) — Depends:",
    re.MULTILINE,
)
EVIDENCE = re.compile(
    r"^\s*<!--\s*specsfy:evidence\s+(\{.*?\})\s*-->\s*$",
    re.MULTILINE,
)
DEFINED_ID = re.compile(r"\b(?:US|FR|NFR|AC)-\d{3,}\b")


def current_commit(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value) else None


def result(
    spec: Path,
    root: Path,
    task_filter: str | None,
    attestation_path: Path | None = None,
) -> dict[str, object]:
    text = spec.read_text(encoding="utf-8")
    contract = re.search(
        r"^\|\s*Evidence Contract\s*\|\s*(\d+)\s*\|\s*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    if not contract:
        return {
            "schema_version": 1,
            "result": "passed",
            "mode": "legacy",
            "tasks": [],
            "errors": [],
            "warnings": ["Evidence Contract ausente; compatibilidade legada aplicada."],
        }
    if contract.group(1) != "1":
        return {
            "schema_version": 1,
            "result": "failed",
            "mode": "strict",
            "tasks": [],
            "errors": [f"Evidence Contract não suportado: {contract.group(1)}"],
            "warnings": [],
        }

    definitions = set(DEFINED_ID.findall(text))
    payloads: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    for raw in EVIDENCE.findall(text):
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as error:
            errors.append(f"evidence JSON inválido: {error.msg}")
            continue
        task_id = item.get("task")
        if not isinstance(task_id, str):
            errors.append("evidence sem task")
            continue
        if task_id in payloads:
            errors.append(f"{task_id}: evidence duplicada")
        payloads[task_id] = item

    reports: list[dict[str, object]] = []
    root_real = root.resolve()
    for match in TASK.finditer(text):
        task_id = match.group("id")
        if task_filter and task_id != task_filter:
            continue
        if (
            "[CODE]" not in match.group("body")
            and not (attestation_path is not None and task_id in payloads)
        ):
            continue
        task_errors: list[str] = []
        item = payloads.get(task_id)
        if item is None:
            task_errors.append("evidence ausente")
        else:
            refs = item.get("refs")
            files = item.get("files")
            commands = item.get("commands")
            if not isinstance(refs, list) or not refs:
                task_errors.append("refs ausentes")
            else:
                invalid = sorted(
                    ref for ref in refs if not isinstance(ref, str) or ref not in definitions
                )
                if invalid:
                    task_errors.append("refs inválidas: " + ", ".join(map(str, invalid)))
            if not isinstance(files, list) or not files:
                task_errors.append("files ausentes")
            else:
                for raw_path in files:
                    if not isinstance(raw_path, str):
                        task_errors.append("file não textual")
                        continue
                    candidate = (root_real / raw_path).resolve()
                    if not candidate.is_relative_to(root_real) or not candidate.is_file():
                        task_errors.append(f"arquivo inexistente ou inseguro: {raw_path}")
            if not isinstance(commands, list) or not commands:
                task_errors.append("commands ausentes")
            else:
                for command in commands:
                    if (
                        not isinstance(command, dict)
                        or not isinstance(command.get("run"), str)
                        or not command.get("run")
                        or command.get("exit") != 0
                    ):
                        task_errors.append("comando sem run ou exit 0")
        reports.append({"task": task_id, "errors": task_errors})
        errors.extend(f"{task_id}: {message}" for message in task_errors)

    mode = "strict"
    if attestation_path is not None:
        mode = "attested"
        try:
            attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"atestação inválida: {error}")
            attestation = {}
        if attestation.get("schema_version") != 2:
            errors.append("atestação exige schema_version 2")
        if attestation.get("result") != "passed":
            errors.append("atestação não possui result passed")
        digest = attestation.get("policy_digest")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append("atestação possui policy_digest inválido")
        observed_commit = attestation.get("commit_sha")
        actual_commit = current_commit(root_real)
        if observed_commit is not None and observed_commit != actual_commit:
            errors.append(
                f"commit divergente: atestado={observed_commit} atual={actual_commit}"
            )
        bindings = attestation.get("evidence_bindings")
        if not isinstance(bindings, list):
            errors.append("atestação sem evidence_bindings")
            bindings = []
        try:
            spec_name = spec.relative_to(root_real).as_posix()
        except ValueError:
            spec_name = ""
            errors.append("spec fora da raiz")
        binding_by_task: dict[str, dict[str, object]] = {}
        passed_checks = {
            str(check["name"])
            for check in attestation.get("checks", [])
            if isinstance(check, dict)
            and check.get("status") == "passed"
            and isinstance(check.get("name"), str)
        }
        for binding in bindings:
            if (
                isinstance(binding, dict)
                and binding.get("spec") == spec_name
                and isinstance(binding.get("task"), str)
            ):
                task = str(binding["task"])
                if task in binding_by_task:
                    errors.append(f"{task}: binding atestado duplicado")
                binding_by_task[task] = binding
        for report in reports:
            task_id = str(report["task"])
            binding = binding_by_task.get(task_id)
            inline = payloads.get(task_id, {})
            if binding is None:
                errors.append(f"{task_id}: binding atestado ausente")
                continue
            if binding.get("refs") != inline.get("refs"):
                errors.append(f"{task_id}: refs atestadas divergentes")
            if binding.get("commands") != inline.get("commands"):
                errors.append(f"{task_id}: comandos atestados divergentes")
            observed_checks = binding.get("observed_checks")
            if (
                not isinstance(observed_checks, list)
                or not observed_checks
                or any(
                    not isinstance(name, str) or name not in passed_checks
                    for name in observed_checks
                )
            ):
                errors.append(f"{task_id}: checks atestados ausentes ou divergentes")
            bound_files = binding.get("files")
            if not isinstance(bound_files, dict):
                errors.append(f"{task_id}: hashes atestados ausentes")
                continue
            for raw_path in inline.get("files", []):
                if not isinstance(raw_path, str):
                    continue
                candidate = (root_real / raw_path).resolve()
                if not candidate.is_relative_to(root_real) or not candidate.is_file():
                    continue
                actual_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
                expected_hash = bound_files.get(raw_path)
                if expected_hash != actual_hash:
                    errors.append(
                        f"{task_id}: hash divergente para {raw_path}: "
                        f"atestado={expected_hash} atual={actual_hash}"
                    )

    return {
        "schema_version": 1,
        "result": "passed" if not errors else "failed",
        "mode": mode,
        "tasks": reports,
        "errors": errors,
        "warnings": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("root", type=Path)
    parser.add_argument("--task")
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.spec.is_file() or not args.root.is_dir():
        print("ERRO: spec ou raiz inexistente.", file=sys.stderr)
        return 2
    payload = result(
        args.spec.resolve(),
        args.root.resolve(),
        args.task,
        args.attestation.resolve() if args.attestation else None,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Evidência: {payload['result'].upper()} ({payload['mode']})")
        for error in payload["errors"]:
            print(f"ERRO: {error}")
        for warning in payload["warnings"]:
            print(f"AVISO: {warning}")
    return 0 if payload["result"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
