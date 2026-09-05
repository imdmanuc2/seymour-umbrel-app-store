from __future__ import annotations

from typing import Any


def evaluate_provider_readiness(
    provider: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate only canonical provider install readiness.

    This function is intentionally pure. Host/runtime probes such as
    registry reachability, port availability, Docker, Umbrel, and
    storage validation belong to the target adapter/preflight layer.
    """
    provider_id = str(
        provider.get("providerId") or ""
    ).strip()

    selectable = bool(
        provider.get("selectable")
    )

    production_image = str(
        provider.get("productionImage") or ""
    ).strip()

    runtime = provider.get("runtime")
    runtime_present = isinstance(runtime, dict)

    checks = {
        "providerIdPresent": bool(provider_id),
        "providerSelectable": selectable,
        "productionImagePresent": bool(production_image),
        "runtimePresent": runtime_present,
    }

    errors: list[str] = []

    if not checks["providerIdPresent"]:
        errors.append(
            "Provider ID is missing."
        )

    if not checks["providerSelectable"]:
        errors.append(
            f"{provider_id or 'Provider'} is not selectable."
        )

    if not checks["productionImagePresent"]:
        errors.append(
            f"{provider_id or 'Provider'} has no production image."
        )

    if not checks["runtimePresent"]:
        errors.append(
            f"{provider_id or 'Provider'} has no runtime contract."
        )

    return {
        "compatible": not errors,
        "checks": checks,
        "errors": errors,
    }
