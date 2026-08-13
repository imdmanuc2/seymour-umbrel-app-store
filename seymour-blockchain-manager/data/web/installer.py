from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import socket
import subprocess
from typing import Any
from urllib import request
from uuid import uuid4

from shared.blockchain_install import evaluate as evaluate_install_preflight
from shared.blockchain_install.host import profile as host_profile
from shared.blockchain_install.binding import build_binding_plan
from storage_targets import storage_targets, target_by_id

CATALOG_PATH = Path(os.environ.get("PROVIDER_CATALOG_PATH", "/catalog/providers.v1.json"))
CONTROL_SCRIPT = Path(os.environ.get(
    "SEYMOUR_UMBREL_CONTROL_SCRIPT",
    "/control/seymour-umbrel-app",
))
EVIDENCE_PATH = Path(os.environ.get(
    "INSTALL_EVIDENCE_PATH",
    "/evidence/installations.jsonl",
))
OPERATIONS_PATH = Path(os.environ.get(
    "INSTALL_OPERATION_DIRECTORY",
    "/evidence/install-operations",
))

PROVIDERS = {
    "bitcoin-mainnet": {
        "appId": os.environ.get("BTC_APP_ID", "seymour-bitcoin-node"),
        "installScript": Path(os.environ.get(
            "SEYMOUR_BTC_INSTALL_SCRIPT",
            "/control/seymour-install-btc",
        )),
        "rpcPrefix": "BTC",
    },
    "bitcoin-cash-mainnet": {
        "appId": os.environ.get("BCH_APP_ID", "seymour-bch-node"),
        "installScript": Path(os.environ.get(
            "SEYMOUR_BCH_INSTALL_SCRIPT",
            "/control/seymour-install-bch",
        )),
        "rpcPrefix": "BCH",
    },
}

class InstallStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

@dataclass
class InstallRequest:
    provider_id: str
    app_id: str
    node_name: str
    rpc_user: str
    rpc_password: str
    rpc_port: int
    p2p_port: int
    storage_target_id: str
    confirmation: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstallRequest":
        return cls(
            provider_id=str(data.get("providerId", "")),
            app_id=str(data.get("appId", "")),
            node_name=str(data.get("nodeName", "")).strip(),
            rpc_user=str(data.get("rpcUser", "")).strip(),
            rpc_password=str(data.get("rpcPassword", "")),
            rpc_port=int(data.get("rpcPort", 8332)),
            p2p_port=int(data.get("p2pPort", 8333)),
            storage_target_id=str(data.get("storageTargetId", "")).strip(),
            confirmation=str(data.get("confirmation", "")),
        )

@dataclass
class InstallOperation:
    operation_id: str
    status: InstallStatus
    created_at: str
    updated_at: str
    request: dict[str, Any]
    preflight: dict[str, Any]
    result: Any = None
    verification: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        if "rpc_password" in payload["request"]:
            payload["request"]["rpc_password"] = "[REDACTED]"
        return payload

def utc_now() -> str:
    return datetime.now(UTC).isoformat()

def generate_credentials() -> dict[str, str]:
    return {"rpcUser": "seymour_rpc", "rpcPassword": secrets.token_urlsafe(32)}

def normalized_architecture() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "amd64"
    if machine in {"aarch64", "arm64"}:
        return "arm64"
    return machine

def _docker_available() -> bool:
    try:
        result = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"], capture_output=True, text=True, timeout=4, check=False)
        return result.returncode == 0
    except Exception:
        return False

def _network_available() -> bool:
    try:
        request.urlopen("https://ghcr.io/v2/", timeout=5)
        return True
    except Exception as exc:
        return getattr(exc, "code", None) == 401

def _port_available(port: int) -> bool:
    with socket.socket() as sock:
        try:
            sock.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False

def _provider(provider_id: str) -> dict[str, Any]:
    catalog = json.loads(CATALOG_PATH.read_text())
    return next(
        item for item in catalog["providers"]
        if item["providerId"] == provider_id
    )

