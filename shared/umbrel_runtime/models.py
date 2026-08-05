from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ContainerState:
    name: str
    service: str | None
    status: str
    running: bool
    healthy: bool | None
    image: str | None
    started_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AppRuntimeState:
    app_id: str
    installed: bool
    source_available: bool
    version: str | None
    lifecycle_status: str
    containers: list[ContainerState] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    missing_dependencies: list[str] = field(default_factory=list)
    health: dict[str, Any] = field(default_factory=dict)
    paths: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "containers": [
                container.to_dict()
                for container in self.containers
            ],
        }
