"""Synthetic SchemaFlow graph used by the notebook and dashboard runtime."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SCHEMAS = ["ODS", "STG", "CORE", "MARTS", "CRM"]

TABLES: dict[str, dict[str, Any]] = {
    "ODS.ODS_CUSTOMER_PROFILE": {
        "description": "Raw customer profile table that receives LOYALTY_TIER in this change.",
        "primary_key": ["CUSTOMER_ID"],
        "columns": [
            {
                "name": "CUSTOMER_ID",
                "type": "VARCHAR(32)",
                "nullable": False,
                "description": "Stable customer identifier from the source system.",
                "semantic_meaning": "customer-identifier",
            },
            {
                "name": "EMAIL_HASH",
                "type": "VARCHAR(64)",
                "nullable": True,
                "description": "Hashed email value used for matching without exposing PII.",
            },
            {"name": "CUSTOMER_STATUS", "type": "VARCHAR(20)", "nullable": True},
            {
                "name": "LOYALTY_TIER",
                "type": "VARCHAR(20)",
                "nullable": True,
                "description": "Nullable loyalty segment added by the change request and backfilled from CORE.DIM_CUSTOMER.",
                "semantic_meaning": "loyalty-segment",
            },
            {"name": "UPDATED_AT", "type": "TIMESTAMP", "nullable": True},
            {"name": "INGESTED_AT", "type": "TIMESTAMP", "nullable": True},
        ],
    },
    "ODS.ODS_ORDER": {
        "description": "Raw order header feed used to measure loyalty-tier revenue impact.",
        "primary_key": ["ORDER_ID"],
        "columns": [
            {
                "name": "ORDER_ID",
                "type": "VARCHAR(40)",
                "nullable": False,
                "semantic_meaning": "order-identifier",
            },
            {"name": "ORDER_TS", "type": "TIMESTAMP", "nullable": False},
            {"name": "CUSTOMER_ID", "type": "VARCHAR(32)", "nullable": True},
            {"name": "ORDER_STATUS", "type": "VARCHAR(30)", "nullable": True},
            {"name": "NET_AMOUNT", "type": "NUMERIC(12,2)", "nullable": True},
        ],
    },
    "STG.STG_CUSTOMER_PROFILE": {
        "description": "Staging table that normalizes customer profile rows for downstream dimensions and views.",
        "primary_key": ["CUSTOMER_ID"],
        "columns": [
            {
                "name": "CUSTOMER_ID",
                "type": "VARCHAR(32)",
                "nullable": False,
                "semantic_meaning": "customer-identifier",
            },
            {"name": "CUSTOMER_STATUS", "type": "VARCHAR(20)", "nullable": True},
            {
                "name": "LOYALTY_TIER",
                "type": "VARCHAR(20)",
                "nullable": True,
                "description": "Propagated loyalty segment from ODS.ODS_CUSTOMER_PROFILE.",
                "semantic_meaning": "loyalty-segment",
            },
            {"name": "PROFILE_UPDATED_AT", "type": "TIMESTAMP", "nullable": True},
        ],
    },
    "STG.STG_ORDER_ENRICHED": {
        "description": "Staging order table enriched with customer status and loyalty tier for metrics.",
        "primary_key": ["ORDER_ID"],
        "columns": [
            {"name": "ORDER_ID", "type": "VARCHAR(40)", "nullable": False},
            {"name": "CUSTOMER_ID", "type": "VARCHAR(32)", "nullable": True},
            {
                "name": "LOYALTY_TIER",
                "type": "VARCHAR(20)",
                "nullable": True,
                "semantic_meaning": "loyalty-segment",
            },
            {"name": "ORDER_TS", "type": "TIMESTAMP", "nullable": False},
            {"name": "NET_AMOUNT", "type": "NUMERIC(12,2)", "nullable": True},
        ],
    },
    "CORE.DIM_CUSTOMER": {
        "description": "Conformed customer dimension and source for the LOYALTY_TIER backfill.",
        "primary_key": ["CUSTOMER_SK"],
        "columns": [
            {
                "name": "CUSTOMER_SK",
                "type": "BIGINT",
                "nullable": False,
                "semantic_meaning": "surrogate-key",
            },
            {
                "name": "CUSTOMER_ID",
                "type": "VARCHAR(32)",
                "nullable": False,
                "semantic_meaning": "customer-identifier",
            },
            {"name": "EMAIL_HASH", "type": "VARCHAR(64)", "nullable": True},
            {"name": "COUNTRY_CODE", "type": "VARCHAR(2)", "nullable": True},
            {
                "name": "LOYALTY_TIER",
                "type": "VARCHAR(20)",
                "nullable": True,
                "description": "Current loyalty segment used as the backfill source.",
                "semantic_meaning": "loyalty-segment",
            },
            {
                "name": "IS_CURRENT",
                "type": "BOOLEAN",
                "nullable": False,
                "semantic_meaning": "current-row-flag",
            },
            {"name": "VALID_FROM_TS", "type": "TIMESTAMP", "nullable": True},
            {"name": "VALID_TO_TS", "type": "TIMESTAMP", "nullable": True},
        ],
    },
    "CORE.DIM_LOYALTY_TIER": {
        "description": "Reference dimension for loyalty tier labels, rank, and benefits.",
        "primary_key": ["LOYALTY_TIER"],
        "columns": [
            {
                "name": "LOYALTY_TIER",
                "type": "VARCHAR(20)",
                "nullable": False,
                "semantic_meaning": "loyalty-segment",
            },
            {"name": "TIER_RANK", "type": "INTEGER", "nullable": True},
            {"name": "TIER_DESCRIPTION", "type": "VARCHAR(255)", "nullable": True},
            {"name": "ACTIVE_FLAG", "type": "BOOLEAN", "nullable": True},
        ],
    },
    "CORE.FACT_ORDER": {
        "description": "Order fact table used by revenue and customer 360 marts.",
        "primary_key": ["ORDER_ID"],
        "columns": [
            {"name": "ORDER_ID", "type": "VARCHAR(40)", "nullable": False},
            {"name": "CUSTOMER_SK", "type": "BIGINT", "nullable": True},
            {"name": "ORDER_TS", "type": "TIMESTAMP", "nullable": False},
            {
                "name": "NET_AMOUNT",
                "type": "NUMERIC(12,2)",
                "nullable": True,
                "semantic_meaning": "monetary-amount",
            },
        ],
    },
    "CORE.FACT_CUSTOMER_ACTIVITY": {
        "description": "Daily customer activity fact used for retention and loyalty reporting.",
        "primary_key": ["CUSTOMER_SK", "ACTIVITY_DATE"],
        "columns": [
            {"name": "CUSTOMER_SK", "type": "BIGINT", "nullable": False},
            {"name": "ACTIVITY_DATE", "type": "DATE", "nullable": False},
            {
                "name": "LOYALTY_TIER",
                "type": "VARCHAR(20)",
                "nullable": True,
                "semantic_meaning": "loyalty-segment",
            },
            {"name": "ORDER_COUNT", "type": "INTEGER", "nullable": True},
            {"name": "NET_AMOUNT", "type": "NUMERIC(12,2)", "nullable": True},
        ],
    },
    "CRM.CUSTOMER_SEGMENT_EXPORT": {
        "description": "Activation export consumed by marketing journeys and retention campaigns.",
        "primary_key": ["CUSTOMER_ID"],
        "columns": [
            {"name": "CUSTOMER_ID", "type": "VARCHAR(32)", "nullable": False},
            {
                "name": "LOYALTY_TIER",
                "type": "VARCHAR(20)",
                "nullable": True,
                "semantic_meaning": "loyalty-segment",
            },
            {"name": "SEGMENT_CODE", "type": "VARCHAR(40)", "nullable": True},
            {"name": "EXPORT_BATCH_ID", "type": "VARCHAR(40)", "nullable": True},
        ],
    },
}

VIEWS: dict[str, dict[str, str]] = {
    "MARTS.VW_CUSTOMER_360": {
        "description": "Customer 360 view with profile, loyalty tier, and recent activity."
    },
    "MARTS.VW_LOYALTY_REVENUE": {
        "description": "Revenue by loyalty tier for dashboarding and finance checks."
    },
    "MARTS.VW_RETENTION_BY_TIER": {
        "description": "Retention metrics grouped by current loyalty tier."
    },
}

FOREIGN_KEYS = [
    ("ODS", "ODS_ORDER", "CUSTOMER_ID", "ODS", "ODS_CUSTOMER_PROFILE", "CUSTOMER_ID"),
    ("STG", "STG_CUSTOMER_PROFILE", "CUSTOMER_ID", "ODS", "ODS_CUSTOMER_PROFILE", "CUSTOMER_ID"),
    ("STG", "STG_ORDER_ENRICHED", "CUSTOMER_ID", "STG", "STG_CUSTOMER_PROFILE", "CUSTOMER_ID"),
    ("CORE", "DIM_CUSTOMER", "CUSTOMER_ID", "ODS", "ODS_CUSTOMER_PROFILE", "CUSTOMER_ID"),
    ("CORE", "DIM_CUSTOMER", "LOYALTY_TIER", "CORE", "DIM_LOYALTY_TIER", "LOYALTY_TIER"),
    ("CORE", "FACT_ORDER", "CUSTOMER_SK", "CORE", "DIM_CUSTOMER", "CUSTOMER_SK"),
    ("CORE", "FACT_CUSTOMER_ACTIVITY", "CUSTOMER_SK", "CORE", "DIM_CUSTOMER", "CUSTOMER_SK"),
    ("CORE", "FACT_CUSTOMER_ACTIVITY", "LOYALTY_TIER", "CORE", "DIM_LOYALTY_TIER", "LOYALTY_TIER"),
    ("CRM", "CUSTOMER_SEGMENT_EXPORT", "CUSTOMER_ID", "ODS", "ODS_CUSTOMER_PROFILE", "CUSTOMER_ID"),
]

DERIVED_FROM = [
    ("ODS.ODS_CUSTOMER_PROFILE", "CORE.DIM_CUSTOMER"),
    ("STG.STG_CUSTOMER_PROFILE", "ODS.ODS_CUSTOMER_PROFILE"),
    ("STG.STG_ORDER_ENRICHED", "ODS.ODS_ORDER"),
    ("STG.STG_ORDER_ENRICHED", "STG.STG_CUSTOMER_PROFILE"),
    ("CORE.DIM_CUSTOMER", "STG.STG_CUSTOMER_PROFILE"),
    ("CORE.DIM_CUSTOMER", "CORE.DIM_LOYALTY_TIER"),
    ("CORE.FACT_ORDER", "STG.STG_ORDER_ENRICHED"),
    ("CORE.FACT_ORDER", "CORE.DIM_CUSTOMER"),
    ("CORE.FACT_CUSTOMER_ACTIVITY", "CORE.FACT_ORDER"),
    ("CORE.FACT_CUSTOMER_ACTIVITY", "CORE.DIM_CUSTOMER"),
    ("MARTS.VW_CUSTOMER_360", "CORE.DIM_CUSTOMER"),
    ("MARTS.VW_CUSTOMER_360", "CORE.FACT_CUSTOMER_ACTIVITY"),
    ("MARTS.VW_LOYALTY_REVENUE", "CORE.FACT_ORDER"),
    ("MARTS.VW_LOYALTY_REVENUE", "CORE.DIM_LOYALTY_TIER"),
    ("MARTS.VW_RETENTION_BY_TIER", "CORE.FACT_CUSTOMER_ACTIVITY"),
    ("MARTS.VW_RETENTION_BY_TIER", "CORE.DIM_LOYALTY_TIER"),
    ("CRM.CUSTOMER_SEGMENT_EXPORT", "MARTS.VW_CUSTOMER_360"),
    ("CRM.CUSTOMER_SEGMENT_EXPORT", "MARTS.VW_RETENTION_BY_TIER"),
]

JOINS = [
    ("STG.STG_ORDER_ENRICHED", "STG.STG_CUSTOMER_PROFILE"),
    ("CORE.FACT_ORDER", "CORE.DIM_CUSTOMER"),
    ("CORE.FACT_CUSTOMER_ACTIVITY", "CORE.DIM_CUSTOMER"),
    ("CORE.FACT_CUSTOMER_ACTIVITY", "CORE.DIM_LOYALTY_TIER"),
    ("MARTS.VW_CUSTOMER_360", "CORE.DIM_CUSTOMER"),
    ("MARTS.VW_LOYALTY_REVENUE", "CORE.DIM_LOYALTY_TIER"),
    ("MARTS.VW_RETENTION_BY_TIER", "CORE.DIM_LOYALTY_TIER"),
]


def build_seed_graph() -> dict[str, Any]:
    graph = {
        "schemas": deepcopy(SCHEMAS),
        "tables": deepcopy(TABLES),
        "views": deepcopy(VIEWS),
        "foreign_keys": deepcopy(FOREIGN_KEYS),
        "derived_from": deepcopy(DERIVED_FROM),
        "joins": deepcopy(JOINS),
    }
    for table_id, meta in graph["tables"].items():
        primary_keys = set(meta.get("primary_key") or [])
        schema, table = table_id.split(".", 1)
        meta["schema"] = schema
        meta["name"] = table
        for column in meta["columns"]:
            column.setdefault("is_primary_key", column["name"] in primary_keys)
            column.setdefault("description", None)
            column.setdefault("semantic_meaning", None)
    for view_id, meta in graph["views"].items():
        schema, view = view_id.split(".", 1)
        meta["schema"] = schema
        meta["name"] = view
    return graph


def summarize_graph(graph: dict[str, Any]) -> dict[str, int]:
    tables = graph["tables"]
    return {
        "schemas": len(graph["schemas"]),
        "tables": len(tables),
        "views": len(graph["views"]),
        "columns": sum(len(table["columns"]) for table in tables.values()),
        "primary_keys": sum(len(table.get("primary_key") or []) for table in tables.values()),
        "foreign_keys": len(graph["foreign_keys"]),
        "derived_from": len(graph["derived_from"]),
        "joins": len(graph["joins"]),
    }


def missing_semantic_columns(graph: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    missing = []
    for table_id, table in graph["tables"].items():
        for column in table["columns"]:
            if not column.get("semantic_meaning"):
                missing.append((table_id, column))
    return missing
