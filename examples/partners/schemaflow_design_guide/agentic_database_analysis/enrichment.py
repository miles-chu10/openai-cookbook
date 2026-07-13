"""Optional OpenAI semantic-tag enrichment for SchemaFlow columns."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

from .seed import missing_semantic_columns

ENRICH_SYSTEM = (
    "You are a data architect assistant. Provide concise semantic-meaning tags "
    "for database columns. Return only a 2-5 word tag, no preamble."
)

TAG_RE = re.compile(r"[^a-z0-9-]+")


@dataclass
class EnrichmentResult:
    updated: int
    attempted: int
    skipped: int
    model: str
    failures: list[str] = field(default_factory=list)


def openai_client_from_env() -> Any:
    try:
        from openai import OpenAI
    except Exception as exc:
        raise RuntimeError("Install the OpenAI Python package first: pip install -U openai") from exc
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise RuntimeError("OPENAI_API_KEY is required for semantic enrichment.")
    return OpenAI()


def extract_response_text(response: Any) -> str:
    text = (getattr(response, "output_text", None) or "").strip()
    if text:
        return text
    for item in getattr(response, "output", []) or []:
        for part in getattr(item, "content", []) or []:
            value = getattr(part, "text", None)
            if isinstance(value, str):
                text += value
            elif isinstance(part, dict):
                text += part.get("text", "")
    return text.strip()


def normalize_tag(value: str) -> str | None:
    tag = value.strip().strip('"').strip("'").strip(".").lower()
    tag = re.sub(r"\s+", "-", tag)
    tag = TAG_RE.sub("", tag)
    tag = re.sub(r"-{2,}", "-", tag).strip("-")
    if not tag:
        return None
    return tag[:64]


def enrich_column_semantics(
    graph: dict[str, Any],
    *,
    client: Any,
    model: str,
    limit: int = 30,
) -> EnrichmentResult:
    missing = missing_semantic_columns(graph)
    selected = missing[: max(0, limit)]
    result = EnrichmentResult(
        updated=0,
        attempted=len(selected),
        skipped=max(0, len(missing) - len(selected)),
        model=model,
    )

    for table_id, column in selected:
        prompt = (
            f"Provide a short semantic-meaning tag for column '{column['name']}' "
            f"in table '{table_id}'. Data type: '{column.get('type', 'UNKNOWN')}'. "
            "Valid examples: natural-key, foreign-key, surrogate-key, monetary-amount, "
            "timestamp, descriptive-text, category-code, count, boolean-flag."
        )
        try:
            response = client.responses.create(
                model=model,
                store=False,
                input=[
                    {"role": "system", "content": ENRICH_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
            tag = normalize_tag(extract_response_text(response))
            if tag:
                column["semantic_meaning"] = tag
                result.updated += 1
            else:
                result.failures.append(f"{table_id}.{column['name']}: empty tag")
        except Exception as exc:
            result.failures.append(f"{table_id}.{column['name']}: {type(exc).__name__}: {exc}")

    return result