def provider_runtime(provider_id: str) -> dict[str, Any]:
    if provider_id not in PROVIDERS:
        raise ValueError("Provider is not enabled for installation.")
    return PROVIDERS[provider_id]

def preflight(
    storage_target_id: str | None = None,
    provider_id: str = "bitcoin-cash-mainnet",
) -> dict[str, Any]:
    provider = _provider(provider_id)
    inventory = storage_targets()
    targets = inventory.get("targets", [])
    selected = target_by_id(storage_target_id) if storage_target_id else None
    if selected is None and targets:
        for item in sorted(targets, key=lambda value: int(value.get("free_bytes", 0)), reverse=True):
            candidate = target_by_id(item["target_id"])
            if candidate is not None:
                selected = candidate
                break
    checks = {
        "providerSelectable": provider["selectable"],
        "productionImage": provider["productionImage"],
        "networkAvailable": _network_available(),
        "ports": {
            "rpc": {"port": 8332, "available": _port_available(8332)},
            "p2p": {"port": 8333, "available": _port_available(8333)},
        },
        "storageTargets": inventory,
        "selectedStorageTargetId": selected.target_id if selected else None,
    }
    errors = []
    if not checks["providerSelectable"]: errors.append(f"{provider_id} is not selectable.")
    if not checks["productionImage"]: errors.append(f"{provider_id} has no production image.")
    if not checks["networkAvailable"]: errors.append("Container registry is unreachable.")
    common = None
    if selected is None:
        errors.append("No storage target is selected.")
    else:
        common = evaluate_install_preflight(provider=provider, host=host_profile(), storage_target=selected)
        errors.extend(common.errors)
    return {
        "compatible": not errors,
        "checks": checks,
        "errors": errors,
        "storagePreflight": common.to_dict() if common is not None else None,
    }

def validate_request(value: InstallRequest) -> None:
    runtime = provider_runtime(value.provider_id)
    expected_app_id = runtime["appId"]
    expected_confirmation = f"INSTALL-{expected_app_id}"

    if value.app_id != expected_app_id:
        raise ValueError("App ID does not match the selected provider.")
    if value.confirmation != expected_confirmation:
        raise ValueError("Installation confirmation token did not match.")
    if not value.node_name:
        raise ValueError("Node name is required.")
    if not value.storage_target_id:
        raise ValueError("Storage target is required.")
    if not value.rpc_user:
        raise ValueError("RPC user is required.")
    if len(value.rpc_password) < 24:
        raise ValueError("RPC password must contain at least 24 characters.")
    if not 1 <= value.rpc_port <= 65535 or not 1 <= value.p2p_port <= 65535:
        raise ValueError("Port is invalid.")

