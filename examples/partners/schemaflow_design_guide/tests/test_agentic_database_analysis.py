from __future__ import annotations

import sys
import unittest
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXAMPLE_DIR))

from agentic_database_analysis.neo4j_loader import normalize_neo4j_uri, validate_relationship_type
from agentic_database_analysis.payload import graph_to_dashboard_payload
from agentic_database_analysis.seed import build_seed_graph, missing_semantic_columns, summarize_graph


class AgenticDatabaseAnalysisTests(unittest.TestCase):
    def test_seed_summary_matches_notebook_section(self) -> None:
        graph = build_seed_graph()
        summary = summarize_graph(graph)
        self.assertEqual(summary["schemas"], 5)
        self.assertEqual(summary["tables"], 9)
        self.assertEqual(summary["views"], 3)
        self.assertEqual(summary["foreign_keys"], 9)
        self.assertEqual(summary["derived_from"], 18)
        self.assertEqual(summary["joins"], 7)
        self.assertGreater(summary["columns"], 30)

    def test_seed_build_isolated_from_mutation(self) -> None:
        graph = build_seed_graph()
        first_missing = missing_semantic_columns(graph)
        self.assertGreater(len(first_missing), 0)
        first_missing[0][1]["semantic_meaning"] = "test-tag"
        fresh_graph = build_seed_graph()
        fresh_missing = missing_semantic_columns(fresh_graph)
        self.assertGreater(len(fresh_missing), 0)
        self.assertIsNone(fresh_missing[0][1]["semantic_meaning"])

    def test_dashboard_payload_contains_lineage_and_columns(self) -> None:
        payload = graph_to_dashboard_payload(build_seed_graph())
        database = payload["database_hierarchy"]["SCHEMAFLOW_GRAPH_DB"]
        ods_profile = database["schemas"]["ODS"]["tables"]["ODS_CUSTOMER_PROFILE"]
        self.assertEqual(ods_profile["table_type"], "TABLE")
        self.assertIn("LOYALTY_TIER", ods_profile["columns"])
        relationship_types = {item["type"] for item in payload["relationships"]}
        self.assertIn("DERIVED_FROM", relationship_types)
        self.assertIn("JOINS", relationship_types)
        self.assertIn("FK_TO", relationship_types)

    def test_uri_normalization_accepts_neo4j_browser_url(self) -> None:
        self.assertEqual(
            normalize_neo4j_uri("http://127.0.0.1:7474"),
            "neo4j://127.0.0.1:7687",
        )
        self.assertEqual(
            normalize_neo4j_uri("neo4j+s://example.databases.neo4j.io"),
            "neo4j+s://example.databases.neo4j.io",
        )

    def test_relationship_type_validation_rejects_cypher_fragments(self) -> None:
        self.assertEqual(validate_relationship_type("derived_from"), "DERIVED_FROM")
        with self.assertRaises(ValueError):
            validate_relationship_type("DERIVED_FROM`]-() DELETE n //")


if __name__ == "__main__":
    unittest.main()
