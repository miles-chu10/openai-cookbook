"""Neo4j loader for the SchemaFlow agentic database analysis graph."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

RELATIONSHIP_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    user: str
    password: str


def normalize_neo4j_uri(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme in {"bolt", "bolt+ssc", "bolt+s", "neo4j", "neo4j+ssc", "neo4j+s"}:
        return uri
    if parsed.scheme in {"http", "https"} and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return f"neo4j://{parsed.hostname}:7687"
    return uri


def load_config_from_env() -> Neo4jConfig:
    uri = normalize_neo4j_uri(os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687").strip())
    user = os.getenv("NEO4J_USER", "neo4j").strip()
    password = os.getenv("NEO4J_PASSWORD", "")
    if not uri or not user or not password:
        raise RuntimeError("NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD are required.")
    return Neo4jConfig(uri=uri, user=user, password=password)


def validate_relationship_type(value: str) -> str:
    relationship_type = (value or "").strip().upper()
    if not RELATIONSHIP_TYPE_RE.match(relationship_type):
        raise ValueError(f"Invalid Neo4j relationship type: {value!r}")
    return relationship_type


def _node_label(object_id: str, graph: dict[str, Any]) -> str:
    return "View:SchemaFlowCookbook" if object_id in graph["views"] else "Table:SchemaFlowCookbook"


def upsert_graph(graph: dict[str, Any], config: Neo4jConfig | None = None) -> dict[str, int]:
    try:
        from neo4j import GraphDatabase
    except Exception as exc:
        raise RuntimeError("Install the Neo4j driver first: pip install neo4j") from exc

    cfg = config or load_config_from_env()
    driver = GraphDatabase.driver(cfg.uri, auth=(cfg.user, cfg.password))
    try:
        with driver.session() as session:
            return upsert_graph_with_session(session, graph)
    finally:
        driver.close()


def upsert_graph_with_session(session: Any, graph: dict[str, Any]) -> dict[str, int]:
    counts = {
        "schemas": 0,
        "tables": 0,
        "columns": 0,
        "foreign_keys": 0,
        "views": 0,
        "derived_from": 0,
        "joins": 0,
    }

    session.run("RETURN 1 AS ok").single()

    for cypher in [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Table) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Column) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (v:View) REQUIRE v.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Schema) REQUIRE s.name IS UNIQUE",
    ]:
        session.run(cypher)

    for schema in graph["schemas"]:
        session.run("MERGE (s:Schema {name:$name}) SET s:SchemaFlowCookbook", name=schema)
        counts["schemas"] += 1

    for table_id, table in graph["tables"].items():
        schema, table_name = table_id.split(".", 1)
        session.run(
            """
            MERGE (s:Schema {name:$schema})
            SET s:SchemaFlowCookbook
            MERGE (t:Table {id:$id})
              ON CREATE SET t.created_by = 'schemaflow-cookbook'
            SET t:SchemaFlowCookbook,
                t.name = $table,
                t.schema = $schema,
                t.type = 'TABLE',
                t.description = coalesce($description, t.description)
            MERGE (s)-[:CONTAINS]->(t)
            """,
            id=table_id,
            schema=schema,
            table=table_name,
            description=table.get("description"),
        )
        counts["tables"] += 1
        for column in table["columns"]:
            column_id = f"{table_id}.{column['name']}"
            session.run(
                """
                MERGE (t:Table {id:$table_id})
                SET t:SchemaFlowCookbook
                MERGE (c:Column {id:$column_id})
                  ON CREATE SET c.created_by = 'schemaflow-cookbook'
                SET c:SchemaFlowCookbook,
                    c.name = $name,
                    c.type = $data_type,
                    c.nullable = $nullable,
                    c.is_primary_key = $is_primary_key,
                    c.description = coalesce($description, c.description),
                    c.semantic_meaning = coalesce($semantic_meaning, c.semantic_meaning)
                MERGE (t)-[:HAS_COLUMN]->(c)
                """,
                table_id=table_id,
                column_id=column_id,
                name=column["name"],
                data_type=column.get("type", "UNKNOWN"),
                nullable=bool(column.get("nullable", True)),
                is_primary_key=bool(column.get("is_primary_key", False)),
                description=column.get("description"),
                semantic_meaning=column.get("semantic_meaning"),
            )
            counts["columns"] += 1

    for source_schema, source_table, source_column, target_schema, target_table, target_column in graph["foreign_keys"]:
        session.run(
            """
            MATCH (source:Column {id:$source_id})
            MATCH (target:Column {id:$target_id})
            SET source:SchemaFlowCookbook, target:SchemaFlowCookbook
            MERGE (source)-[:FK_TO]->(target)
            """,
            source_id=f"{source_schema}.{source_table}.{source_column}",
            target_id=f"{target_schema}.{target_table}.{target_column}",
        )
        counts["foreign_keys"] += 1

    for view_id, view in graph["views"].items():
        schema, view_name = view_id.split(".", 1)
        session.run(
            """
            MERGE (s:Schema {name:$schema})
            SET s:SchemaFlowCookbook
            MERGE (v:View {id:$id})
              ON CREATE SET v.created_by = 'schemaflow-cookbook'
            SET v:SchemaFlowCookbook,
                v.name = $view,
                v.schema = $schema,
                v.type = 'VIEW',
                v.description = coalesce($description, v.description)
            MERGE (s)-[:CONTAINS]->(v)
            """,
            id=view_id,
            schema=schema,
            view=view_name,
            description=view.get("description"),
        )
        counts["views"] += 1

    for source, target in graph["derived_from"]:
        source_label = _node_label(source, graph)
        target_label = _node_label(target, graph)
        session.run(
            f"MATCH (source:{source_label} {{id:$source}}), (target:{target_label} {{id:$target}}) "
            "MERGE (source)-[:DERIVED_FROM]->(target)",
            source=source,
            target=target,
        )
        counts["derived_from"] += 1

    for source, target in graph["joins"]:
        source_label = _node_label(source, graph)
        target_label = _node_label(target, graph)
        session.run(
            f"MATCH (source:{source_label} {{id:$source}}), (target:{target_label} {{id:$target}}) "
            "MERGE (source)-[:JOINS]->(target)",
            source=source,
            target=target,
        )
        counts["joins"] += 1

    return counts
