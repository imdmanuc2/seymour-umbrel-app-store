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

from shared.blockchain_install import (
    HostProfile,
    StorageTarget,
    evaluate as evaluate_install_preflight,
)
from shared.blockchain_install.host import profile as host_profile
from shared.blockchain_install.binding import build_binding_plan
from storage_targets import storage_targets, target_by_id
from shared.blockchain_install.storage import verify_storage_target

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
BINDING_CONFIG_ROOT = Path(os.environ.get(
    "RUNTIME_BINDING_CONFIG_DIRECTORY",
    "/evidence/runtime-bindings",
))

BCH_LOCAL_DATA_PATH = Path(
    os.environ.get(
        "SEYMOUR_BCH_LOCAL_DATA_PATH",
        "/home/umbrel/umbrel/app-data/seymour-bch-node/data/node",
    )
)

INSTALL_ADAPTERS = {
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

def _runtime_contract(provider: dict[str, Any]) -> dict[str, Any]:
    runtime = provider.get("runtime")
    if not isinstance(runtime, dict):
        raise ValueError("Provider runtime contract is missing.")
    return runtime


def _rpc_contract(provider: dict[str, Any]) -> dict[str, Any]:
    rpc = _runtime_contract(provider).get("rpc")
    if not isinstance(rpc, dict):
        raise ValueError("Provider RPC contract is missing.")
    return rpc


def _p2p_contract(provider: dict[str, Any]) -> dict[str, Any]:
    p2p = _runtime_contract(provider).get("p2p")
    if not isinstance(p2p, dict):
        raise ValueError("Provider P2P contract is missing.")
    return p2p


def _runtime_port(contract: dict[str, Any], name: str) -> int:
    value = int(contract.get("port", 0))
    if not 1 <= value <= 65535:
        raise ValueError(f"Provider {name} port is invalid.")
    return value


def _rpc_authentication(provider: dict[str, Any]) -> str:
    value = str(_rpc_contract(provider).get("authentication") or "").strip()
    if value not in {"none", "username-password"}:
        raise ValueError("Provider RPC authentication contract is unsupported.")
    return value


def provider_runtime(provider_id: str) -> dict[str, Any]:
    provider = _provider(provider_id)
    runtime = _runtime_contract(provider)

    adapter = INSTALL_ADAPTERS.get(provider_id)

    result = dict(runtime)
    result["providerId"] = provider_id
    result["selectable"] = bool(provider.get("selectable"))
    result["productionImage"] = provider.get("productionImage")
    result["installAdapterEnabled"] = adapter is not None

    if adapter is not None:
        result.update(adapter)

    return result

def _preflight_host_profile() -> HostProfile:
    base = host_profile()

    docker_socket = Path(
        os.environ.get(
            "DOCKER_SOCKET",
            "/var/run/docker.sock",
        )
    )

    umbrel_control = Path(
        os.environ.get(
            "SEYMOUR_UMBREL_CONTROL_SCRIPT",
            "/control/seymour-umbrel-app",
        )
    )

    return HostProfile(
        hostname=base.hostname,
        architecture=base.architecture,
        cpu_count=base.cpu_count,
        memory_total_bytes=base.memory_total_bytes,
        docker_available=(
            base.docker_available
            or docker_socket.exists()
        ),
        umbrel_available=(
            base.umbrel_available
            or umbrel_control.is_file()
        ),
    )


def _preflight_storage_target(
    selected: StorageTarget,
) -> StorageTarget:
    canonical = os.environ.get(
        "SEYMOUR_STORAGE_CANONICAL_HOST_PATH",
        "",
    ).strip()

    probe = os.environ.get(
        "SEYMOUR_STORAGE_PROBE_PATH",
        "",
    ).strip()

    if (
        not canonical
        or not probe
        or selected.path != canonical
    ):
        return selected

    probe_path = Path(probe)

    return StorageTarget(
        target_id=selected.target_id,
        target_type=selected.target_type,
        host=selected.host,
        path=str(probe_path),
        filesystem=selected.filesystem,
        source=selected.source,
        total_bytes=selected.total_bytes,
        used_bytes=selected.used_bytes,
        free_bytes=selected.free_bytes,
        writable=selected.writable,
        persistent=selected.persistent,
        reachable=selected.reachable,
        mount_point=str(probe_path),
        remote_host=selected.remote_host,
        filesystem_uuid=selected.filesystem_uuid,
    )


def _preflight_data_path(
    selected: StorageTarget,
    canonical_path: Path,
) -> Path:
    canonical_root = os.environ.get(
        "SEYMOUR_STORAGE_CANONICAL_HOST_PATH",
        "",
    ).strip()

    probe_root = os.environ.get(
        "SEYMOUR_STORAGE_PROBE_PATH",
        "",
    ).strip()

    if (
        not canonical_root
        or not probe_root
        or selected.path != canonical_root
    ):
        return canonical_path

    try:
        relative = canonical_path.relative_to(
            Path(canonical_root)
        )
    except ValueError:
        return canonical_path

    return Path(probe_root) / relative


def _decode_http_chunked(
    body: bytes,
) -> bytes:
    decoded = bytearray()
    position = 0

    while True:
        line_end = body.find(
            b"\r\n",
            position,
        )

        if line_end < 0:
            raise ValueError(
                "Invalid chunked Docker response."
            )

        size_text = body[
            position:line_end
        ].split(
            b";",
            1,
        )[0].strip()

        try:
            size = int(size_text, 16)
        except ValueError as exc:
            raise ValueError(
                "Invalid Docker chunk size."
            ) from exc

        position = line_end + 2

        if size == 0:
            return bytes(decoded)

        chunk_end = position + size

        if chunk_end > len(body):
            raise ValueError(
                "Truncated Docker chunk."
            )

        decoded.extend(
            body[position:chunk_end]
        )

        position = chunk_end

        if body[
            position:position + 2
        ] != b"\r\n":
            raise ValueError(
                "Invalid Docker chunk terminator."
            )

        position += 2


def _docker_container_mounts(
    container_name: str,
) -> list[dict[str, Any]]:
    socket_path = os.environ.get(
        "DOCKER_SOCKET",
        "/var/run/docker.sock",
    )

    client = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
    )

    try:
        client.settimeout(10)
        client.connect(socket_path)

        request = (
            f"GET /containers/{container_name}/json HTTP/1.1\r\n"
            "Host: docker\r\n"
            "Connection: close\r\n"
            "\r\n"
        )

        client.sendall(request.encode())

        chunks = []

        while True:
            chunk = client.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)

    finally:
        client.close()

    raw = b"".join(chunks)

    if b"\r\n\r\n" not in raw:
        raise RuntimeError(
            "Docker API returned an invalid response."
        )

    header, body = raw.split(b"\r\n\r\n", 1)

    status_line = header.splitlines()[0].decode(
        errors="replace"
    )

    if " 200 " not in status_line:
        raise RuntimeError(
            "Docker API container inspection failed: "
            + status_line
        )

    if b"transfer-encoding: chunked" in header.lower():
        body = _decode_http_chunked(body)

    payload = json.loads(body.decode())

    mounts = payload.get("Mounts", [])

    return mounts if isinstance(mounts, list) else []


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
            "rpc": {
                "port": _runtime_port(_rpc_contract(provider), "RPC"),
                "available": _port_available(
                    _runtime_port(_rpc_contract(provider), "RPC")
                ),
            },
            "p2p": {
                "port": _runtime_port(_p2p_contract(provider), "P2P"),
                "available": _port_available(
                    _runtime_port(_p2p_contract(provider), "P2P")
                ),
            },
        },
        "rpcAuthentication": _rpc_authentication(provider),
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
        common = evaluate_install_preflight(
            provider=provider,
            host=_preflight_host_profile(),
            storage_target=_preflight_storage_target(
                selected
            ),
        )
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
    provider = _provider(value.provider_id)
    rpc_authentication = _rpc_authentication(provider)

    if rpc_authentication == "username-password":
        if not value.rpc_user:
            raise ValueError("RPC user is required.")
        if len(value.rpc_password) < 24:
            raise ValueError(
                "RPC password must contain at least 24 characters."
            )

    expected_rpc_port = _runtime_port(_rpc_contract(provider), "RPC")
    expected_p2p_port = _runtime_port(_p2p_contract(provider), "P2P")

    if value.rpc_port != expected_rpc_port:
        raise ValueError(
            f"RPC port does not match provider contract: expected {expected_rpc_port}."
        )

    if value.p2p_port != expected_p2p_port:
        raise ValueError(
            f"P2P port does not match provider contract: expected {expected_p2p_port}."
        )

