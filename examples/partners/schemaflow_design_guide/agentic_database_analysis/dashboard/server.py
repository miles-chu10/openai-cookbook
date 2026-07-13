"""FastAPI server for the SchemaFlow Neo4j knowledge-graph dashboard."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..neo4j_loader import load_config_from_env, validate_relationship_type
from ..payload import graph_to_dashboard_payload, neo4j_records_to_dashboard_payload
from ..seed import build_seed_graph

STATIC_DIR = Path(__file__).with_name("static")

app = FastAPI(title="SchemaFlow Knowledge Graph Dashboard")


class RelationshipUpdateRequest(BaseModel):
    source_table_id: str
    target_table_id: str
    old_relationship_type: str
    new_relationship_type: str


class RelationshipDeleteRequest(BaseModel):
    source_table_id: str
    target_table_id: str
    relationship_type: str


class ColumnSemanticUpdateRequest(BaseModel):
    table_id: str
    column_name: str
    semantic_meaning: str


def _driver():
    try:
        from neo4j import GraphDatabase
    except Exception as exc:
        raise RuntimeError("Install the Neo4j driver first: pip install neo4j") from exc
    config = load_config_from_env()
    return GraphDatabase.driver(config.uri, auth=(config.user, config.password))


def _split_table_id(table_id: str) -> tuple[str, str]:
    try:
        _, schema, table = table_id.split(".", 2)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Expected table id format: db.schema.table") from exc
    return schema, table


def fetch_knowledge_graph_data() -> dict:
    if os.getenv("SCHEMAFLOW_DASHBOARD_SOURCE", "").strip().lower() == "seed":
        return graph_to_dashboard_payload(build_seed_graph())

    hierarchy_query = """
    MATCH (object:SchemaFlowCookbook)
    WHERE object:Table OR object:View
    OPTIONAL MATCH (object)-[:HAS_COLUMN]->(column:Column:SchemaFlowCookbook)
    RETURN
      object.schema AS schema_name,
      object.name AS object_name,
      object.type AS object_type,
      object.description AS description,
      collect({
        column_name: column.name,
        data_type: column.type,
        nullable: column.nullable,
        is_primary_key: column.is_primary_key,
        description: column.description,
        semantic_meaning: column.semantic_meaning
      }) AS columns
    ORDER BY schema_name, object_name
    """
    relationship_query = """
    MATCH (source:SchemaFlowCookbook)-[relationship]-(target:SchemaFlowCookbook)
    WHERE (source:Table OR source:View)
      AND (target:Table OR target:View)
      AND elementId(source) < elementId(target)
    RETURN
      source.schema AS source_schema,
      source.name AS source_name,
      target.schema AS target_schema,
      target.name AS target_name,
      type(relationship) AS relationship_type
    UNION
    MATCH (source_table:Table:SchemaFlowCookbook)-[:HAS_COLUMN]->(:Column:SchemaFlowCookbook)
      -[:FK_TO]->(:Column:SchemaFlowCookbook)<-[:HAS_COLUMN]-(target_table:Table:SchemaFlowCookbook)
    RETURN
      source_table.schema AS source_schema,
      source_table.name AS source_name,
      target_table.schema AS target_schema,
      target_table.name AS target_name,
      'FK_TO' AS relationship_type
    ORDER BY source_schema, source_name, target_schema, target_name, relationship_type
    """
    driver = _driver()
    try:
        with driver.session() as session:
            hierarchy_records = [dict(record) for record in session.run(hierarchy_query)]
            relationship_records = [dict(record) for record in session.run(relationship_query)]
    finally:
        driver.close()
    return neo4j_records_to_dashboard_payload(hierarchy_records, relationship_records)


@app.get("/api/knowledge-graph")
async def get_knowledge_graph() -> Response:
    try:
        data = fetch_knowledge_graph_data()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(content=json.dumps(data), media_type="application/json")


@app.post("/api/update-relationship")
async def update_relationship(request: RelationshipUpdateRequest) -> dict:
    source_schema, source_table = _split_table_id(request.source_table_id)
    target_schema, target_table = _split_table_id(request.target_table_id)
    old_type = validate_relationship_type(request.old_relationship_type)
    new_type = validate_relationship_type(request.new_relationship_type)
    query = f"""
    MATCH (source:SchemaFlowCookbook {{name:$source_table, schema:$source_schema}})
    MATCH (target:SchemaFlowCookbook {{name:$target_table, schema:$target_schema}})
    MATCH (source)-[relationship:`{old_type}`]-(target)
    CREATE (source)-[new_relationship:`{new_type}`]->(target)
    DELETE relationship
    RETURN type(new_relationship) AS new_type
    """
    driver = _driver()
    try:
        with driver.session() as session:
            record = session.run(
                query,
                source_table=source_table,
                source_schema=source_schema,
                target_table=target_table,
                target_schema=target_schema,
            ).single()
    finally:
        driver.close()
    if not record:
        raise HTTPException(status_code=404, detail="Relationship not found.")
    return {"status": "success", "updated_relationship": dict(record)}


@app.post("/api/delete-relationship")
async def delete_relationship(request: RelationshipDeleteRequest) -> dict:
    source_schema, source_table = _split_table_id(request.source_table_id)
    target_schema, target_table = _split_table_id(request.target_table_id)
    relationship_type = validate_relationship_type(request.relationship_type)
    query = f"""
    MATCH (source:SchemaFlowCookbook {{name:$source_table, schema:$source_schema}})
      -[relationship:`{relationship_type}`]-
      (target:SchemaFlowCookbook {{name:$target_table, schema:$target_schema}})
    DELETE relationship
    RETURN count(relationship) AS deleted_count
    """
    driver = _driver()
    try:
        with driver.session() as session:
            record = session.run(
                query,
                source_table=source_table,
                source_schema=source_schema,
                target_table=target_table,
                target_schema=target_schema,
            ).single()
    finally:
        driver.close()
    return {"status": "success", "deleted_count": record["deleted_count"] if record else 0}


@app.post("/api/update-column-semantic-meaning")
async def update_column_semantic_meaning(request: ColumnSemanticUpdateRequest) -> dict:
    schema, table = _split_table_id(request.table_id)
    query = """
    MATCH (table:Table:SchemaFlowCookbook {name:$table, schema:$schema})
      -[:HAS_COLUMN]->(column:Column:SchemaFlowCookbook {name:$column})
    SET column.semantic_meaning = $semantic_meaning
    RETURN column.name AS column_name, column.semantic_meaning AS semantic_meaning
    """
    driver = _driver()
    try:
        with driver.session() as session:
            record = session.run(
                query,
                table=table,
                schema=schema,
                column=request.column_name,
                semantic_meaning=request.semantic_meaning,
            ).single()
    finally:
        driver.close()
    if not record:
        raise HTTPException(status_code=404, detail="Column not found.")
    return {"status": "success", "updated_column": dict(record)}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main() -> None:
    import uvicorn

    port = int(os.getenv("NEO4J_DASHBOARD_PORT", "8005"))
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
