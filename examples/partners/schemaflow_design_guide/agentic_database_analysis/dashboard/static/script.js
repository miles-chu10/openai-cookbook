const graphSvg = d3.select("#graph");
const metricsEl = document.getElementById("metrics");
const selectionEl = document.getElementById("selection");
const insightsEl = document.getElementById("insightsGrid");
const statusEl = document.getElementById("status");
const refreshButton = document.getElementById("refreshButton");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function collectGraph(data) {
  const nodes = [];
  const links = [];
  const nodeById = new Map();
  const stats = { databases: 0, schemas: 0, tables: 0, views: 0, columns: 0, insights: 0 };
  const insights = [];

  Object.entries(data.database_hierarchy || {}).forEach(([dbName, database]) => {
    stats.databases += 1;
    const dbNode = { id: dbName, name: dbName, type: "database", radius: 18 };
    nodes.push(dbNode);
    nodeById.set(dbNode.id, dbNode);

    Object.entries(database.schemas || {}).forEach(([schemaName, schema]) => {
      stats.schemas += 1;
      const schemaId = `${dbName}.${schemaName}`;
      const schemaNode = { id: schemaId, name: schemaName, type: "schema", radius: 14 };
      nodes.push(schemaNode);
      nodeById.set(schemaNode.id, schemaNode);
      links.push({ source: dbName, target: schemaId, type: "CONTAINS" });

      Object.entries(schema.tables || {}).forEach(([tableName, table]) => {
        const objectType = table.table_type === "VIEW" ? "view" : "table";
        if (objectType === "view") stats.views += 1;
        else stats.tables += 1;
        const tableId = `${dbName}.${schemaName}.${tableName}`;
        const columnNames = Object.keys(table.columns || {});
        stats.columns += columnNames.length;
        const node = {
          id: tableId,
          name: `${schemaName}.${tableName}`,
          type: objectType,
          radius: objectType === "view" ? 12 : 13,
          description: table.description || "",
          columns: table.columns || {},
        };
        nodes.push(node);
        nodeById.set(node.id, node);
        links.push({ source: schemaId, target: tableId, type: "CONTAINS" });

        columnNames.forEach((columnName) => {
          const column = table.columns[columnName];
          if (column.semantic_meaning) {
            stats.insights += 1;
            insights.push({
              table: node.name,
              column: columnName,
              type: column.data_type || "UNKNOWN",
              semantic: column.semantic_meaning,
            });
          }
        });
      });
    });
  });

  (data.relationships || []).forEach((relationship) => {
    if (nodeById.has(relationship.source) && nodeById.has(relationship.target)) {
      links.push({ ...relationship });
    }
  });

  return { nodes, links, stats, insights };
}

function renderMetrics(stats) {
  const metrics = [
    ["Databases", stats.databases],
    ["Schemas", stats.schemas],
    ["Tables", stats.tables],
    ["Views", stats.views],
    ["Columns", stats.columns],
  ];
  metricsEl.replaceChildren();
  metrics.forEach(([label, value]) => {
    const metric = document.createElement("div");
    metric.className = "metric";
    const valueEl = document.createElement("strong");
    valueEl.textContent = String(value);
    const labelEl = document.createElement("span");
    labelEl.textContent = label;
    metric.append(valueEl, labelEl);
    metricsEl.append(metric);
  });
}

function renderInsights(insights) {
  insightsEl.replaceChildren();
  insights
    .sort((a, b) => `${a.table}.${a.column}`.localeCompare(`${b.table}.${b.column}`))
    .forEach((item) => {
      const insight = document.createElement("div");
      insight.className = "insight";
      const column = document.createElement("b");
      column.textContent = item.column;
      const table = document.createElement("span");
      table.textContent = item.table;
      const semantic = document.createElement("span");
      semantic.textContent = `${item.type} · ${item.semantic}`;
      insight.append(column, table, document.createElement("br"), semantic);
      insightsEl.append(insight);
    });
}