def _write_runtime_binding_config(
    *,
    app_id: str,
    data_path: Path,
    blocks_path: Path,
) -> dict[str, str]:
    BINDING_CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
    path = BINDING_CONFIG_ROOT / f"{app_id}.env"
    temporary = path.with_suffix(".env.tmp")
    payload = (
        "SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH="
        f"{data_path}\n"
        "SEYMOUR_BLOCKCHAIN_BLOCKS_PATH="
        f"{blocks_path}\n"
    )
    temporary.write_text(payload)
    temporary.chmod(0o600)
    temporary.replace(path)
    return {
        "path": str(path),
        "localDataPath": str(data_path),
        "blocksPath": str(blocks_path),
    }


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

    def list_recent(
        self,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        if not self.operations_path.is_dir():
            return []

        operations: list[dict[str, Any]] = []

        for path in self.operations_path.glob("*.json"):
            try:
                payload = json.loads(path.read_text())
            except Exception:
                continue

            if isinstance(payload, dict):
                operations.append(payload)

        operations.sort(
            key=lambda item: str(
                item.get("updated_at")
                or item.get("updatedAt")
                or item.get("created_at")
                or item.get("createdAt")
                or ""
            ),
            reverse=True,
        )

        return operations[:max(0, int(limit))]

    def _active_install_for_app(self, app_id: str) -> dict[str, Any] | None:
        now = datetime.now(UTC)
        for payload in self.list_recent(limit=100):
            request_payload = payload.get("request", {})
            if not isinstance(request_payload, dict):
                continue
            candidate_app_id = str(
                request_payload.get("app_id")
                or request_payload.get("appId")
                or ""
            )
            if candidate_app_id != app_id or payload.get("status") != InstallStatus.RUNNING.value:
                continue
            updated_raw = str(payload.get("updated_at") or payload.get("updatedAt") or "")
            try:
                updated = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
                if (now - updated).total_seconds() > 3600:
                    continue
            except Exception:
                pass
            return payload
        return None

    def execute(self, value: InstallRequest) -> InstallOperation:
        validate_request(value)
        runtime = provider_runtime(value.provider_id)
        if not runtime.get("installAdapterEnabled"):
            raise ValueError("Provider installation adapter is not enabled.")
        active = self._active_install_for_app(value.app_id)
        if active is not None:
            now = utc_now()
            operation = InstallOperation(
                str(uuid4()),
                InstallStatus.FAILED,
                now,
                now,
                asdict(value),
                {},
                error=(
                    "Installation already in progress for "
                    f"{value.app_id}; active operation "
                    f"{active.get('operation_id') or active.get('operationId') or 'unknown'}."
                ),
            )
            self._save(operation)
            return operation
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
            target_is_data_root=(
                selected_target.target_type.value
                == "remote"
            ),
        )
        operation.preflight["storageBinding"] = binding.to_dict()

        if not binding.eligible:
            operation.status = InstallStatus.FAILED
            operation.error = "Selected storage target is not eligible for runtime binding."
            operation.updated_at = utc_now()
            self._save(operation)
            return operation

        data_path = Path(binding.data_path)

        storage_preflight = (
            checks.get("storagePreflight", {})
            if isinstance(checks, dict)
            else {}
        )

        capacity = (
            storage_preflight.get("capacity", {})
            if isinstance(storage_preflight, dict)
            else {}
        )

        required_bytes = (
            int(capacity.get("required_bytes", 0))
            if isinstance(capacity, dict)
            else 0
        )

        probe_target = _preflight_storage_target(
            selected_target
        )

        probe_data_path = _preflight_data_path(
            selected_target,
            data_path,
        )

        storage_guard = verify_storage_target(
            probe_target,
            minimum_free_bytes=required_bytes,
            data_path=probe_data_path,
        )
        operation.preflight["storageMountGuard"] = storage_guard
        if not storage_guard["healthy"]:
            operation.status = InstallStatus.FAILED
            operation.error = (
                "Selected blockchain storage failed live mount identity verification: "
                + "; ".join(str(item) for item in storage_guard["errors"])
            )
            operation.updated_at = utc_now()
            self._save(operation)
            return operation
        hybrid_bch = (
            value.provider_id == "bitcoin-cash-mainnet"
            and selected_target.target_type.value == "remote"
        )
        runtime_data_path = (
            BCH_LOCAL_DATA_PATH
            if hybrid_bch
            else data_path
        )

        runtime_blocks_path = (
            data_path / "blocks"
            if hybrid_bch
            else None
        )

        try:
            if hybrid_bch:
                assert runtime_blocks_path is not None

                probe_blocks_path = _preflight_data_path(
                    selected_target,
                    runtime_blocks_path,
                )

                probe_blocks_path.mkdir(
                    parents=True,
                    exist_ok=True,
                )

            else:
                runtime_data_path.mkdir(
                    parents=True,
                    exist_ok=True,
                )

        except Exception as exc:
            operation.status = InstallStatus.FAILED
            operation.error = (
                "Unable to prepare selected blockchain "
                f"storage layout: {exc}"
            )
            operation.updated_at = utc_now()
            self._save(operation)
            return operation
        operation.preflight["storageLayout"] = {
            "mode": "hybrid" if hybrid_bch else "single-path",
            "localDataPath": str(runtime_data_path),
            "remoteBulkRoot": str(data_path) if hybrid_bch else None,
            "remoteBlocksPath": str(runtime_blocks_path) if runtime_blocks_path is not None else None,
        }

        prefix = runtime["rpcPrefix"]
        env.update({
            f"{prefix}_RPC_USER": value.rpc_user,
            f"{prefix}_RPC_PASSWORD": value.rpc_password,
            f"{prefix}_RPC_PORT": str(value.rpc_port),
            f"{prefix}_P2P_PORT": str(value.p2p_port),
            "SEYMOUR_NODE_NAME": value.node_name,
            "SEYMOUR_BLOCKCHAIN_DATA_PATH": str(data_path),
            "SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH": str(runtime_data_path),
            "SEYMOUR_BLOCKCHAIN_BLOCKS_PATH": str(runtime_blocks_path if runtime_blocks_path is not None else runtime_data_path / "blocks"),
        })

        if value.provider_id == "bitcoin-cash-mainnet":
            binding_config = _write_runtime_binding_config(
                app_id=runtime["appId"],
                data_path=runtime_data_path,
                blocks_path=(
                    runtime_blocks_path
                    if runtime_blocks_path is not None
                    else runtime_data_path / "blocks"
                ),
            )
            operation.preflight["runtimeBindingConfig"] = binding_config
            self._save(operation)

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

            mounts = _docker_container_mounts(
                f"{runtime['appId']}_node_1"
            )

            mount_source = None
            blocks_mount_source = None

            for item in mounts:
                if item.get("Destination") == "/data":
                    mount_source = item.get("Source")

                elif item.get("Destination") == "/data/blocks":
                    blocks_mount_source = item.get("Source")

            requested_source = str(runtime_data_path.resolve())
            mount_matches = mount_source is not None and str(Path(mount_source).resolve()) == requested_source
            requested_blocks_source = str(runtime_blocks_path.resolve()) if runtime_blocks_path is not None else None
            blocks_mount_matches = True if requested_blocks_source is None else (
                blocks_mount_source is not None
                and str(Path(blocks_mount_source).resolve()) == requested_blocks_source
            )

            operation.verification = {
                "state": json.loads(state.stdout) if state.stdout else None,
                "stateVerified": state.returncode == 0,
                "storageBinding": binding.to_dict(),
                "storageLayout": operation.preflight.get("storageLayout"),
                "requestedDataPath": requested_source,
                "runtimeDataMountSource": mount_source,
                "runtimeDataMountMatches": mount_matches,
                "requestedBlocksPath": requested_blocks_source,
                "runtimeBlocksMountSource": blocks_mount_source,
                "runtimeBlocksMountMatches": blocks_mount_matches,
                "verified": state.returncode == 0 and mount_matches and blocks_mount_matches,
            }
            operation.status = InstallStatus.SUCCEEDED if operation.verification["verified"] else InstallStatus.FAILED
            if not mount_matches:
                operation.error = "Runtime /data mount does not match the local runtime storage path."
            elif not blocks_mount_matches:
                operation.error = "Runtime /data/blocks mount does not match the selected advanced storage target."
        except Exception as exc:
            operation.status = InstallStatus.FAILED
            operation.error = str(exc)
        operation.updated_at = utc_now()
        self._save(operation)
        return operation
