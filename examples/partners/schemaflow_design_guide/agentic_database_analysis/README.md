# Agentic Database Analysis Runtime

This directory materializes the optional Neo4j knowledge-graph and dashboard workflow outlined in `schemaflow_cookbook.ipynb`.

The notebook remains self-contained, but these files make the Section 11 graph work reusable outside Jupyter:

- `seed.py` defines the synthetic customer-loyalty schema graph.
- `enrichment.py` optionally fills missing column `semantic_meaning` tags with the OpenAI Responses API.
- `neo4j_loader.py` upserts schemas, tables, views, columns, lineage, joins, and foreign-key edges into Neo4j.
- `dashboard/server.py` serves a local FastAPI + D3 dashboard over the Neo4j graph.

## Setup

From `examples/partners/schemaflow_design_guide`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start Neo4j locally or use Neo4j Desktop/AuraDB. For a local container:

```bash
docker run -d --name schemaflow-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/change-me-please \
  neo4j:5
```

Set the connection environment:

```bash
export NEO4J_URI=neo4j://127.0.0.1:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=change-me-please
```

## Load the graph

Load the deterministic seed graph without OpenAI calls:

```bash
python -m agentic_database_analysis.load_graph
```

Optionally enrich missing column tags before loading:

```bash
export OPENAI_API_KEY=...
python -m agentic_database_analysis.load_graph --enrich --enrich-limit 30
```

To preview the dashboard JSON without touching Neo4j:

```bash
python -m agentic_database_analysis.load_graph --preview-json
```

## Launch the dashboard

```bash
python -m agentic_database_analysis.dashboard.server
```

Then open `http://127.0.0.1:8005`.

For a no-Neo4j visual smoke test, serve the deterministic seed payload instead:

```bash
SCHEMAFLOW_DASHBOARD_SOURCE=seed python -m agentic_database_analysis.dashboard.server
```

The loader labels all sample nodes with `SchemaFlowCookbook`, so the dashboard only reads this cookbook graph.
