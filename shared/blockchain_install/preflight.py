from __future__ import annotations
from typing import Any
from .models import CapacityPolicy, HostProfile, InstallPreflight, StorageTarget

DEFAULT_RESERVE_RATIO = 0.20
DEFAULT_MINIMUM_RESERVE_BYTES = 50_000_000_000

def capacity_policy(
    estimated_bytes: int,
    *,
    reserve_ratio: float = DEFAULT_RESERVE_RATIO,
    minimum_reserve_bytes: int = DEFAULT_MINIMUM_RESERVE_BYTES,
) -> CapacityPolicy:
    estimated = max(int(estimated_bytes), 0)
    reserve = max(int(estimated * float(reserve_ratio)), int(minimum_reserve_bytes))
    return CapacityPolicy(estimated, reserve, estimated + reserve)

def evaluate(
    *,
    provider: dict[str, Any],
    host: HostProfile,
    storage_target: StorageTarget,
    require_umbrel: bool = True,
    reserve_ratio: float = DEFAULT_RESERVE_RATIO,
    minimum_reserve_bytes: int = DEFAULT_MINIMUM_RESERVE_BYTES,
) -> InstallPreflight:
    provider_id = str(provider.get("providerId","")).strip()
    arches = tuple(str(x) for x in provider.get("supportedArchitectures",[]))
    policy = capacity_policy(
        int(provider.get("estimatedDiskBytes",0)),
        reserve_ratio=reserve_ratio,
        minimum_reserve_bytes=minimum_reserve_bytes,
    )
    checks = {
        "providerIdPresent": bool(provider_id),
        "architecture": host.architecture,
        "architectureSupported": host.architecture in arches,
        "cpuCount": host.cpu_count,
        "memoryTotalBytes": host.memory_total_bytes,
        "dockerAvailable": host.docker_available,
        "umbrelAvailable": host.umbrel_available,
        "storageReachable": storage_target.reachable,
        "storageWritable": storage_target.writable,
        "storagePersistent": storage_target.persistent,
        "storageFreeBytes": storage_target.free_bytes,
        "storageRequiredBytes": policy.required_bytes,
        "storageCapacityHealthy": storage_target.free_bytes >= policy.required_bytes,
    }
    errors, warnings = [], []
    if not checks["providerIdPresent"]: errors.append("Provider ID is missing.")
    if not checks["architectureSupported"]: errors.append(f"Host architecture {host.architecture} is not supported.")
    if not checks["dockerAvailable"]: errors.append("Docker is unavailable.")
    if require_umbrel and not checks["umbrelAvailable"]: errors.append("Umbrel runtime is unavailable.")
    if not checks["storageReachable"]: errors.append("Selected storage target is unreachable.")
    if not checks["storageWritable"]: errors.append("Selected storage target is not writable.")
    if not checks["storagePersistent"]: errors.append("Selected storage target is not persistent.")
    if not checks["storageCapacityHealthy"]: errors.append("Selected storage target does not have enough free capacity.")
    if host.cpu_count <= 0: warnings.append("CPU count could not be measured.")
    if host.memory_total_bytes <= 0: warnings.append("Memory capacity could not be measured.")
    return InstallPreflight(
        provider_id=provider_id,
        compatible=not errors,
        host=host.to_dict(),
        storage_target=storage_target.to_dict(),
        capacity=policy.to_dict(),
        checks=checks,
        errors=errors,
        warnings=warnings,
    )
