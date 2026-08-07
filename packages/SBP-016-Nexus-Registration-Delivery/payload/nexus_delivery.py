from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any
from urllib import error, request


REGISTRATION_URL = os.environ.get(
    "NEXUS_REGISTRATION_URL",
    "",
).strip()

REGISTRATION_TOKEN = os.environ.get(
    "NEXUS_REGISTRATION_TOKEN",
    "",
).strip()

TIMEOUT_SECONDS = int(os.environ.get(
    "NEXUS_REGISTRATION_TIMEOUT_SECONDS",
    "15",
))

MAX_ATTEMPTS = int(os.environ.get(
    "NEXUS_REGISTRATION_MAX_ATTEMPTS",
    "4",
))

BACKOFF_SECONDS = float(os.environ.get(
    "NEXUS_REGISTRATION_BACKOFF_SECONDS",
    "2",
))

EVIDENCE_PATH = Path(os.environ.get(
    "NEXUS_DELIVERY_EVIDENCE_PATH",
    "/evidence/nexus-delivery.jsonl",
))

STATUS_PATH = Path(os.environ.get(
    "NEXUS_DELIVERY_STATUS_PATH",
    "/evidence/nexus-delivery-status.json",
))


@dataclass
class DeliveryResult:
    delivery_id: str
    registration_id: str
    status: str
    attempted_at: str
    attempts: int
    http_status: int | None = None
    response: Any = None
    error: str | None = None
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def delivery_id(registration_id: str) -> str:
    digest = hashlib.sha256(
        f"nexus-registration:{registration_id}".encode()
    ).hexdigest()[:20]
    return f"nexus-delivery-{digest}"


def idempotency_key(registration_id: str) -> str:
    return f"seymour-registration-{registration_id}"


def _write_result(result: DeliveryResult) -> None:
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = result.to_dict()

    with EVIDENCE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(payload, sort_keys=True) + "\n"
        )

    STATUS_PATH.write_text(
        json.dumps(payload, indent=2)
    )


def load_status() -> dict[str, Any]:
    if not STATUS_PATH.is_file():
        return {
            "status": "never-delivered",
            "deliveryId": None,
        }

    return json.loads(STATUS_PATH.read_text())


def validate_configuration() -> list[str]:
    errors: list[str] = []

    if not REGISTRATION_URL:
        errors.append("NEXUS_REGISTRATION_URL is required.")

    if not REGISTRATION_TOKEN:
        errors.append("NEXUS_REGISTRATION_TOKEN is required.")

    if MAX_ATTEMPTS < 1:
        errors.append(
            "NEXUS_REGISTRATION_MAX_ATTEMPTS must be at least 1."
        )

    if TIMEOUT_SECONDS < 1:
        errors.append(
            "NEXUS_REGISTRATION_TIMEOUT_SECONDS must be at least 1."
        )

    return errors


def deliver(
    payload: dict[str, Any],
    *,
    dry_run: bool = False,
    sleep_fn=time.sleep,
    opener=request.urlopen,
) -> DeliveryResult:
    registration_id = str(
        payload.get("registrationId", "")
    )

    if not registration_id:
        raise ValueError(
            "Registration payload is missing registrationId."
        )

    result = DeliveryResult(
        delivery_id=delivery_id(registration_id),
        registration_id=registration_id,
        status="planned",
        attempted_at=utc_now(),
        attempts=0,
        dry_run=dry_run,
    )

    if dry_run:
        result.status = "dry-run"
        result.response = {
            "urlConfigured": bool(REGISTRATION_URL),
            "tokenConfigured": bool(REGISTRATION_TOKEN),
            "idempotencyKey": (
                idempotency_key(registration_id)
            ),
            "payloadBytes": len(
                json.dumps(payload).encode()
            ),
        }
        _write_result(result)
        return result

    configuration_errors = validate_configuration()

    if configuration_errors:
        result.status = "failed"
        result.error = " ".join(configuration_errors)
        _write_result(result)
        return result

    body = json.dumps(payload).encode()

    headers = {
        "Authorization": f"Bearer {REGISTRATION_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Idempotency-Key": idempotency_key(
            registration_id
        ),
        "User-Agent": (
            "Seymour-Blockchain-Manager/1.0"
        ),
    }

    last_error: str | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        result.attempts = attempt

        try:
            outbound = request.Request(
                REGISTRATION_URL,
                data=body,
                headers=headers,
                method="POST",
            )

            with opener(
                outbound,
                timeout=TIMEOUT_SECONDS,
            ) as response:
                response_body = (
                    response.read().decode()
                )

                try:
                    parsed = json.loads(response_body)
                except json.JSONDecodeError:
                    parsed = {
                        "raw": response_body,
                    }

                result.http_status = int(
                    response.status
                )
                result.response = parsed

                if 200 <= response.status < 300:
                    result.status = "succeeded"
                    _write_result(result)
                    return result

                last_error = (
                    f"Nexus returned HTTP "
                    f"{response.status}."
                )

        except error.HTTPError as exc:
            result.http_status = int(exc.code)

            try:
                response_body = (
                    exc.read().decode()
                )
            except Exception:
                response_body = ""

            last_error = (
                f"Nexus returned HTTP "
                f"{exc.code}: {response_body}"
            )

            if 400 <= exc.code < 500 and exc.code != 429:
                break

        except Exception as exc:
            last_error = str(exc)

        if attempt < MAX_ATTEMPTS:
            sleep_fn(
                BACKOFF_SECONDS
                * (2 ** (attempt - 1))
            )

    result.status = "failed"
    result.error = last_error or (
        "Registration delivery failed."
    )
    _write_result(result)
    return result
