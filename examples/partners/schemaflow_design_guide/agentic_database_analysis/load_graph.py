"""CLI helpers for loading and previewing the SchemaFlow graph."""

from __future__ import annotations

import argparse
import json
import os
from typing import Sequence

from .enrichment import enrich_column_semantics, openai_client_from_env
from .neo4j_loader import upsert_graph
from .payload import graph_to_dashboard_payload
from .seed import build_seed_graph, summarize_graph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Load the SchemaFlow sample graph into Neo4j.")
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Use OpenAI Responses API to fill missing semantic_meaning tags before loading.",
    )
    parser.add_argument(
        "--enrich-limit",
        type=int,
        default=int(os.getenv("SEED_AI_ENRICH_LIMIT", "30")),
        help="Maximum number of missing column tags to enrich.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-5.6"),
        help="OpenAI model for semantic enrichment.",
    )
    parser.add_argument(
        "--preview-json",
        action="store_true",
        help="Print dashboard JSON instead of writing to Neo4j.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    graph = build_seed_graph()

    if args.enrich:
        result = enrich_column_semantics(
            graph,
            client=openai_client_from_env(),
            model=args.model,
            limit=args.enrich_limit,
        )
        print(
            "Enrichment: "
            f"{result.updated}/{result.attempted} updated, "
            f"{result.skipped} skipped, {len(result.failures)} failure(s)."
        )
        for failure in result.failures:
            print("  -", failure)

    if args.preview_json:
        print(json.dumps(graph_to_dashboard_payload(graph), indent=2, ensure_ascii=False))
        return 0

    counts = upsert_graph(graph)
    summary = summarize_graph(graph)
    print("Seed summary:", json.dumps(summary, sort_keys=True))
    print("Neo4j upsert:", json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
