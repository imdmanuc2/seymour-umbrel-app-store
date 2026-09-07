from __future__ import annotations

import secrets
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .request import InstallRequest
from .validation import (
    provider_from_catalog,
    rpc_authentication,
    rpc_contract,
    p2p_contract,
    runtime_contract,
    runtime_port,
    validate_install_request,
)


CredentialGenerator = Callable[[], tuple[str, str]]


def generate_rpc_credentials() -> tuple[str, str]:
    """
    Generate Seymour RPC credentials on the execution target.

    Secrets produced here must remain inside the target-side execution
    boundary and must never be transported through Nexus capability
    parameters or command argv.
    """
    return (
        "seymour_rpc",
        secrets.token_urlsafe(32),
    )


def _default_node_name(
    provider: dict[str, Any],
) -> str:
    display_name = str(
        provider.get("displayName") or ""
    ).strip()

    if not display_name:
        raise ValueError(
            "Provider display name is missing."
        )

    return f"Seymour {display_name} Node"


def materialize_install_request(
    *,
    provider_id: str,
    storage_target_id: str,
    catalog_path: Path,
    node_name: str | None = None,
    credential_generator: CredentialGenerator = generate_rpc_credentials,
) -> InstallRequest:
    """
    Expand the minimal target install contract into the validated shared
    InstallRequest used by the installation orchestrator.

    providerId and storageTargetId are the only values required from a
    remote management caller such as Nexus. Canonical application
    identity, ports, confirmation and authentication policy are resolved
    from the provider catalog on the execution target.

    A management UI may optionally supply a descriptive node name.
    """
    provider = provider_from_catalog(
        Path(catalog_path),
        str(provider_id).strip(),
    )

    runtime = runtime_contract(provider)

    app_id = str(
        runtime.get("appId") or ""
    ).strip()

    if not app_id:
        raise ValueError(
            "Provider application ID is missing."
        )

    resolved_node_name = str(
        node_name or ""
    ).strip()

    if not resolved_node_name:
        resolved_node_name = _default_node_name(
            provider
        )

    authentication = rpc_authentication(
        provider
    )

    if authentication == "username-password":
        rpc_user, rpc_password = (
            credential_generator()
        )

        rpc_user = str(rpc_user).strip()
        rpc_password = str(rpc_password)

    elif authentication == "none":
        rpc_user = ""
        rpc_password = ""

    else:
        # rpc_authentication() currently fails closed before this branch.
        raise ValueError(
            "Unsupported RPC authentication contract."
        )

    request = InstallRequest(
        provider_id=str(
            provider.get("providerId") or ""
        ).strip(),
        app_id=app_id,
        node_name=resolved_node_name,
        rpc_user=rpc_user,
        rpc_password=rpc_password,
        rpc_port=runtime_port(
            rpc_contract(provider),
            "RPC",
        ),
        p2p_port=runtime_port(
            p2p_contract(provider),
            "P2P",
        ),
        storage_target_id=str(
            storage_target_id
        ).strip(),
        confirmation=f"INSTALL-{app_id}",
    )

    validate_install_request(
        request,
        Path(catalog_path),
    )

    return request
