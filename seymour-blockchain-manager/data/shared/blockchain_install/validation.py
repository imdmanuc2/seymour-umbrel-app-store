from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .request import InstallRequest


def provider_from_catalog(
    catalog_path: Path,
    provider_id: str,
) -> dict[str, Any]:
    """
    Load exactly one provider record from the canonical catalog.

    This deliberately does not instantiate the legacy ProviderCatalog
    model because installation validation only needs the selected
    provider's runtime contract.
    """
    catalog = json.loads(
        catalog_path.read_text()
    )

    providers = catalog.get("providers")

    if not isinstance(providers, list):
        raise ValueError(
            "Provider catalog is missing providers."
        )

    for provider in providers:
        if (
            isinstance(provider, dict)
            and provider.get("providerId") == provider_id
        ):
            return provider

    raise ValueError(
        f"Unknown blockchain provider: {provider_id}"
    )


def runtime_contract(
    provider: dict[str, Any],
) -> dict[str, Any]:
    runtime = provider.get("runtime")

    if not isinstance(runtime, dict):
        raise ValueError(
            "Provider runtime contract is missing."
        )

    return runtime


def rpc_contract(
    provider: dict[str, Any],
) -> dict[str, Any]:
    rpc = runtime_contract(provider).get("rpc")

    if not isinstance(rpc, dict):
        raise ValueError(
            "Provider RPC contract is missing."
        )

    return rpc


def p2p_contract(
    provider: dict[str, Any],
) -> dict[str, Any]:
    p2p = runtime_contract(provider).get("p2p")

    if not isinstance(p2p, dict):
        raise ValueError(
            "Provider P2P contract is missing."
        )

    return p2p


def runtime_port(
    contract: dict[str, Any],
    name: str,
) -> int:
    value = int(contract.get("port", 0))

    if not 1 <= value <= 65535:
        raise ValueError(
            f"Provider {name} port is invalid."
        )

    return value


def rpc_authentication(
    provider: dict[str, Any],
) -> str:
    value = str(
        rpc_contract(provider).get("authentication")
        or ""
    ).strip()

    if value not in {
        "none",
        "username-password",
    }:
        raise ValueError(
            "Provider RPC authentication contract "
            "is unsupported."
        )

    return value


def validate_install_request(
    value: InstallRequest,
    catalog_path: Path,
) -> None:
    """
    Validate a provider-neutral installation request against the
    canonical selected-provider runtime contract.

    Adapter availability and host lifecycle execution are intentionally
    outside this validation boundary.
    """
    provider = provider_from_catalog(
        catalog_path,
        value.provider_id,
    )

    runtime = runtime_contract(provider)

    expected_app_id = str(
        runtime.get("appId") or ""
    ).strip()

    if not expected_app_id:
        raise ValueError(
            "Provider application ID is missing."
        )

    expected_confirmation = (
        f"INSTALL-{expected_app_id}"
    )

    if value.app_id != expected_app_id:
        raise ValueError(
            "App ID does not match the selected provider."
        )

    if value.confirmation != expected_confirmation:
        raise ValueError(
            "Installation confirmation token did not match."
        )

    if not value.node_name:
        raise ValueError(
            "Node name is required."
        )

    if not value.storage_target_id:
        raise ValueError(
            "Storage target is required."
        )

    authentication = rpc_authentication(provider)

    if authentication == "username-password":
        if not value.rpc_user:
            raise ValueError(
                "RPC user is required."
            )

        if len(value.rpc_password) < 24:
            raise ValueError(
                "RPC password must contain at least "
                "24 characters."
            )

    expected_rpc_port = runtime_port(
        rpc_contract(provider),
        "RPC",
    )

    expected_p2p_port = runtime_port(
        p2p_contract(provider),
        "P2P",
    )

    if value.rpc_port != expected_rpc_port:
        raise ValueError(
            "RPC port does not match provider contract: "
            f"expected {expected_rpc_port}."
        )

    if value.p2p_port != expected_p2p_port:
        raise ValueError(
            "P2P port does not match provider contract: "
            f"expected {expected_p2p_port}."
        )
