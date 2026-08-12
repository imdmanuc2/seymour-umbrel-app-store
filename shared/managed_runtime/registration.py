from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import (
    ManagedRuntimeCapabilities,
    ManagedRuntimeIdentity,
    ManagedRuntimeObservation,
)

REGISTRATION_CONTRACT = "seymour.managed-runtime-registration"
REGISTRATION_VERSION = "1.0"


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _bool(value: Any, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


def _provider_id(asset: dict[str, Any], telemetry: dict[str, Any]) -> str | None:
    for source in (asset, telemetry):
        for key in ("providerId", "provider_id"):
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _runtime_id(asset: dict[str, Any], provider_id: str | None) -> str:
    for key in ("runtimeId", "appId", "assetId", "id"):
        value = asset.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return provider_id or "unknown-runtime"


def _state(asset: dict[str, Any], telemetry: dict[str, Any]) -> dict[str, Any]:
    operational = _dict(
        asset.get("operationalState")
        or telemetry.get("operationalState")
    )
    state_name = (
        asset.get("runtimeState")
        or telemetry.get("runtimeState")
        or operational.get("state")
        or telemetry.get("lifecycleStatus")
        or "unknown"
    )
    installed = telemetry.get("installed")
    running = telemetry.get("running")
    rpc_reachable = (
        telemetry.get("runtimeRpcReachable")
        if "runtimeRpcReachable" in telemetry
        else operational.get("rpcReachable")
    )
    rpc_healthy = (
        telemetry.get("runtimeRpcHealthy")
        if "runtimeRpcHealthy" in telemetry
        else operational.get("rpcHealthy")
    )
    ibd = (
        telemetry.get("runtimeInitialBlockDownload")
        if "runtimeInitialBlockDownload" in telemetry
        else operational.get("initialBlockDownload")
    )
    progress = (
        telemetry.get("runtimeVerificationProgress")
        if "runtimeVerificationProgress" in telemetry
        else operational.get("verificationProgress")
    )
    reason = telemetry.get("runtimeStateReason") or operational.get("reason") or ""

    return {
        "state": str(state_name).strip().lower(),
        "reason": str(reason),
        "installed": _bool(installed, True),
        "running": _bool(running, str(state_name).lower() in {
            "starting", "syncing", "running", "degraded"
        }),
        "containerHealth": _dict(telemetry.get("container")).get("health", "unknown"),
        "rpcReachable": _bool(rpc_reachable),
        "rpcHealthy": _bool(rpc_healthy),
        "rpcStatus": operational.get("rpcStatus"),
        "initialBlockDownload": ibd if isinstance(ibd, bool) else None,
        "verificationProgress": (
            float(progress) if isinstance(progress, (int, float)) else None
        ),
    }


def _capabilities(asset: dict[str, Any], telemetry: dict[str, Any]) -> ManagedRuntimeCapabilities:
    supplied = _dict(asset.get("capabilities") or telemetry.get("capabilities"))
    # Registration is observational. Lifecycle booleans describe advertised
    # capabilities only; this projector never executes them.
    return ManagedRuntimeCapabilities(
        inspect=True,
        telemetry=True,
        logs=_bool(supplied.get("logs"), True),
        install=_bool(supplied.get("install")),
        start=_bool(supplied.get("start")),
        stop=_bool(supplied.get("stop")),
        restart=_bool(supplied.get("restart")),
        update=_bool(supplied.get("update")),
        uninstall=_bool(supplied.get("uninstall")),
    )


def project_asset(asset: dict[str, Any]) -> dict[str, Any]:
    source = deepcopy(asset)
    telemetry = _dict(source.get("telemetry"))
    provider_id = _provider_id(source, telemetry)
    runtime_id = _runtime_id(source, provider_id)

    identity = ManagedRuntimeIdentity(
        runtime_id=runtime_id,
        runtime_type=str(
            source.get("runtimeType")
            or telemetry.get("runtimeType")
            or "umbrel"
        ),
        provider_id=provider_id,
        display_name=(
            source.get("displayName")
            or source.get("name")
            or telemetry.get("displayName")
        ),
        version=(
            str(source.get("version"))
            if source.get("version") is not None
            else None
        ),
    )

    canonical_telemetry = {
        key: deepcopy(value)
        for key, value in telemetry.items()
        if key not in {
            "operationalState",
            "runtimeState",
            "runtimeStateReason",
            "runtimeRpcReachable",
            "runtimeRpcHealthy",
            "runtimeInitialBlockDownload",
            "runtimeVerificationProgress",
            "installed",
            "running",
            "container",
            "lifecycleStatus",
        }
    }

    observation = ManagedRuntimeObservation(
        identity=identity,
        state=_state(source, telemetry),
        capabilities=_capabilities(source, telemetry),
        telemetry=canonical_telemetry,
        native={
            "registrationAsset": source,
        },
    )
    return observation.to_dict()


def project_registration_payload(payload: dict[str, Any]) -> dict[str, Any]:
    assets = payload.get("assets")
    if not isinstance(assets, list):
        assets = []

    managed = []
    for item in assets:
        if not isinstance(item, dict):
            continue
        telemetry = _dict(item.get("telemetry"))
        has_runtime_signal = any(
            key in item or key in telemetry
            for key in (
                "runtimeState",
                "operationalState",
                "lifecycleStatus",
                "installed",
                "running",
                "providerId",
            )
        )
        if has_runtime_signal:
            managed.append(project_asset(item))

    return {
        "contract": REGISTRATION_CONTRACT,
        "version": REGISTRATION_VERSION,
        "managedRuntimes": managed,
    }


def attach_managed_runtime_projection(payload: dict[str, Any]) -> dict[str, Any]:
    projection = project_registration_payload(payload)
    result = deepcopy(payload)
    result["managedRuntimeContract"] = (
        f"{projection['contract']}/{projection['version']}"
    )
    result["managedRuntimes"] = projection["managedRuntimes"]
    return result