class Installer:
    def __init__(
        self,
        control_script: Path = CONTROL_SCRIPT,
        evidence_path: Path = EVIDENCE_PATH,
        operations_path: Path = OPERATIONS_PATH,
    ) -> None:
        self.control_script = control_script
        self.evidence_path = evidence_path
        self.operations_path = operations_path

    def _save(self, operation: InstallOperation) -> None:
        self.operations_path.mkdir(parents=True, exist_ok=True)
        (self.operations_path / f"{operation.operation_id}.json").write_text(json.dumps(operation.to_dict(), indent=2))
        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)
        with self.evidence_path.open("a") as handle:
            handle.write(json.dumps(operation.to_dict(), sort_keys=True) + "\n")

    def load(self, operation_id: str) -> dict[str, Any]:
        path = self.operations_path / f"{operation_id}.json"
        if not path.is_file():
            raise KeyError(operation_id)
        return json.loads(path.read_text())

    def execute(self, value: InstallRequest) -> InstallOperation:
        validate_request(value)
        runtime = provider_runtime(value.provider_id)
        checks = preflight(value.storage_target_id, value.provider_id)
        now = utc_now()
        operation = InstallOperation(str(uuid4()), InstallStatus.PLANNED, now, now, asdict(value), checks)
        self._save(operation)
        if not checks["compatible"]:
            operation.status = InstallStatus.FAILED
            operation.error = "Installation preflight failed."
            operation.updated_at = utc_now()
            self._save(operation)
            return operation
        operation.status = InstallStatus.RUNNING
        operation.updated_at = utc_now()
        self._save(operation)
        env = os.environ.copy()
        selected_target = target_by_id(value.storage_target_id)
        if selected_target is None:
            operation.status = InstallStatus.FAILED
            operation.error = "Selected storage target disappeared before execution."
            operation.updated_at = utc_now()
            self._save(operation)
            return operation

        binding = build_binding_plan(
            provider_id=value.provider_id,
            runtime_host=socket.gethostname(),
            storage_target=selected_target,
        )
        operation.preflight["storageBinding"] = binding.to_dict()

        if not binding.eligible:
            operation.status = InstallStatus.FAILED
            operation.error = "Selected storage target is not eligible for runtime binding."
            operation.updated_at = utc_now()
            self._save(operation)
            return operation

        data_path = Path(binding.data_path)
        try:
            data_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            operation.status = InstallStatus.FAILED
            operation.error = f"Unable to prepare selected blockchain data path: {exc}"
            operation.updated_at = utc_now()
            self._save(operation)
            return operation

        prefix = runtime["rpcPrefix"]
        env.update({
            f"{prefix}_RPC_USER": value.rpc_user,
            f"{prefix}_RPC_PASSWORD": value.rpc_password,
            f"{prefix}_RPC_PORT": str(value.rpc_port),
            f"{prefix}_P2P_PORT": str(value.p2p_port),
            "SEYMOUR_NODE_NAME": value.node_name,
            "SEYMOUR_BLOCKCHAIN_DATA_PATH": str(data_path),
        })

        install_script = runtime["installScript"]
        confirmation_token = f"INSTALL-{runtime['appId']}"

        try:
            completed = subprocess.run(
                [
                    str(install_script),
                    "--execute",
                    "--confirm",
                    confirmation_token,
                ],
                capture_output=True,
                text=True,
                timeout=900,
                check=False,
                env=env,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr or completed.stdout)
            operation.result = json.loads(completed.stdout)
            state = subprocess.run([str(self.control_script), "state", runtime["appId"]], capture_output=True, text=True, timeout=120, check=False)

            mount_verify = subprocess.run(
                ["docker", "inspect", f"{runtime['appId']}_node_1", "--format", "{{json .Mounts}}"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            mount_source = None
            if mount_verify.returncode == 0 and mount_verify.stdout.strip():
                try:
                    mounts = json.loads(mount_verify.stdout)
                    for item in mounts:
                        if item.get("Destination") == "/data":
                            mount_source = item.get("Source")
                            break
                except Exception:
                    mount_source = None

            requested_source = str(data_path.resolve())
            mount_matches = (
                mount_source is not None
                and str(Path(mount_source).resolve()) == requested_source
            )

            operation.verification = {
                "state": json.loads(state.stdout) if state.stdout else None,
                "stateVerified": state.returncode == 0,
                "storageBinding": binding.to_dict(),
                "requestedDataPath": requested_source,
                "runtimeDataMountSource": mount_source,
                "runtimeDataMountMatches": mount_matches,
                "verified": state.returncode == 0 and mount_matches,
            }
            operation.status = InstallStatus.SUCCEEDED if operation.verification["verified"] else InstallStatus.FAILED
            if not mount_matches:
                operation.error = "Runtime /data mount does not match the selected storage target."
        except Exception as exc:
            operation.status = InstallStatus.FAILED
            operation.error = str(exc)
        operation.updated_at = utc_now()
        self._save(operation)
        return operation
