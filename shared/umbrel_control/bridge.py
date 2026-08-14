from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from shared.blockchain_install.start_guard import (
    resolve_storage_expectation,
    verify_expected_path,
)


WRITE_ACTIONS = {
    "install",
    "uninstall",
    "start",
    "stop",
    "restart",
    "update",
}


def _native_result_error(payload: object) -> str | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        for key in ("error", "message", "detail", "reason"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        nested = payload.get("result")
        if nested is not None:
            value = _native_result_error(nested)
            if value:
                return value
    if isinstance(payload, str):
        value = payload.strip()
        if value:
            return value
    return None


def _state_matches_action(action: str, state: object) -> bool:
    value = str(state or "").strip().lower()
    if action in {"start", "restart"}:
        return value in {"ready", "running"}
    if action == "stop":
        return value in {"stopped", "not-running", "inactive"}
    return False



@dataclass
class ControlOperation:
    operation_id: str
    action: str
    app_id: str | None
    mode: str
    created_at: str
    executed: bool
    success: bool | None
    result: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class UmbrelAppControlBridge:
    def __init__(
        self,
        *,
        helper_path: Path,
        data_directory: Path = Path("/home/umbrel/umbrel"),
        endpoint: str = "ws://localhost/trpc",
        evidence_directory: Path | None = None,
    ) -> None:
        self.helper_path = helper_path
        self.data_directory = data_directory
        self.endpoint = endpoint
        self.evidence_directory = (
            evidence_directory
            or Path("/home/umbrel/umbrel/seymour-evidence/app-control")
        )

    @staticmethod
    def utc_now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def confirmation_token(
        action: str,
        app_id: str,
    ) -> str:
        return f"{action.upper()}-{app_id}"

    def plan(
        self,
        action: str,
        app_id: str | None,
    ) -> ControlOperation:
        return ControlOperation(
            operation_id=str(uuid4()),
            action=action,
            app_id=app_id,
            mode="plan",
            created_at=self.utc_now(),
            executed=False,
            success=None,
            result={
                "writeOperation": action in WRITE_ACTIONS,
                "requiredConfirmation": (
                    self.confirmation_token(action, app_id)
                    if action in WRITE_ACTIONS and app_id
                    else None
                ),
                "nativeApi": True,
                "directDockerLifecycle": False,
            },
        )

    def _invoke(
        self,
        action: str,
        app_id: str | None,
    ) -> Any:
        command = [
            "/usr/local/bin/node",
            "--require",
            "/opt/umbreld/node_modules/tsx/dist/preflight.cjs",
            "--import",
            "file:///opt/umbreld/node_modules/tsx/dist/loader.mjs",
            str(self.helper_path),
            "--data-directory",
            str(self.data_directory),
            "--endpoint",
            self.endpoint,
            action,
        ]

        if app_id:
            command.append(app_id)

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=1800,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or result.stdout.strip()
                or f"Umbrel control helper failed with {result.returncode}"
            )

        return json.loads(result.stdout)

    def execute(
        self,
        action: str,
        app_id: str | None,
        *,
        execute: bool = False,
        confirmation: str | None = None,
    ) -> ControlOperation:
        operation = self.plan(action, app_id)

        if action in WRITE_ACTIONS:
            if not execute:
                return operation

            if app_id is None:
                raise ValueError(
                    f"{action} requires an app id."
                )

            expected = self.confirmation_token(
                action,
                app_id,
            )

            if confirmation != expected:
                raise ValueError(
                    "Confirmation mismatch. "
                    f"Expected: {expected}"
                )

        operation.mode = "execute"

        storage_expectation = None
        storage_preflight = None

        if app_id is not None and action in {"start", "restart"}:
            try:
                storage_expectation = resolve_storage_expectation(
                    data_directory=self.data_directory,
                    app_id=app_id,
                )
                if storage_expectation is not None:
                    storage_preflight = verify_expected_path(
                        storage_expectation
                    )
                    if not storage_preflight.get("healthy"):
                        raise RuntimeError(
                            "Blockchain storage pre-start guard blocked "
                            f"{app_id}: {storage_preflight}"
                        )
            except Exception as exc:
                operation.executed = False
                operation.success = False
                operation.error = str(exc)
                operation.result = {
                    "storageGuard": {
                        "phase": "pre-start",
                        "preflight": storage_preflight,
                    }
                }
                self.write_evidence(operation)
                return operation

        try:
            operation.result = self._invoke(
                action,
                app_id,
            )
            operation.executed = True
            operation.success = True

            if storage_expectation is not None:
                operation.result = {
                    "nativeResult": operation.result,
                    "storageGuard": {
                        "phase": "pre-start-verified",
                        "preflight": storage_preflight,
                        "postStartInspection": (
                            "delegated-to-privileged-runtime-observer"
                        ),
                    },
                }

        except Exception as exc:
            operation.executed = True
            if app_id is not None and action in {"start", "restart", "stop"}:
                try:
                    state_payload = self._invoke("state", app_id)
                    state = state_payload.get("result", state_payload) if isinstance(state_payload, dict) else state_payload
                    current_state = state.get("state") if isinstance(state, dict) else state
                    if _state_matches_action(action, current_state):
                        operation.success = True
                        operation.error = None
                        operation.result = {
                            "reconciled": True,
                            "state": current_state,
                            "nativeError": str(exc),
                            "statePayload": state_payload,
                        }
                    else:
                        operation.success = False
                        operation.error = _native_result_error(state_payload) or str(exc)
                except Exception as state_exc:
                    operation.success = False
                    operation.error = str(exc) + " Post-operation state reconciliation failed: " + str(state_exc)
            else:
                operation.success = False
                operation.error = str(exc)

        self.write_evidence(operation)
        return operation

    def write_evidence(
        self,
        operation: ControlOperation,
    ) -> Path:
        self.evidence_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = (
            self.evidence_directory
            / f"{operation.operation_id}.json"
        )
        path.write_text(
            json.dumps(
                operation.to_dict(),
                indent=2,
            )
            + "\n"
        )
        return path

    def wait_for_state(
        self,
        app_id: str,
        *,
        accepted_states: set[str],
        timeout_seconds: int = 900,
        interval_seconds: int = 5,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        latest: dict[str, Any] = {}

        while time.monotonic() < deadline:
            latest = self._invoke(
                "state",
                app_id,
            )

            state = (
                latest.get("result", latest)
                if isinstance(latest, dict)
                else latest
            )

            if isinstance(state, dict):
                current = state.get("state")
                if current in accepted_states:
                    return latest

            time.sleep(interval_seconds)

        raise TimeoutError(
            f"Timed out waiting for {app_id}: "
            f"{sorted(accepted_states)}; latest={latest}"
        )
