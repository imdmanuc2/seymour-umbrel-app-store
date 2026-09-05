from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .request import InstallRequest


@dataclass(frozen=True)
class InstallResult:
    """
    Provider-neutral result returned by a Seymour blockchain
    installation execution service.

    The shared contract intentionally contains no Umbrel, Docker,
    HTTP, SSH, Nexus, or Blockchain Manager implementation details.
    """

    operation_id: str
    status: str
    result: Any = None
    verification: Any = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "succeeded"

    def to_dict(self) -> dict[str, Any]:
        return {
            "operationId": self.operation_id,
            "status": self.status,
            "result": self.result,
            "verification": self.verification,
            "error": self.error,
        }


class InstallExecutor(Protocol):
    """
    Shared execution boundary.

    Implementations may use Umbrel-native lifecycle, another supported
    host runtime adapter, or future platform-specific mechanisms.
    Management products consume this interface rather than each other.
    """

    def execute(
        self,
        request: InstallRequest,
    ) -> InstallResult:
        ...
