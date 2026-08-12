from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass(frozen=True)
class ManagedRuntimeIdentity:
    runtime_id: str
    runtime_type: str
    provider_id: str | None = None
    display_name: str | None = None
    version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtimeId": self.runtime_id,
            "runtimeType": self.runtime_type,
            "providerId": self.provider_id,
            "displayName": self.display_name,
            "version": self.version,
        }

@dataclass(frozen=True)
class ManagedRuntimeCapabilities:
    inspect: bool = True
    telemetry: bool = True
    logs: bool = True
    install: bool = False
    start: bool = False
    stop: bool = False
    restart: bool = False
    update: bool = False
    uninstall: bool = False

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)

@dataclass(frozen=True)
class ManagedRuntimeObservation:
    identity: ManagedRuntimeIdentity
    state: dict[str, Any]
    capabilities: ManagedRuntimeCapabilities
    telemetry: dict[str, Any] = field(default_factory=dict)
    native: dict[str, Any] = field(default_factory=dict)

    CONTRACT = "seymour.managed-runtime"
    VERSION = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.CONTRACT,
            "version": self.VERSION,
            "identity": self.identity.to_dict(),
            "state": dict(self.state),
            "capabilities": self.capabilities.to_dict(),
            "telemetry": dict(self.telemetry),
            "native": dict(self.native),
        }