function renderSelection(node) {
  const columns = Object.entries(node.columns || {});
  selectionEl.replaceChildren();

  const title = document.createElement("div");
  title.className = "node-title";
  title.textContent = node.name;
  const type = document.createElement("div");
  type.textContent = node.type.toUpperCase();
  const description = document.createElement("p");
  description.textContent = node.description || "No description provided.";
  selectionEl.append(title, type, description);

  if (columns.length) {
    const list = document.createElement("ul");
    list.className = "column-list";
    columns.forEach(([name, column]) => {
      const item = document.createElement("li");
      const columnName = document.createElement("code");
      columnName.textContent = name;
      const dataType = document.createElement("span");
      dataType.textContent = `${column.data_type || "UNKNOWN"}${column.nullable === false ? " · not null" : ""}`;
      const semantic = document.createElement("span");
      semantic.textContent = column.semantic_meaning || "semantic tag pending";
      item.append(
        columnName,
        document.createElement("br"),
        dataType,
        document.createElement("br"),
        semantic
      );
      list.append(item);
    });
    selectionEl.append(list);
  }
}

function nodeColor(type) {
  if (type === "database") return "#17202a";
  if (type === "schema") return "#2f6fed";
  if (type === "view") return "#268060";
  return "#d97706";
}

function renderGraph(nodes, links) {
  graphSvg.selectAll("*").remove();
  const width = graphSvg.node().clientWidth || 900;
  const height = graphSvg.node().clientHeight || 580;

  const root = graphSvg
    .attr("viewBox", [0, 0, width, height])
    .append("g");

  graphSvg.call(
    d3.zoom().scaleExtent([0.5, 2.5]).on("zoom", (event) => {
      root.attr("transform", event.transform);
    })
  );

  const simulation = d3
    .forceSimulation(nodes)
    .force("link", d3.forceLink(links).id((d) => d.id).distance((d) => (d.type === "CONTAINS" ? 78 : 130)))
    .force("charge", d3.forceManyBody().strength(-360))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide().radius((d) => d.radius + 22));

  const link = root
    .append("g")
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("class", "link")
    .attr("stroke-width", (d) => (d.type === "CONTAINS" ? 1 : 1.8))
    .attr("stroke-dasharray", (d) => (d.type === "CONTAINS" ? "2 4" : null));

  const labels = root
    .append("g")
    .selectAll("text")
    .data(links.filter((d) => d.type !== "CONTAINS"))
    .join("text")
    .attr("class", "link-label")
    .text((d) => d.type.replaceAll("_", " "));

  const node = root
    .append("g")
    .selectAll("g")
    .data(nodes)
    .join("g")
    .attr("class", "node")
    .call(
      d3
        .drag()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
    )
    .on("click", (_, d) => renderSelection(d));

  node.append("circle").attr("r", (d) => d.radius).attr("fill", (d) => nodeColor(d.type));
  node
    .append("text")
    .attr("x", (d) => d.radius + 6)
    .attr("y", 4)
    .text((d) => d.name);

  simulation.on("tick", () => {
    link
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x)
      .attr("y2", (d) => d.target.y);
    labels
      .attr("x", (d) => (d.source.x + d.target.x) / 2)
      .attr("y", (d) => (d.source.y + d.target.y) / 2);
    node.attr("transform", (d) => `translate(${d.x},${d.y})`);
  });
}

async function loadGraph() {
  setStatus("Loading graph data...");
  try {
    const response = await fetch("/api/knowledge-graph");
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    const data = await response.json();
    const graph = collectGraph(data);
    renderMetrics(graph.stats);
    renderInsights(graph.insights);
    renderGraph(graph.nodes, graph.links);
    setStatus(`Loaded ${graph.nodes.length} nodes and ${graph.links.length} links.`);
  } catch (error) {
    console.error(error);
    setStatus(`Unable to load graph: ${error.message}`, true);
  }
}

refreshButton.addEventListener("click", loadGraph);
loadGraph();
