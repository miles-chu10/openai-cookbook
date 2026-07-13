"""Dashboard payload builders for SchemaFlow graph data."""

from __future__ import annotations

from typing import Any

DB_NAME = "SCHEMAFLOW_GRAPH_DB"


def _table_node_id(schema: str, name: str, db_name: str = DB_NAME) -> str:
    return f"{db_name}.{schema}.{name}"


def _split_object_id(object_id: str) -> tuple[str, str]:
    return object_id.split(".", 1)


def _table_payload(table: dict[str, Any], table_type: str) -> dict[str, Any]:
    columns = {}
    for column in table.get("columns", []):
        column_name = column["name"]
        columns[column_name] = {
            "column_name": column_name,
            "data_type": column.get("type") or "UNKNOWN",
            "nullable": bool(column.get("nullable", True)),
            "is_primary_key": bool(column.get("is_primary_key", False)),
            "description": column.get("description"),
            "semantic_meaning": column.get("semantic_meaning"),
        }
    return {
        "table_type": table_type,
        "description": table.get("description"),
        "columns": columns,
    }


def graph_to_dashboard_payload(graph: dict[str, Any], db_name: str = DB_NAME) -> dict[str, Any]:
    hierarchy: dict[str, Any] = {db_name: {"schemas": {}}}
    relationships = []

    for schema in graph["schemas"]:
        hierarchy[db_name]["schemas"][schema] = {"tables": {}}

    for table_id, table in graph["tables"].items():
        schema, table_name = _split_object_id(table_id)
        hierarchy[db_name]["schemas"].setdefault(schema, {"tables": {}})
        hierarchy[db_name]["schemas"][schema]["tables"][table_name] = _table_payload(table, "TABLE")

    for view_id, view in graph["views"].items():
        schema, view_name = _split_object_id(view_id)
        hierarchy[db_name]["schemas"].setdefault(schema, {"tables": {}})
        hierarchy[db_name]["schemas"][schema]["tables"][view_name] = _table_payload(view, "VIEW")

    for source, target in graph["derived_from"]:
        source_schema, source_name = _split_object_id(source)
        target_schema, target_name = _split_object_id(target)
        relationships.append(
            {
                "source": _table_node_id(source_schema, source_name, db_name),
                "target": _table_node_id(target_schema, target_name, db_name),
                "type": "DERIVED_FROM",
            }
        )

    for source, target in graph["joins"]:
        source_schema, source_name = _split_object_id(source)
        target_schema, target_name = _split_object_id(target)
        relationships.append(
            {
                "source": _table_node_id(source_schema, source_name, db_name),
                "target": _table_node_id(target_schema, target_name, db_name),
                "type": "JOINS",
            }
        )

    for source_schema, source_table, _, target_schema, target_table, _ in graph["foreign_keys"]:
        relationships.append(
            {
                "source": _table_node_id(source_schema, source_table, db_name),
                "target": _table_node_id(target_schema, target_table, db_name),
                "type": "FK_TO",
            }
        )

    return {"database_hierarchy": hierarchy, "relationships": relationships}


def neo4j_records_to_dashboard_payload(
    hierarchy_records: list[dict[str, Any]],
    relationship_records: list[dict[str, Any]],
    db_name: str = DB_NAME,
) -> dict[str, Any]:
    hierarchy: dict[str, Any] = {db_name: {"schemas": {}}}
    relationships = []

    for record in hierarchy_records:
        schema = record.get("schema_name") or "default_schema"
        name = record.get("object_name")
        if not name:
            continue
        hierarchy[db_name]["schemas"].setdefault(schema, {"tables": {}})
        columns = {}
        for column in record.get("columns") or []:
            if not column or not column.get("column_name"):
                continue
            columns[column["column_name"]] = column
        hierarchy[db_name]["schemas"][schema]["tables"][name] = {
            "table_type": record.get("object_type") or "TABLE",
            "description": record.get("description"),
            "columns": columns,
        }

    for record in relationship_records:
        source_schema = record.get("source_schema")
        source_name = record.get("source_name")
        target_schema = record.get("target_schema")
        target_name = record.get("target_name")
        relationship_type = record.get("relationship_type")
        if not all([source_schema, source_name, target_schema, target_name, relationship_type]):
            continue
        relationships.append(
            {
                "source": _table_node_id(source_schema, source_name, db_name),
                "target": _table_node_id(target_schema, target_name, db_name),
                "type": relationship_type,
            }
        )

    return {"database_hierarchy": hierarchy, "relationships": relationships}
