from __future__ import annotations

from hmac import compare_digest
from http import HTTPStatus
import os
from pathlib import Path
from typing import Any, Mapping

from shared.blockchain_install.request_materializer import (
    materialize_install_request,
)


CONTROL_TOKEN_ENV = "NEXUS_CONTROL_TOKEN"

CATALOG_PATH = Path(
    os.environ.get(
        "PROVIDER_CATALOG_PATH",
        "/catalog/providers.v1.json",
    )
)

_ALLOWED_INSTALL_FIELDS = frozenset({
    "providerId",
    "storageTargetId",
})


def _error(
    error: str,
    message: str,
) -> dict[str, Any]:
    return {
        "contract": "seymour.nexus-control-error",
        "version": 1,
        "error": error,
        "message": message,
    }


def authorize(
    headers: Mapping[str, Any],
) -> tuple[bool, dict[str, Any] | None, int]:
    """
    Authenticate a remote Nexus control-plane request.

    A dedicated target-side secret is required. This secret is separate
    from RPC credentials, Umbrel credentials, Nexus registration
    delivery credentials, peer identity, and capability parameters.
    """

    expected = os.environ.get(
        CONTROL_TOKEN_ENV,
        "",
    ).strip()

    if not expected:
        return (
            False,
            _error(
                "nexus-control-not-configured",
                "Nexus control authentication is not configured.",
            ),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    authorization = str(
        headers.get("Authorization") or ""
    ).strip()

    prefix = "Bearer "

    if not authorization.startswith(prefix):
        return (
            False,
            _error(
                "nexus-control-authentication-required",
                "Bearer authentication is required.",
            ),
            HTTPStatus.UNAUTHORIZED,
        )

    supplied = authorization[len(prefix):].strip()

    if not supplied or not compare_digest(
        supplied,
        expected,
    ):
        return (
            False,
            _error(
                "nexus-control-authentication-failed",
                "Nexus control authentication failed.",
            ),
            HTTPStatus.FORBIDDEN,
        )

    return True, None, HTTPStatus.OK


def materialize_remote_install_request(
    payload: Mapping[str, Any],
):
    """
    Convert the minimal Nexus request into the full target-local
    installation request.

    Nexus may select only canonical provider and storage identities.
    Secrets, app identity, ports, node name, and confirmation tokens are
    generated or resolved by the target-side Seymour runtime.
    """

    if not isinstance(payload, Mapping):
        raise ValueError(
            "Nexus install request must be an object."
        )

    unknown = set(payload) - _ALLOWED_INSTALL_FIELDS

    if unknown:
        raise ValueError(
            "Unsupported Nexus install parameters: "
            + ", ".join(sorted(str(item) for item in unknown))
        )

    provider_id = str(
        payload.get("providerId") or ""
    ).strip()

    storage_target_id = str(
        payload.get("storageTargetId") or ""
    ).strip()

    if not provider_id:
        raise ValueError(
            "providerId is required."
        )

    if not storage_target_id:
        raise ValueError(
            "storageTargetId is required."
        )

    return materialize_install_request(
        provider_id=provider_id,
        storage_target_id=storage_target_id,
        catalog_path=CATALOG_PATH,
    )


def execute_install(
    payload: Mapping[str, Any],
    installer: Any,
) -> tuple[dict[str, Any], int]:
    """
    Execute one provider-neutral blockchain install using the existing
    Blockchain Manager execution owner.
    """

    request = materialize_remote_install_request(
        payload
    )

    execute = getattr(
        installer,
        "execute_shared",
        None,
    )

    if not callable(execute):
        raise TypeError(
            "Blockchain Manager installer does not expose execute_shared."
        )

    result = execute(request)

    to_dict = getattr(
        result,
        "to_dict",
        None,
    )

    if not callable(to_dict):
        raise TypeError(
            "Blockchain installation result is invalid."
        )

    response = to_dict()

    if not isinstance(response, dict):
        raise TypeError(
            "Blockchain installation result payload is invalid."
        )

    status = str(
        response.get("status") or ""
    ).strip()

    if status == "succeeded":
        return response, HTTPStatus.OK

    return response, HTTPStatus.BAD_REQUEST
