from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .request import InstallRequest


@dataclass(frozen=True)
class TargetInstallPreflight:
    """
    Target-specific readiness returned to the shared install
    orchestrator.

    This contract intentionally contains no Umbrel, Docker,
    SSH, Nexus, or Blockchain Manager implementation detail.
    """

    compatible: bool
    checks: dict[str, Any]
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "compatible": self.compatible,
            "checks": dict(self.checks),
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class TargetInstallExecution:
    """
    Raw target-adapter execution result.

    Provider/platform-specific evidence may be carried inside
    result and evidence while the outer contract remains stable.
    """

    success: bool
    result: Any = None
    evidence: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "evidence": self.evidence,
            "error": self.error,
        }


@dataclass(frozen=True)
class TargetInstallVerification:
    """
    Post-execution verification returned by the target adapter.
    """

    verified: bool
    evidence: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "evidence": self.evidence,
            "error": self.error,
        }


class TargetInstallAdapter(Protocol):
    """
    Bounded host/runtime-specific installation boundary.

    Implementations may use Umbrel-native lifecycle or another
    supported host runtime, but management products never invoke
    platform-specific installation mechanisms directly.
    """

    adapter_type: str

    def preflight(
        self,
        request: InstallRequest,
        provider: dict[str, Any],
    ) -> TargetInstallPreflight:
        ...

    def execute(
        self,
        request: InstallRequest,
        provider: dict[str, Any],
    ) -> TargetInstallExecution:
        ...

    def verify(
        self,
        request: InstallRequest,
        provider: dict[str, Any],
        execution: TargetInstallExecution,
    ) -> TargetInstallVerification:
        ...
