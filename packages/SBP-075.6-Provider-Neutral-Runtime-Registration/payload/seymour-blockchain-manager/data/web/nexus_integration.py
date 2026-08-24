from __future__ import annotations

from bch_runtime_probe import probe as probe_bch_runtime

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
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


HOST_MACHINE_ID_PATH = Path(
    os.environ.get(
        "SEYMOUR_HOST_MACHINE_ID_PATH",
        "/host-identity/machine-id",
    )
)


def host_identity() -> str:
    """
    Return a stable identity for the Umbrel host.

    Container hostname MUST NOT participate in canonical asset identity.
    """

    try:
        value = HOST_MACHINE_ID_PATH.read_text().strip()
    except Exception:
        value = ""

    if value:
        return f"machine-id:{value}"

    raise RuntimeError(
        "Stable Umbrel host identity is unavailable."
    )


def manager_identity() -> dict[str, Any]:
    hostname = socket.gethostname()
    host_id = host_identity()
    return {
        "assetId": stable_id("asset", f"{host_id}:{MANAGER_APP_ID}"),
        "assetType": "blockchain-manager",
        "name": "Seymour Blockchain Manager",
        "hostname": hostname,
        "appId": MANAGER_APP_ID,
        "managedBy": "nexus",
        "source": "seymour-umbrel",
    }


