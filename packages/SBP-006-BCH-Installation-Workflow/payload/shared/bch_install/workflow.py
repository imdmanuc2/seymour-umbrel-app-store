from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


APP_ID = "seymour-bch-node"
EXPECTED_VERSION = "0.2.2-alpha"
DEFAULT_MINIMUM_FREE_BYTES = 600_000_000_000


@dataclass
class InstallEvidence:
    operation_id: str
    mode: str
    app_id: str
    created_at: str
    started_at: str | None
    completed_at: str | None
    status: str
    preflight: dict[str, Any]
    install_result: dict[str, Any] | None
    final_state: dict[str, Any] | None
    runtime: dict[str, Any] | None
    health: dict[str, Any] | None
    cleanup_recommendation: dict[str, Any] | None
    error: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BchInstallWorkflow:
    def __init__(
        self,
        *,
        repository: Path,
        data_directory: Path,
        control_script: Path,
        runtime_script: Path,
        evidence_directory: Path,
        dashboard_host: str = "127.0.0.1",
        dashboard_port: int = 8563,
        minimum_free_bytes: int = DEFAULT_MINIMUM_FREE_BYTES,
    ) -> None:
        self.repository = repository
        self.data_directory = data_directory
        self.control_script = control_script
        self.runtime_script = runtime_script
        self.evidence_directory = evidence_directory
        self.dashboard_host = dashboard_host
        self.dashboard_port = dashboard_port
        self.minimum_free_bytes = minimum_free_bytes

    @staticmethod
    def utc_now() -> str:
        return datetime.now(UTC).isoformat()

    def manifest_path(self) -> Path:
        return (
            self.repository
            / APP_ID
            / "umbrel-app.yml"
        )

    def read_manifest_value(
        self,
        key: str,
    ) -> str | None:
        path = self.manifest_path()

        if not path.exists():
            return None

        prefix = f"{key}:"

        for line in path.read_text().splitlines():
            if line.startswith(prefix):
                return (
                    line.split(":", 1)[1]
                    .strip()
                    .strip('"')
                )

        return None

    def app_store_copy(self) -> Path | None:
        root = self.data_directory / "app-stores"

        if not root.is_dir():
            return None

        candidates = sorted(
            root.glob(
                "imdmanuc2-seymour-umbrel-app-store-*"
            )
        )

        for candidate in reversed(candidates):
            app = candidate / APP_ID

            if (
                app / "umbrel-app.yml"
            ).is_file():
                return app

        return None

    def storage_check(self) -> dict[str, Any]:
        target = self.data_directory

        try:
            usage = shutil.disk_usage(target)
        except Exception as exc:
            return {
                "healthy": False,
                "path": str(target),
                "error": str(exc),
            }

        return {
            "healthy": (
                usage.free
                >= self.minimum_free_bytes
            ),
            "path": str(target),
            "totalBytes": usage.total,
            "usedBytes": usage.used,
            "freeBytes": usage.free,
            "minimumFreeBytes": (
                self.minimum_free_bytes
            ),
        }

    def run_json(
        self,
        command: list[str],
        *,
        timeout: int = 1800,
    ) -> dict[str, Any]:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )

        if not result.stdout.strip():
            raise RuntimeError(
                result.stderr.strip()
                or "Command returned no JSON."
            )

        payload = json.loads(
            result.stdout
        )

        if result.returncode != 0:
            raise RuntimeError(
                payload.get("error")
                or payload.get("message")
                or result.stderr.strip()
                or "Command failed."
            )

        return payload

    def current_state(self) -> dict[str, Any]:
        return self.run_json(
            [
                str(self.control_script),
                "state",
                APP_ID,
            ],
            timeout=60,
        )

    def runtime_state(self) -> dict[str, Any]:
        return self.run_json(
            [
                str(self.runtime_script),
                "show",
                APP_ID,
                "--health-host",
                self.dashboard_host,
                "--health-port",
                str(self.dashboard_port),
            ],
            timeout=60,
        )

    def preflight(self) -> dict[str, Any]:
        local_version = self.read_manifest_value(
            "version"
        )
        store_copy = self.app_store_copy()
        store_version = None

        if store_copy is not None:
            manifest = store_copy / "umbrel-app.yml"

            for line in manifest.read_text().splitlines():
                if line.startswith("version:"):
                    store_version = (
                        line.split(":", 1)[1]
                        .strip()
                        .strip('"')
                    )
                    break

        storage = self.storage_check()

        checks = {
            "repositoryManifest": (
                self.manifest_path().is_file()
            ),
            "localVersion": local_version,
            "expectedVersion": EXPECTED_VERSION,
            "localVersionValid": (
                local_version == EXPECTED_VERSION
            ),
            "appStoreCopyFound": (
                store_copy is not None
            ),
            "appStoreCopy": (
                str(store_copy)
                if store_copy
                else None
            ),
            "appStoreVersion": store_version,
            "appStoreVersionValid": (
                store_version == EXPECTED_VERSION
            ),
            "controlBridgeAvailable": (
                self.control_script.is_file()
            ),
            "runtimeBridgeAvailable": (
                self.runtime_script.is_file()
            ),
            "umbrelJwtAvailable": (
                self.data_directory
                / "secrets"
                / "jwt"
            ).is_file(),
            "storage": storage,
        }

        compatible = all(
            [
                checks["repositoryManifest"],
                checks["localVersionValid"],
                checks["appStoreCopyFound"],
                checks["appStoreVersionValid"],
                checks["controlBridgeAvailable"],
                checks["runtimeBridgeAvailable"],
                checks["umbrelJwtAvailable"],
                storage["healthy"],
            ]
        )

        return {
            "compatible": compatible,
            "checks": checks,
        }

    def installation_plan(
        self,
    ) -> dict[str, Any]:
        preflight = self.preflight()

        return {
            "mode": "plan",
            "appId": APP_ID,
            "compatible": preflight["compatible"],
            "preflight": preflight,
            "steps": [
                "capture-current-state",
                "call-umbrel-native-install",
                "poll-install-state",
                "inspect-runtime-containers",
                "probe-dashboard",
                "probe-health-endpoint",
                "write-operation-evidence",
            ],
            "requiredConfirmation": (
                "INSTALL-seymour-bch-node"
            ),
            "automaticUninstallOnFailure": False,
        }

    def install(
        self,
        *,
        execute: bool = False,
        confirmation: str | None = None,
        timeout_seconds: int = 1800,
    ) -> InstallEvidence:
        operation = InstallEvidence(
            operation_id=str(uuid4()),
            mode=(
                "execute"
                if execute
                else "plan"
            ),
            app_id=APP_ID,
            created_at=self.utc_now(),
            started_at=None,
            completed_at=None,
            status="planned",
            preflight=self.preflight(),
            install_result=None,
            final_state=None,
            runtime=None,
            health=None,
            cleanup_recommendation=None,
            error=None,
        )

        if not execute:
            self.write_evidence(operation)
            return operation

        if (
            confirmation
            != "INSTALL-seymour-bch-node"
        ):
            raise ValueError(
                "Confirmation mismatch. Expected "
                "INSTALL-seymour-bch-node"
            )

        if not operation.preflight["compatible"]:
            operation.status = "blocked"
            operation.error = (
                "Installation preflight failed."
            )
            operation.completed_at = self.utc_now()
            self.write_evidence(operation)
            return operation

        operation.started_at = self.utc_now()
        operation.status = "installing"

        try:
            before = self.current_state()

            operation.install_result = self.run_json(
                [
                    str(self.control_script),
                    "install",
                    APP_ID,
                    "--execute",
                    "--confirm",
                    "INSTALL-seymour-bch-node",
                ],
                timeout=timeout_seconds,
            )

            deadline = (
                time.monotonic()
                + timeout_seconds
            )
            latest = {}

            while time.monotonic() < deadline:
                latest = self.current_state()
                result = latest.get(
                    "result",
                    latest,
                )

                nested = result.get(
                    "result",
                    result,
                )

                state = (
                    nested.get("data")
                    or nested.get("json")
                    or nested
                )

                current = (
                    state.get("state")
                    if isinstance(state, dict)
                    else None
                )

                if current in {
                    "ready",
                    "running",
                    "stopped",
                }:
                    break

                if current in {
                    "failed",
                    "broken",
                }:
                    raise RuntimeError(
                        f"Umbrel reported state: {current}"
                    )

                time.sleep(5)

            operation.final_state = latest
            operation.runtime = self.runtime_state()
            operation.health = self.probe_health()
            operation.status = "installed"
            operation.completed_at = self.utc_now()
            operation.cleanup_recommendation = None

        except Exception as exc:
            operation.status = "failed"
            operation.error = str(exc)
            operation.completed_at = self.utc_now()
            operation.cleanup_recommendation = {
                "automaticCleanupPerformed": False,
                "recommendedAction": (
                    "Inspect state and logs before "
                    "running guarded uninstall."
                ),
                "stateCommand": (
                    "./scripts/seymour-umbrel-app "
                    "state seymour-bch-node"
                ),
                "logsCommand": (
                    "./scripts/seymour-umbrel-app "
                    "logs seymour-bch-node"
                ),
                "uninstallCommand": (
                    "./scripts/seymour-umbrel-app "
                    "uninstall seymour-bch-node "
                    "--execute "
                    "--confirm "
                    "UNINSTALL-seymour-bch-node"
                ),
            }

        self.write_evidence(operation)
        return operation

    def probe_health(self) -> dict[str, Any]:
        url = (
            f"http://{self.dashboard_host}:"
            f"{self.dashboard_port}/api/health"
        )

        try:
            with urllib.request.urlopen(
                url,
                timeout=10,
            ) as response:
                body = response.read().decode()

            return {
                "reachable": True,
                "statusCode": response.status,
                "payload": json.loads(body),
                "url": url,
            }

        except urllib.error.HTTPError as exc:
            body = exc.read().decode(
                errors="replace"
            )

            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {
                    "raw": body,
                }

            return {
                "reachable": True,
                "statusCode": exc.code,
                "payload": payload,
                "url": url,
            }

        except Exception as exc:
            return {
                "reachable": False,
                "error": str(exc),
                "url": url,
            }

    def write_evidence(
        self,
        operation: InstallEvidence,
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
