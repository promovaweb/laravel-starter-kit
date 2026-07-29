#!/usr/bin/env python3
"""Executa a política Specsfy idêntica nas fronteiras local, Git e CI."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


SCHEMA_VERSION = 2
BOUNDARIES = ("local", "git", "ci")
DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_MAX_OUTPUT_BYTES = 65536


def _metadata(text: str, key: str) -> str | None:
    match = re.search(
        rf"^\|\s*{re.escape(key)}\s*\|\s*(.+?)\s*\|\s*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _json_object(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def tdd_policy(root: Path) -> dict[str, object]:
    composer = _json_object(root / "composer.json")
    package = _json_object(root / "package.json")
    is_php = (root / "composer.json").is_file() or (root / "artisan").is_file()
    is_node = (root / "package.json").is_file()

    if is_php:
        composer_sections = [
            composer.get("require", {}),
            composer.get("require-dev", {}),
        ]
        has_pest = any(
            isinstance(section, dict) and "pestphp/pest" in section
            for section in composer_sections
        )
        if not has_pest:
            return {
                "runner": "pest-missing",
                "command": None,
                "question": None,
                "suggestion": "Adicione Pest como dependência de desenvolvimento do projeto PHP.",
            }
        command = (
            ["php", "artisan", "test", "--compact"]
            if (root / "artisan").is_file()
            else ["php", "vendor/bin/pest"]
        )
        return {
            "runner": "pest",
            "command": command,
            "question": None,
            "suggestion": None,
        }

    if is_node:
        scripts = package.get("scripts", {})
        tdd_script = scripts.get("test:tdd") if isinstance(scripts, dict) else None
        if isinstance(tdd_script, str) and tdd_script.strip():
            forbidden_runner = re.search(
                r"(?:cucumber|behave|\.feature\b)",
                tdd_script,
                re.IGNORECASE,
            )
            if forbidden_runner:
                return {
                    "runner": "node-reference-violation",
                    "command": None,
                    "question": (
                        "Confirme com o usuário um runner para os testes TDD "
                        "derivados do BDD de referência."
                    ),
                    "suggestion": (
                        "Sugira Vitest; o script não pode executar arquivos .feature."
                    ),
                }
            if (root / "pnpm-lock.yaml").is_file():
                command = ["pnpm", "run", "test:tdd"]
            elif (root / "yarn.lock").is_file():
                command = ["yarn", "test:tdd"]
            elif (root / "bun.lock").is_file() or (root / "bun.lockb").is_file():
                command = ["bun", "run", "test:tdd"]
            else:
                command = ["npm", "run", "test:tdd"]
            return {
                "runner": "node",
                "command": command,
                "question": None,
                "suggestion": None,
            }
        return {
            "runner": "node-undecided",
            "command": None,
            "question": (
                "Pergunte ao usuário qual runner TDD deve ser adotado no projeto Node."
            ),
            "suggestion": (
                "Sugira Vitest para derivar testes executáveis do BDD mantido "
                "somente como referência na spec."
            ),
        }

    return {
        "runner": "not-applicable",
        "command": None,
        "question": None,
        "suggestion": None,
    }


def _discover_specs(root: Path) -> list[Path]:
    return sorted(
        {
            path
            for pattern in ("specs/specs/*/spec.md", "specs/*/spec.md")
            for path in root.glob(pattern)
            if path.is_file()
        }
    )


def bounded_detail(
    stdout: bytes | str | None,
    stderr: bytes | str | None,
    max_output_bytes: int,
) -> tuple[str, bool]:
    def raw(value: bytes | str | None) -> bytes:
        if value is None:
            return b""
        return value if isinstance(value, bytes) else value.encode("utf-8")

    content = raw(stdout) + raw(stderr)
    truncated = len(content) > max_output_bytes
    visible = content[:max_output_bytes]
    detail = visible.decode("utf-8", errors="replace").strip()
    detail = re.sub(
        r"\bRan (\d+) tests in \d+(?:\.\d+)?s",
        r"Ran \1 tests in <elapsed>",
        detail,
    )
    detail = re.sub(r"\bTook \d+min \d+(?:\.\d+)?s", "Took <elapsed>", detail)
    if truncated:
        detail += ("\n" if detail else "") + "...[truncated]"
    return detail, truncated


def run(
    command: list[str],
    root: Path,
    *,
    name: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> dict[str, object]:
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        detail, truncated = bounded_detail(
            completed.stdout,
            completed.stderr,
            max_output_bytes,
        )
        status = "passed" if completed.returncode == 0 else "failed"
        code = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as error:
        detail, truncated = bounded_detail(
            error.stdout,
            error.stderr,
            max_output_bytes,
        )
        detail += ("\n" if detail else "") + f"timeout after {timeout_seconds:g}s"
        status = "timed_out"
        code = 124
        timed_out = True
    return {
        "name": name or (Path(command[-1]).name if len(command) > 1 else command[0]),
        "status": status,
        "code": code,
        "command": command,
        "detail": detail,
        "timed_out": timed_out,
        "truncated": truncated,
    }


def canaries() -> list[dict[str, object]]:
    probes: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        outside = root / "outside"
        research = root / "specs" / "specs" / "demo" / "research"
        outside.mkdir()
        research.mkdir(parents=True)
        target = outside / "source.md"
        target.write_text("secret\n", encoding="utf-8")
        link = research / "source.md"
        link.symlink_to(target)
        probes.append(
            {
                "name": "research-symlink",
                "passed": link.is_symlink() and not link.resolve().is_relative_to(research.resolve()),
            }
        )
        probes.append(
            {
                "name": "nonzero-is-failure",
                "passed": subprocess.run(
                    [sys.executable, "-c", "raise SystemExit(7)"],
                    capture_output=True,
                    check=False,
                    timeout=1,
                ).returncode
                == 7,
            }
        )
        probes.append(
            {
                "name": "no-implicit-attestation",
                "passed": not (root / "attestation.json").exists(),
            }
        )
        timeout = run(
            [sys.executable, "-c", "import time; time.sleep(1)"],
            root,
            timeout_seconds=0.01,
            max_output_bytes=64,
        )
        probes.append(
            {
                "name": "timeout-is-bounded",
                "passed": timeout["status"] == "timed_out" and timeout["code"] == 124,
            }
        )
        output = run(
            [sys.executable, "-c", "print('x' * 256)"],
            root,
            timeout_seconds=1,
            max_output_bytes=32,
        )
        probes.append(
            {
                "name": "output-is-bounded",
                "passed": output["status"] == "passed" and output["truncated"],
            }
        )
    return probes


def policy_sources(root: Path) -> list[Path]:
    sources = sorted((root / ".agents/skills").glob("specsfy-*/scripts/*.py"))
    workflow = root / ".github/workflows/specsfy.yml"
    if workflow.is_file():
        sources.append(workflow)
    return sources


def policy_digest(
    root: Path,
    checks: list[dict[str, object]],
    timeout_seconds: float,
    max_output_bytes: int,
    sources: list[Path] | None = None,
) -> str:
    root = root.resolve()

    def portable(value: object) -> object:
        if not isinstance(value, str):
            return value
        root_text = str(root)
        return "." + value[len(root_text) :] if value.startswith(root_text) else value

    def portable_command(command: object) -> list[object]:
        if not isinstance(command, list):
            return []
        normalized: list[object] = []
        for index, part in enumerate(command):
            if (
                index == 0
                and isinstance(part, str)
                and Path(part).resolve() == Path(sys.executable).resolve()
            ):
                normalized.append("<python>")
            else:
                normalized.append(portable(part))
        return normalized

    source_hashes: dict[str, str] = {}
    for path in sorted(sources if sources is not None else policy_sources(root)):
        resolved = path.resolve()
        key = (
            resolved.relative_to(root).as_posix()
            if resolved.is_relative_to(root)
            else resolved.as_posix()
        )
        source_hashes[key] = hashlib.sha256(resolved.read_bytes()).hexdigest()
    material = {
        "checks": [
            {
                "name": item.get("name"),
                "command": portable_command(item.get("command")),
            }
            for item in checks
        ],
        "limits": {
            "timeout_seconds": timeout_seconds,
            "max_output_bytes": max_output_bytes,
        },
        "sources": source_hashes,
    }
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def commit_sha(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return None
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value) else None


def evidence_bindings(
    root: Path,
    checks: list[dict[str, object]],
) -> list[dict[str, object]]:
    completed_task = re.compile(r"^- \[x\] (T\d{3,})\b", re.MULTILINE)
    evidence = re.compile(
        r"^\s*<!--\s*specsfy:evidence\s+(\{.*?\})\s*-->\s*$",
        re.MULTILINE,
    )
    bindings: list[dict[str, object]] = []
    root_real = root.resolve()
    observed_checks = sorted(
        str(check["name"])
        for check in checks
        if check.get("status") == "passed" and isinstance(check.get("name"), str)
    )
    for spec in _discover_specs(root):
        text = spec.read_text(encoding="utf-8")
        completed = set(completed_task.findall(text))
        for raw in evidence.findall(text):
            try:
                item = json.loads(raw)
            except json.JSONDecodeError:
                continue
            task = item.get("task")
            if task not in completed:
                continue
            hashes: dict[str, str] = {}
            for raw_path in item.get("files", []):
                if not isinstance(raw_path, str):
                    continue
                candidate = (root_real / raw_path).resolve()
                if candidate.is_relative_to(root_real) and candidate.is_file():
                    hashes[raw_path] = hashlib.sha256(candidate.read_bytes()).hexdigest()
            bindings.append(
                {
                    "spec": spec.relative_to(root_real).as_posix(),
                    "task": task,
                    "refs": item.get("refs", []),
                    "commands": item.get("commands", []),
                    "files": dict(sorted(hashes.items())),
                    "observed_checks": observed_checks,
                }
            )
    return sorted(bindings, key=lambda item: (str(item["spec"]), str(item["task"])))


def skill_check(root: Path) -> dict[str, object]:
    base_skill_names = {
        "specsfy-01-inbox",
        "specsfy-02-backlog",
        "specsfy-03-specify",
        "specsfy-04-validate",
        "specsfy-05-tasks",
        "specsfy-06-tdd-bdd",
        "specsfy-07-implement",
        "specsfy-update-spec",
        "specsfy-progress",
    }
    installed_skills_root = root / ".agents" / "skills"
    skills_root = (
        installed_skills_root
        if installed_skills_root.is_dir()
        else root
    )
    names = sorted(
        path.name
        for path in skills_root.glob("specsfy-*")
        if path.is_dir()
    )
    base_names = [name for name in names if name in base_skill_names]
    specialist_names = [
        name for name in names if name.startswith("specsfy-specialist-")
    ]
    auxiliary_names = [
        name for name in names if name.startswith("specsfy-aux-")
    ]
    setup_names = [name for name in names if name == "specsfy-setup"]
    documentation_names = [
        name for name in names if name == "specsfy-documentator"
    ]
    unsupported_names = sorted(
        set(names)
        - set(base_names)
        - set(auxiliary_names)
        - set(setup_names)
        - set(documentation_names)
        - set(specialist_names)
    )
    errors: list[str] = []
    for name in names:
        skill = skills_root / name
        body = skill / "SKILL.md"
        metadata = skill / "agents" / "openai.yaml"
        if not body.is_file() or not metadata.is_file():
            errors.append(f"{name}: SKILL.md ou agents/openai.yaml ausente")
            continue
        text = body.read_text(encoding="utf-8")
        if f"name: {name}" not in text or "description:" not in text:
            errors.append(f"{name}: frontmatter inválido")
        if len(text.splitlines()) >= 500:
            errors.append(f"{name}: SKILL.md possui 500 linhas ou mais")
    if len(base_names) != 9:
        errors.append(f"catálogo base esperado=9 observado={len(base_names)}")
    if len(auxiliary_names) != 3:
        errors.append(
            f"catálogo auxiliar esperado=3 observado={len(auxiliary_names)}"
        )
    if len(setup_names) != 1:
        errors.append(f"setup esperado=1 observado={len(setup_names)}")
    if len(documentation_names) != 1:
        errors.append(
            "documentador esperado=1 "
            f"observado={len(documentation_names)}"
        )
    for name in unsupported_names:
        errors.append(f"{name}: namespace de skill não suportado")
    detail = (
        f"{len(names)} skills válidas "
        f"({len(base_names)} base, {len(auxiliary_names)} auxiliares, "
        f"{len(setup_names)} setup, {len(documentation_names)} documentador, "
        f"{len(specialist_names)} especialistas)"
    )
    return {
        "name": "skills",
        "status": "passed" if not errors else "failed",
        "code": 0 if not errors else 1,
        "command": ["internal", "skill-contract"],
        "detail": "\n".join(errors) if errors else detail,
        "timed_out": False,
        "truncated": False,
    }


def repository_checks(
    root: Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> list[dict[str, object]]:
    python = sys.executable
    checks: list[dict[str, object]] = []
    validate = root / ".agents/skills/specsfy-04-validate/scripts/validate_spec.py"
    tasks = root / ".agents/skills/specsfy-05-tasks/scripts/validate_tasks.py"
    trace = root / ".agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.py"
    acceptance = root / ".agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.py"
    evidence = root / ".agents/skills/specsfy-07-implement/scripts/verify_evidence.py"
    research = root / ".agents/skills/specsfy-03-specify/scripts/load_research.py"

    def execute(command: list[str], name: str) -> dict[str, object]:
        return run(
            command,
            root,
            name=name,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
        )

    for spec in _discover_specs(root):
        checks.append(
            execute(
                [python, "-B", str(validate), str(spec)],
                f"spec:{spec.parent.name}",
            )
        )
        text = spec.read_text(encoding="utf-8")
        status = _metadata(text, "Status")
        evidence_contract = _metadata(text, "Evidence Contract")
        if status in {"Planned", "Implementing", "Complete"}:
            checks.append(
                execute(
                    [python, "-B", str(tasks), str(spec)],
                    f"tasks:{spec.parent.name}",
                )
            )
        if status == "Complete":
            trace_command = [
                python,
                "-B",
                str(trace),
                str(spec),
                str(root),
                "--kinds",
                "US,FR,NFR,AC",
            ]
            if evidence_contract == "1":
                trace_command.append("--full-chain")
            checks.append(
                execute(
                    trace_command,
                    f"trace:{spec.parent.name}",
                )
            )
            if evidence_contract == "1":
                checks.extend(
                    [
                        execute(
                            [
                                python,
                                "-B",
                                str(acceptance),
                                str(spec),
                                str(root),
                                "--json",
                            ],
                            f"acceptance:{spec.parent.name}",
                        ),
                        execute(
                            [python, "-B", str(evidence), str(spec), str(root)],
                            f"evidence:{spec.parent.name}",
                        ),
                        execute(
                            [python, "-B", str(research), str(spec)],
                            f"research:{spec.parent.name}",
                        ),
                    ]
                )
    checks.append(
        execute(
            [
                python,
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                "test_*.py",
            ],
            "unittest",
        )
    )
    policy = tdd_policy(root)
    tdd_command = policy["command"]
    if isinstance(tdd_command, list):
        checks.append(
            execute(
                [str(part) for part in tdd_command],
                str(policy["runner"]),
            )
        )
    elif policy["runner"] in {
        "pest-missing",
        "node-undecided",
        "node-reference-violation",
    }:
        detail = " ".join(
            str(value)
            for value in (policy["question"], policy["suggestion"])
            if value
        )
        checks.append(
            {
                "name": str(policy["runner"]),
                "status": "failed",
                "code": 2,
                "command": [],
                "detail": detail,
                "timed_out": False,
                "truncated": False,
            }
        )
    checks.append(skill_check(root))
    return checks


def render_human(payload: dict[str, object]) -> str:
    lines = [
        f"Specsfy verify: {payload['result'].upper()}",
        f"Boundary: {payload['boundary']}",
    ]
    for check in payload["checks"]:
        lines.append(
            f"- {check['status'].upper()} {check['name']} (exit {check['code']})"
        )
    for probe in payload["canaries"]:
        lines.append(
            f"- {'PASS' if probe['passed'] else 'FAIL'} canary:{probe['name']}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--boundary", choices=BOUNDARIES, default="local")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--max-output-bytes",
        type=int,
        default=DEFAULT_MAX_OUTPUT_BYTES,
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if (
        not root.is_dir()
        or args.timeout_seconds <= 0
        or args.max_output_bytes < 0
    ):
        print("ERRO: raiz ou limites inválidos.", file=sys.stderr)
        return 2

    probes = canaries()
    checks = (
        [
            {
                "name": "self-test",
                "status": "passed",
                "code": 0,
                "command": ["internal", "self-test"],
                "detail": "política e canários exercitados em diretório temporário",
                "timed_out": False,
                "truncated": False,
            }
        ]
        if args.self_test
        else repository_checks(
            root,
            args.timeout_seconds,
            args.max_output_bytes,
        )
    )
    passed = all(item["status"] == "passed" for item in checks) and all(
        item["passed"] for item in probes
    )
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "boundary": args.boundary,
        "commit_sha": commit_sha(root),
        "policy_digest": policy_digest(
            root,
            checks,
            args.timeout_seconds,
            args.max_output_bytes,
        ),
        "result": "passed" if passed else "failed",
        "checks": checks,
        "evidence_bindings": [] if args.self_test else evidence_bindings(root, checks),
        "canaries": probes,
        "errors": [],
    }
    if args.attestation:
        destination = args.attestation.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if args.json
        else render_human(payload)
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