def node_identity() -> dict[str, Any]:
    hostname = socket.gethostname()
    host_id = host_identity()
    return {
        "assetId": stable_id("asset", f"{host_id}:{BCH_APP_ID}"),
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


# SBP-020 runtime normalization
_sbp020_registration_payload = registration_payload

def registration_payload(dashboard, sync):
    payload = _sbp020_registration_payload(dashboard, sync)
    runtime = probe_bch_runtime()
    document = payload.get("document") if isinstance(payload, dict) else None
    assets = document.get("assets") if isinstance(document, dict) else None
    if not isinstance(assets, list):
        return payload
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("providerId") != "bitcoin-cash-mainnet":
            continue
        telemetry = asset.get("telemetry")
        if not isinstance(telemetry, dict):
            telemetry = {}
            asset["telemetry"] = telemetry
        telemetry["installed"] = bool(runtime.get("installed"))
        telemetry["running"] = bool(runtime.get("running"))
        telemetry["container"] = runtime.get("container") or {}
        telemetry["lifecycleStatus"] = runtime.get("lifecycleStatus", "unknown")
        telemetry["operationalState"] = runtime.get("operationalState")

        operational_state = (
            runtime.get("operationalState")
            if isinstance(runtime.get("operationalState"), dict)
            else {}
        )

        telemetry["operationalStateName"] = operational_state.get("state")
        telemetry["runtimeState"] = operational_state.get("state")
        telemetry["runtimeStateReason"] = operational_state.get("reason")
        telemetry["runtimeRpcReachable"] = operational_state.get("rpcReachable")
        telemetry["runtimeRpcHealthy"] = operational_state.get("rpcHealthy")
        telemetry["runtimeInitialBlockDownload"] = operational_state.get("initialBlockDownload")
        telemetry["runtimeVerificationProgress"] = operational_state.get("verificationProgress")

        telemetry["rpc"] = runtime.get("rpc") or {}
        asset["operationalState"] = runtime.get("operationalState")
        asset["runtimeState"] = operational_state.get("state")
        asset["status"] = runtime.get("lifecycleStatus", "unknown")
    return payload

# SBP-075.6 — provider-neutral managed runtime registration

from shared.blockchain_install.runtime_binding import (
    load_runtime_binding,
)
from shared.managed_runtime import attach_managed_runtime_projection


RUNTIME_BINDING_DIRECTORY = Path(
    os.environ.get(
        "RUNTIME_BINDING_CONFIG_DIRECTORY",
        "/evidence/runtime-bindings",
    )
)

UMBREL_CONTROL_SCRIPT = Path(
    os.environ.get(
        "SEYMOUR_UMBREL_CONTROL_SCRIPT",
        "/control/seymour-umbrel-app",
    )
)

_PROVIDER_COMPATIBILITY = {
    "seymour-bch-node": {
        "providerId": "bitcoin-cash-mainnet",
        "coin": "BCH",
        "displayName": "Seymour Bitcoin Cash Node",
    },
    "seymour-bitcoin-node": {
        "providerId": "bitcoin-mainnet",
        "coin": "BTC",
        "displayName": "Seymour Bitcoin Node",
    },
    "seymour-monero-node": {
        "providerId": "monero-mainnet",
        "coin": "XMR",
        "displayName": "Seymour Monero Node",
    },
}


def _catalog_provider_map() -> dict[str, dict[str, Any]]:
    return {
        item["providerId"]: item
        for item in load_catalog().get("providers", [])
        if isinstance(item, dict)
        and isinstance(item.get("providerId"), str)
    }


def _binding_identity(
    path: Path,
) -> dict[str, Any] | None:
    """
    Resolve canonical provider/app identity from a runtime binding.

    Older BCH bindings predate provider/app identity persistence, so the
    filename is retained as a narrow compatibility bridge.
    """

    try:
        binding = load_runtime_binding(path)

        return {
            "providerId": binding.provider_id,
            "appId": binding.app_id,
            "binding": binding,
        }

    except Exception:
        compatibility = _PROVIDER_COMPATIBILITY.get(path.stem)

        if compatibility is None:
            return None

        return {
            "providerId": compatibility["providerId"],
            "appId": path.stem,
            "binding": None,
        }


def _native_runtime_state(
    app_id: str,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [
                str(UMBREL_CONTROL_SCRIPT),
                "state",
                app_id,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if completed.returncode != 0:
            raise RuntimeError(
                completed.stderr.strip()
                or completed.stdout.strip()
                or (
                    "native lifecycle state command "
                    f"failed with exit code "
                    f"{completed.returncode}"
                )
            )

        operation = json.loads(
            completed.stdout
        )

        if not isinstance(operation, dict):
            raise RuntimeError(
                "native lifecycle state returned "
                "an invalid operation payload"
            )

        if operation.get("success") is not True:
            raise RuntimeError(
                str(
                    operation.get("error")
                    or "native lifecycle state failed"
                )
            )

        state = operation.get("result")

        if not isinstance(state, dict):
            raise RuntimeError(
                "native lifecycle state returned "
                "an invalid result payload"
            )

    except Exception as exc:
        return {
            "installed": True,
            "running": False,
            "lifecycleStatus": "unknown",
            "nativeState": {},
            "nativeStateError": str(exc),
        }

    raw_state = str(
        state.get("state")
        or state.get("status")
        or "unknown"
    ).strip().lower()

    progress = state.get("progress")

    running_states = {
        "ready",
        "running",
        "starting",
        "syncing",
    }

    installed = raw_state not in {
        "not-installed",
        "uninstalled",
        "missing",
    }

    running = raw_state in running_states

    lifecycle = {
        "ready": "running",
        "running": "running",
        "starting": "starting",
        "syncing": "syncing",
        "stopped": "stopped",
        "stop": "stopped",
        "not-installed": "not-installed",
        "uninstalled": "not-installed",
        "missing": "not-installed",
    }.get(
        raw_state,
        raw_state or "unknown",
    )

    return {
        "installed": installed,
        "running": running,
        "lifecycleStatus": lifecycle,
        "nativeState": state,
        "nativeProgress": progress,
    }


def _generic_runtime_asset(
    *,
    manager: dict[str, Any],
    provider_id: str,
    app_id: str,
    native: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    provider = catalog.get(provider_id, {})
    compatibility = _PROVIDER_COMPATIBILITY.get(app_id, {})

    ticker = (
        provider.get("ticker")
        or compatibility.get("coin")
    )

    display_name = (
        compatibility.get("displayName")
        or (
            f"Seymour {provider.get('displayName')} Node"
            if provider.get("displayName")
            else app_id
        )
    )

    lifecycle = native.get(
        "lifecycleStatus",
        "unknown",
    )

    telemetry = {
        "providerId": provider_id,
        "appId": app_id,
        "installed": bool(native.get("installed")),
        "running": bool(native.get("running")),
        "lifecycleStatus": lifecycle,
        "runtimeState": lifecycle,
        "nativeState": native.get("nativeState", {}),
    }

    if native.get("nativeStateError"):
        telemetry["nativeStateError"] = native[
            "nativeStateError"
        ]

    if native.get("nativeProgress") is not None:
        telemetry["nativeProgress"] = native[
            "nativeProgress"
        ]

    return {
        "assetId": stable_id(
            "asset",
            f"{host_identity()}:{app_id}",
        ),
        "assetType": "blockchain-node",
        "name": display_name,
        "hostname": socket.gethostname(),
        "appId": app_id,
        "providerId": provider_id,
        "coin": ticker,
        "network": provider.get("network", "mainnet"),
        "managedBy": "nexus",
        "source": "seymour-umbrel",
        "status": lifecycle,
        "runtimeState": lifecycle,
        "telemetry": telemetry,
    }


def _managed_runtime_assets(
    dashboard: dict[str, Any],
) -> list[dict[str, Any]]:
    catalog = _catalog_provider_map()

    assets: list[dict[str, Any]] = []

    if not RUNTIME_BINDING_DIRECTORY.is_dir():
        return assets

    for path in sorted(
        RUNTIME_BINDING_DIRECTORY.glob("*.env")
    ):
        identity = _binding_identity(path)

        if not identity:
            continue

        provider_id = identity["providerId"]
        app_id = identity["appId"]

        if not provider_id or not app_id:
            continue

        native = _native_runtime_state(
            app_id
        )

        asset = _generic_runtime_asset(
            manager=manager_identity(),
            provider_id=provider_id,
            app_id=app_id,
            native=native,
            catalog=catalog,
        )

        # BCH already has richer canonical telemetry. Preserve it while
        # retaining Umbrel native lifecycle state as the registration
        # existence/lifecycle authority.
        if provider_id == BCH_PROVIDER_ID:
            existing = (
                dashboard
                .get("providers", {})
                .get(BCH_PROVIDER_ID)
            )

            if isinstance(existing, dict):
                telemetry = dict(existing)
                telemetry["providerId"] = provider_id
                telemetry["appId"] = app_id
                telemetry["installed"] = bool(
                    native.get("installed")
                )
                telemetry["running"] = bool(
                    native.get("running")
                )
                telemetry["lifecycleStatus"] = (
                    native.get(
                        "lifecycleStatus",
                        "unknown",
                    )
                )
                telemetry["nativeState"] = native.get(
                    "nativeState",
                    {},
                )

                asset["telemetry"] = telemetry
                asset["status"] = telemetry[
                    "lifecycleStatus"
                ]
                asset["runtimeState"] = (
                    telemetry.get("runtimeState")
                    or telemetry["lifecycleStatus"]
                )

                operational = telemetry.get(
                    "operationalState"
                )

                if isinstance(operational, dict):
                    asset["operationalState"] = operational

        assets.append(asset)

    return assets


_sbp0756_base_registration_payload = registration_payload


def registration_payload(
    dashboard: dict[str, Any],
    sync: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the legacy-compatible registration envelope, replace the
    BCH-only node projection with canonical managed runtime bindings,
    and attach the provider-neutral managed-runtime projection.
    """

    payload = _sbp0756_base_registration_payload(
        dashboard,
        sync,
    )

    document = (
        payload.get("document")
        if isinstance(payload, dict)
        else None
    )

    if not isinstance(document, dict):
        return attach_managed_runtime_projection(payload)

    manager = document.get("manager")

    if not isinstance(manager, dict):
        return attach_managed_runtime_projection(payload)

    runtime_assets = _managed_runtime_assets(
        dashboard
    )

    document["assets"] = [
        manager,
        *runtime_assets,
    ]

    document["relationships"] = [
        {
            "relationshipType": "manages",
            "sourceAssetId": manager["assetId"],
            "targetAssetId": asset["assetId"],
        }
        for asset in runtime_assets
    ]

    # The managed-runtime projector consumes top-level assets. Preserve
    # the existing document envelope while explicitly supplying the
    # canonical runtime asset set to the generic projector.
    projection_input = dict(payload)
    projection_input["assets"] = runtime_assets

    projection = attach_managed_runtime_projection(
        projection_input
    )

    payload["managedRuntimeContract"] = projection[
        "managedRuntimeContract"
    ]
    payload["managedRuntimes"] = projection[
        "managedRuntimes"
    ]

    return payload
