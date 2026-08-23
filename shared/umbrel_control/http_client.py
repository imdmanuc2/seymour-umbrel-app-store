from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def _b64url(value: bytes) -> str:
    return (
        base64.urlsafe_b64encode(value)
        .rstrip(b"=")
        .decode("ascii")
    )


def discover_default_gateway() -> str:
    route = Path("/proc/net/route")

    if not route.is_file():
        raise RuntimeError(
            "Linux route table is unavailable."
        )

    for line in route.read_text().splitlines()[1:]:
        fields = line.split()

        if (
            len(fields) < 3
            or fields[1] != "00000000"
        ):
            continue

        raw = int(
            fields[2],
            16,
        )

        return ".".join(
            str(
                (raw >> shift)
                & 0xFF
            )
            for shift in (
                0,
                8,
                16,
                24,
            )
        )

    raise RuntimeError(
        "Unable to discover Docker host gateway."
    )


def resolve_data_directory(
    configured: Path,
) -> Path:
    candidates = [
        configured,
    ]

    env_path = os.environ.get(
        "SEYMOUR_UMBREL_DATA_DIR",
        "",
    ).strip()

    if env_path:
        candidates.append(
            Path(env_path)
        )

    candidates.append(
        Path("/host-umbrel")
    )

    checked: list[str] = []

    for candidate in candidates:
        value = str(candidate)

        if value in checked:
            continue

        checked.append(value)

        if (
            candidate
            / "secrets"
            / "jwt"
        ).is_file():
            return candidate

    raise RuntimeError(
        "Unable to locate Umbrel JWT. "
        "Checked: "
        + ", ".join(checked)
    )


def sign_umbrel_jwt(
    secret: str,
    *,
    lifetime_seconds: int = 300,
) -> str:
    secret = secret.strip()

    if (
        len(secret) != 64
        or any(
            char
            not in
            "0123456789abcdefABCDEF"
            for char in secret
        )
    ):
        raise RuntimeError(
            "Invalid Umbrel JWT secret."
        )

    now = int(time.time())

    header = {
        "alg": "HS256",
        "typ": "JWT",
    }

    payload = {
        "loggedIn": True,
        "iat": now,
        "exp": (
            now
            + max(
                60,
                int(lifetime_seconds),
            )
        ),
    }

    encoded_header = _b64url(
        json.dumps(
            header,
            separators=(",", ":"),
        ).encode()
    )

    encoded_payload = _b64url(
        json.dumps(
            payload,
            separators=(",", ":"),
        ).encode()
    )

    signing_input = (
        f"{encoded_header}."
        f"{encoded_payload}"
    ).encode()

    signature = hmac.new(
        secret.encode(),
        signing_input,
        hashlib.sha256,
    ).digest()

    return (
        signing_input.decode()
        + "."
        + _b64url(signature)
    )


class UmbrelHttpClient:
    def __init__(
        self,
        *,
        data_directory: Path,
        endpoint: str | None = None,
        timeout_seconds: float = 30,
        mutation_timeout_seconds: float = 1800,
    ) -> None:
        self.data_directory = (
            resolve_data_directory(
                data_directory
            )
        )

        self.timeout_seconds = (
            float(timeout_seconds)
        )
        self.mutation_timeout_seconds = (
            float(mutation_timeout_seconds)
        )

        endpoint_value = str(
            endpoint or ""
        ).strip()

        if (
            endpoint_value.startswith(
                "http://"
            )
            or endpoint_value.startswith(
                "https://"
            )
        ):
            self.endpoint = (
                endpoint_value.rstrip("/")
            )
        else:
            gateway = (
                discover_default_gateway()
            )

            self.endpoint = (
                f"http://{gateway}/trpc"
            )

    def token(self) -> str:
        secret = (
            self.data_directory
            / "secrets"
            / "jwt"
        ).read_text().strip()

        return sign_umbrel_jwt(
            secret
        )

    def state(
        self,
        app_id: str,
    ) -> dict[str, Any]:
        payload = {
            "appId": app_id,
        }

        encoded = quote(
            json.dumps(
                payload,
                separators=(",", ":"),
            ),
            safe="",
        )

        url = (
            f"{self.endpoint}"
            f"/apps.state"
            f"?input={encoded}"
        )

        request = Request(
            url,
            method="GET",
            headers={
                "Authorization":
                    f"Bearer {self.token()}",
                "Accept":
                    "application/json",
                "User-Agent":
                    "Seymour-Blockchain-Manager/1.0",
            },
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                body = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

        except HTTPError as exc:
            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            raise RuntimeError(
                "Umbrel apps.state "
                f"returned HTTP {exc.code}: "
                f"{body}"
            ) from exc

        result = json.loads(body)

        if "error" in result:
            raise RuntimeError(
                json.dumps(
                    result["error"],
                    separators=(",", ":"),
                )
            )

        data = (
            result
            .get("result", {})
            .get("data")
        )

        if not isinstance(
            data,
            dict,
        ):
            raise RuntimeError(
                "Umbrel apps.state returned "
                "an invalid result."
            )

        return data

    def mutation(
        self,
        procedure: str,
        app_id: str,
    ) -> Any:
        payload = {
            "appId": app_id,
        }

        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode()

        url = (
            f"{self.endpoint}/"
            f"{procedure}"
        )

        request = Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization":
                    f"Bearer {self.token()}",
                "Accept":
                    "application/json",
                "Content-Type":
                    "application/json",
                "User-Agent":
                    "Seymour-Blockchain-Manager/1.0",
            },
        )

        try:
            with urlopen(
                request,
                timeout=self.mutation_timeout_seconds,
            ) as response:
                raw = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

        except HTTPError as exc:
            raw = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            raise RuntimeError(
                f"Umbrel {procedure} "
                f"returned HTTP {exc.code}: "
                f"{raw}"
            ) from exc

        if not raw.strip():
            return True

        result = json.loads(raw)

        if (
            isinstance(result, dict)
            and "error" in result
        ):
            raise RuntimeError(
                json.dumps(
                    result["error"],
                    separators=(",", ":"),
                )
            )

        if (
            isinstance(result, dict)
            and isinstance(
                result.get("result"),
                dict,
            )
            and "data"
            in result["result"]
        ):
            return result["result"]["data"]

        return result

    def invoke(
        self,
        action: str,
        app_id: str | None,
    ) -> Any:
        if not app_id:
            raise ValueError(
                f"{action} requires app_id"
            )

        if action == "state":
            return self.state(
                app_id
            )

        procedures = {
            "install": "apps.install",
            "uninstall": "apps.uninstall",
            "start": "apps.start",
            "stop": "apps.stop",
            "restart": "apps.restart",
            "update": "apps.update",
        }

        procedure = procedures.get(
            action
        )

        if procedure is None:
            raise RuntimeError(
                "Unsupported container-native "
                f"Umbrel action: {action}"
            )

        return self.mutation(
            procedure,
            app_id,
        )
