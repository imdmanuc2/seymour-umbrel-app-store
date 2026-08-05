from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


WRITE_ACTIONS = {
    "install",
    "uninstall",
    "start",
    "stop",
    "restart",
    "update",
}


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

        try:
            operation.result = self._invoke(
                action,
                app_id,
            )
            operation.executed = True
            operation.success = True
        except Exception as exc:
            operation.executed = True
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
