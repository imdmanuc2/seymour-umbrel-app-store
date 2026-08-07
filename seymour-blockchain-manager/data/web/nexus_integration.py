from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import socket
from typing import Any

CATALOG_PATH = Path(os.environ.get(
    "PROVIDER_CATALOG_PATH",
    "/catalog/providers.v1.json",
))
EVIDENCE_PATH = Path(os.environ.get(
    "NEXUS_REGISTRATION_EVIDENCE_PATH",
    "/evidence/nexus-registration.jsonl",
))
MANAGER_APP_ID = "seymour-blockchain-manager"
BCH_APP_ID = os.environ.get("BCH_APP_ID", "seymour-bch-node")
BCH_PROVIDER_ID = "bitcoin-cash-mainnet"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def stable_id(namespace: str, value: str) -> str:
    digest = hashlib.sha256(
        f"{namespace}:{value}".encode()
    ).hexdigest()[:16]
    return f"{namespace}-{digest}"


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text())


def manager_identity() -> dict[str, Any]:
    hostname = socket.gethostname()
    return {
        "assetId": stable_id("asset", f"{hostname}:{MANAGER_APP_ID}"),
        "assetType": "blockchain-manager",
        "name": "Seymour Blockchain Manager",
        "hostname": hostname,
        "appId": MANAGER_APP_ID,
        "managedBy": "nexus",
        "source": "seymour-umbrel",
    }


def node_identity() -> dict[str, Any]:
    hostname = socket.gethostname()
    return {
        "assetId": stable_id("asset", f"{hostname}:{BCH_APP_ID}"),
        "assetType": "blockchain-node",
        "name": "Seymour Bitcoin Cash Node",
        "hostname": hostname,
        "appId": BCH_APP_ID,
        "providerId": BCH_PROVIDER_ID,
        "coin": "BCH",
        "network": "mainnet",
        "managedBy": "nexus",
        "source": "seymour-umbrel",
    }


def capabilities() -> list[str]:
    return [
        "catalog.read",
        "telemetry.read",
        "health.read",
        "sync.read",
        "logs.read",
        "diagnostics.run",
        "lifecycle.start",
        "lifecycle.stop",
        "lifecycle.restart",
        "backup.plan",
        "backup.execute",
        "restore.plan",
        "upgrade.plan",
        "adoption.plan",
        "adoption.execute",
    ]


def operations() -> list[dict[str, Any]]:
    return [
        {"operation": "state", "method": "POST", "path": "/api/lifecycle/state", "confirmationRequired": False},
        {"operation": "start", "method": "POST", "path": "/api/lifecycle/start", "confirmationRequired": True},
        {"operation": "stop", "method": "POST", "path": "/api/lifecycle/stop", "confirmationRequired": True},
        {"operation": "restart", "method": "POST", "path": "/api/lifecycle/restart", "confirmationRequired": True},
        {"operation": "diagnostics", "method": "GET", "path": "/api/operations/diagnostics", "confirmationRequired": False},
        {"operation": "backup", "method": "POST", "path": "/api/operations/backup", "confirmationRequired": True},
    ]


def providers() -> list[dict[str, Any]]:
    return [
        {
            "providerId": p["providerId"],
            "displayName": p["displayName"],
            "ticker": p["ticker"],
            "family": p["family"],
            "availability": p["availability"],
            "selectable": p["selectable"],
        }
        for p in load_catalog()["providers"]
    ]


def discovery_document(
    dashboard: dict[str, Any],
    sync: dict[str, Any],
) -> dict[str, Any]:
    manager = manager_identity()
    node = node_identity()
    telemetry = dashboard.get("providers", {}).get(
        BCH_PROVIDER_ID,
        {},
    )
    return {
        "schemaVersion": 1,
        "generatedAt": utc_now(),
        "platform": "seymour",
        "managementPlane": "nexus",
        "manager": manager,
        "assets": [
            manager,
            {
                **node,
                "status": telemetry.get("lifecycleStatus", "unknown"),
                "telemetry": telemetry,
                "sync": sync,
            },
        ],
        "providers": providers(),
        "capabilities": capabilities(),
        "operations": operations(),
        "relationships": [
            {
                "relationshipType": "manages",
                "sourceAssetId": manager["assetId"],
                "targetAssetId": node["assetId"],
            }
        ],
    }


def registration_payload(
    dashboard: dict[str, Any],
    sync: dict[str, Any],
) -> dict[str, Any]:
    document = discovery_document(dashboard, sync)
    return {
        "registrationId": stable_id(
            "registration",
            document["manager"]["assetId"],
        ),
        "createdAt": utc_now(),
        "source": "seymour-blockchain-manager",
        "document": document,
    }


def append_registration_evidence(
    payload: dict[str, Any],
) -> None:
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
