#!/usr/bin/env python3
"""Estima contexto por seção ou ingere métricas reais explicitamente fornecidas."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path


HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def estimated(text: str) -> dict[str, object]:
    matches = list(HEADING.finditer(text))
    sections: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.start() : end]
        sections.append(
            {
                "name": match.group(2).strip(),
                "source": "estimated",
                "unit": "tokens",
                "value": math.ceil(len(body) / 4),
                "characters": len(body),
            }
        )
    return {
        "schema_version": 1,
        "result": "passed",
        "source": "estimated",
        "method": (
            "arredondamento para cima de caracteres UTF-8 / 4; "
            "aproximação, não é saída de tokenizer"
        ),
        "total": {
            "source": "estimated",
            "unit": "tokens",
            "value": math.ceil(len(text) / 4),
        },
        "sections": sections,
        "errors": [],
    }


def measured(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"usage-json inválido: {error}") from error
    input_tokens = data.get("input_tokens")
    output_tokens = data.get("output_tokens")
    if (
        not isinstance(input_tokens, int)
        or isinstance(input_tokens, bool)
        or input_tokens < 0
        or not isinstance(output_tokens, int)
        or isinstance(output_tokens, bool)
        or output_tokens < 0
    ):
        raise ValueError("usage-json exige input_tokens/output_tokens inteiros não negativos")
    return {
        "schema_version": 1,
        "result": "passed",
        "source": "measured",
        "method": "explicit usage-json",
        "total": {
            "source": "measured",
            "unit": "tokens",
            "value": input_tokens + output_tokens,
        },
        "input": {"source": "measured", "unit": "tokens", "value": input_tokens},
        "output": {"source": "measured", "unit": "tokens", "value": output_tokens},
        "sections": [],
        "errors": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--usage-json", type=Path)
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.spec.is_file():
        print("ERRO: spec inexistente.", file=sys.stderr)
        return 2
    try:
        payload = (
            measured(args.usage_json)
            if args.usage_json
            else estimated(args.spec.read_text(encoding="utf-8"))
        )
        if args.compare:
            other = (
                measured(args.compare)
                if args.usage_json
                else estimated(args.compare.read_text(encoding="utf-8"))
            )
            payload["comparison"] = {
                "source": payload["source"],
                "unit": "tokens",
                "delta": payload["total"]["value"] - other["total"]["value"],
                "current": payload["total"]["value"],
                "baseline": other["total"]["value"],
            }
    except ValueError as error:
        print(f"ERRO: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            f"Contexto: {payload['total']['value']} tokens "
            f"({payload['source']}; {payload['method']})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
