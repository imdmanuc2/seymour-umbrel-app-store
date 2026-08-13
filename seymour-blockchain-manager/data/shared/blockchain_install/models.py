from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

class StorageTargetType(StrEnum):
    LOCAL = "local"
    ATTACHED = "attached"
    REMOTE = "remote"

@dataclass(frozen=True)
class HostProfile:
    hostname: str
    architecture: str
    cpu_count: int
    memory_total_bytes: int
    docker_available: bool
    umbrel_available: bool
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class StorageTarget:
    target_id: str
    target_type: StorageTargetType
    host: str
    path: str
    filesystem: str
    source: str | None
    total_bytes: int
    used_bytes: int
    free_bytes: int
    writable: bool
    persistent: bool
    reachable: bool
    mount_point: str | None = None
    remote_host: str | None = None
    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["type"] = self.target_type.value
        del data["target_type"]
        return data

@dataclass(frozen=True)
class CapacityPolicy:
    estimated_bytes: int
    reserve_bytes: int
    required_bytes: int
    def to_dict(self) -> dict[str, int]:
        return asdict(self)

@dataclass(frozen=True)
class InstallPreflight:
    provider_id: str
    compatible: bool
    host: dict[str, Any]
    storage_target: dict[str, Any]
    capacity: dict[str, Any]
    checks: dict[str, Any]
    errors: list[str]
    warnings: list[str]
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
