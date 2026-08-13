from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any

from .models import StorageTarget


SAFE_COMPONENT = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def provider_storage_name(provider_id: str) -> str:
    value = str(provider_id).strip().lower()
    if not value or not SAFE_COMPONENT.fullmatch(value):
        raise ValueError(f"Unsafe provider storage name: {provider_id!r}")
    return value


@dataclass(frozen=True)
class StorageBindingPlan:
    provider_id: str
    runtime_host: str
    storage_target_id: str
    storage_type: str
    storage_host: str
    storage_root: str
    data_path: str
    source: str | None
    filesystem: str
    remote_host: str | None
    reachable: bool
    writable: bool
    persistent: bool
    eligible: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["errors"] = list(self.errors)
        return data


def build_binding_plan(
    *,
    provider_id: str,
    runtime_host: str,
    storage_target: StorageTarget,
    data_root_name: str = "seymour-data",
) -> StorageBindingPlan:
    provider_name = provider_storage_name(provider_id)
    root_name = str(data_root_name).strip()

    if not SAFE_COMPONENT.fullmatch(root_name):
        raise ValueError(f"Unsafe data root name: {data_root_name!r}")

    storage_root = Path(storage_target.path) / root_name
    data_path = storage_root / provider_name

    errors: list[str] = []

    if not storage_target.reachable:
        errors.append("Selected storage target is unreachable.")
    if not storage_target.persistent:
        errors.append("Selected storage target is not persistent.")
    if not storage_target.writable:
        errors.append("Selected storage target is not writable.")

    return StorageBindingPlan(
        provider_id=provider_name,
        runtime_host=str(runtime_host).strip(),
        storage_target_id=storage_target.target_id,
        storage_type=storage_target.target_type.value,
        storage_host=storage_target.host,
        storage_root=str(storage_root),
        data_path=str(data_path),
        source=storage_target.source,
        filesystem=storage_target.filesystem,
        remote_host=storage_target.remote_host,
        reachable=storage_target.reachable,
        writable=storage_target.writable,
        persistent=storage_target.persistent,
        eligible=not errors,
        errors=tuple(errors),
    )
