from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shared.blockchain_install.runtime_binding import (
    persist_runtime_binding,
)


PROVIDER_ID = "bitcoin-mainnet"
APP_ID = "seymour-bitcoin-node"
DEFAULT_DATA_PATH = Path(
    "/mnt/seymour-storage/bitcoin-mainnet"
)


@dataclass
class BitcoinManagedRuntimeWorkflow:
    repository: Path
    umbrel_data_directory: Path = Path(
        "/home/umbrel/umbrel"
    )
    data_path: Path = DEFAULT_DATA_PATH

    @property
    def manifest_path(self) -> Path:
        return (
            self.repository
            / APP_ID
            / "umbrel-app.yml"
        )

    @property
    def installed_app_path(self) -> Path:
        return (
            self.umbrel_data_directory
            / "app-data"
            / APP_ID
        )

    @property
    def installed_compose_path(self) -> Path:
        return (
            self.installed_app_path
            / "docker-compose.yml"
        )

    @property
    def control_script(self) -> Path:
        return (
            self.repository
            / "scripts"
            / "seymour-umbrel-app"
        )

    def _run(
        self,
        command: list[str],
        timeout: int = 1800,
    ) -> dict[str, Any]:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        payload: Any = None

        if result.stdout.strip():
            try:
                payload = json.loads(
                    result.stdout
                )
            except Exception:
                payload = result.stdout.strip()

        return {
            "command": command,
            "returnCode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "payload": payload,
            "success": result.returncode == 0,
        }

    def storage_preflight(self) -> dict[str, Any]:
        path = self.data_path

        result: dict[str, Any] = {
            "path": str(path),
            "exists": path.exists(),
            "isDirectory": path.is_dir(),
            "writable": False,
            "mount": None,
            "healthy": False,
            "errors": [],
        }

        if not path.exists():
            result["errors"].append(
                "bitcoin-data-path-missing"
            )
            return result

        if not path.is_dir():
            result["errors"].append(
                "bitcoin-data-path-not-directory"
            )
            return result

        probe = subprocess.run(
            ["findmnt", "-J", "-T", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if (
            probe.returncode != 0
            or not probe.stdout.strip()
        ):
            result["errors"].append(
                "bitcoin-data-mount-not-found"
            )
            return result

        try:
            fs = json.loads(
                probe.stdout
            )["filesystems"][0]

            mount = {
                "target": fs.get("target"),
                "source": fs.get("source"),
                "fstype": fs.get("fstype"),
            }

            result["mount"] = mount

            if mount.get("target") == "/":
                result["errors"].append(
                    "bitcoin-data-false-root-mount"
                )
        except Exception:
            result["errors"].append(
                "bitcoin-data-mount-probe-invalid"
            )
            return result

        try:
            test = (
                path
                / ".seymour-bitcoin-write-test"
            )
            test.touch(exist_ok=False)
            test.unlink()
            result["writable"] = True
        except Exception:
            # Root-owned NFS paths can still be writable by the
            # runtime/container even if the current shell user
            # cannot write directly. Treat this as advisory.
            result["writable"] = False

        result["healthy"] = (
            not result["errors"]
        )

        return result

    def repository_preflight(
        self,
    ) -> dict[str, Any]:
        return {
            "providerId": PROVIDER_ID,
            "appId": APP_ID,
            "manifestExists": (
                self.manifest_path.is_file()
            ),
            "controlScriptExists": (
                self.control_script.is_file()
            ),
            "storage": self.storage_preflight(),
        }

    def install_plan(self) -> dict[str, Any]:
        preflight = self.repository_preflight()

        return {
            "mode": "plan",
            "providerId": PROVIDER_ID,
            "appId": APP_ID,
            "dataPath": str(self.data_path),
            "compatible": bool(
                preflight["manifestExists"]
                and preflight[
                    "controlScriptExists"
                ]
                and preflight[
                    "storage"
                ]["healthy"]
            ),
            "preflight": preflight,
            "requiredConfirmation": (
                f"INSTALL-{APP_ID}"
            ),
            "steps": [
                "verify-provider-definition",
                "verify-storage-mount",
                "native-umbrel-install",
                "persist-runtime-data-binding",
                "verify-installed-compose",
            ],
        }

    def install(
        self,
        confirmation: str,
    ) -> dict[str, Any]:
        plan = self.install_plan()

        if not plan["compatible"]:
            raise RuntimeError(
                f"Bitcoin install preflight failed: "
                f"{plan['preflight']}"
            )

        expected = f"INSTALL-{APP_ID}"

        if confirmation != expected:
            raise RuntimeError(
                "Confirmation mismatch. "
                f"Expected: {expected}"
            )

        install_result = self._run(
            [
                str(self.control_script),
                "install",
                APP_ID,
                "--execute",
                "--confirm",
                expected,
            ]
        )

        if not install_result["success"]:
            return {
                "success": False,
                "phase": "native-install",
                "installResult": install_result,
            }

        if not self.installed_compose_path.is_file():
            return {
                "success": False,
                "phase": "persist-binding",
                "error": (
                    "Installed Bitcoin compose "
                    "not found after native install."
                ),
                "installResult": install_result,
            }

        binding = persist_runtime_binding(
            provider_id=PROVIDER_ID,
            app_id=APP_ID,
            compose_path=(
                self.installed_compose_path
            ),
            data_path=self.data_path,
        )

        compose_text = (
            self.installed_compose_path
            .read_text()
        )

        persisted = (
            f"{self.data_path}:/data"
            in compose_text
        )

        return {
            "success": persisted,
            "phase": "installed",
            "installResult": install_result,
            "binding": binding.to_dict(),
            "persisted": persisted,
        }

    def start_plan(self) -> dict[str, Any]:
        return {
            "mode": "plan",
            "providerId": PROVIDER_ID,
            "appId": APP_ID,
            "requiredConfirmation": (
                f"START-{APP_ID}"
            ),
            "storage": self.storage_preflight(),
            "installedCompose": str(
                self.installed_compose_path
            ),
        }

    def start(
        self,
        confirmation: str,
    ) -> dict[str, Any]:
        expected = f"START-{APP_ID}"

        if confirmation != expected:
            raise RuntimeError(
                "Confirmation mismatch. "
                f"Expected: {expected}"
            )

        if not self.installed_compose_path.is_file():
            raise RuntimeError(
                "Bitcoin runtime is not installed."
            )

        storage = self.storage_preflight()

        if not storage["healthy"]:
            raise RuntimeError(
                "Bitcoin storage preflight failed: "
                f"{storage}"
            )

        result = self._run(
            [
                str(self.control_script),
                "start",
                APP_ID,
                "--execute",
                "--confirm",
                expected,
            ]
        )

        return {
            "success": result["success"],
            "phase": "start",
            "storage": storage,
            "result": result,
        }


def utc_now() -> str:
    return datetime.now(UTC).isoformat()
