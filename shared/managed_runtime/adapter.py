from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from .models import ManagedRuntimeObservation

class ManagedRuntimeAdapter(ABC):
    adapter_type: str

    @abstractmethod
    def supports(self, runtime_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def inspect(self, runtime_id: str, *, provider_id: str | None = None,
                display_name: str | None = None) -> ManagedRuntimeObservation:
        raise NotImplementedError

    def logs(self, runtime_id: str, *, tail: int = 200) -> Any:
        raise NotImplementedError("This adapter does not expose logs.")

    def lifecycle(self, runtime_id: str, action: str, *, execute: bool = False,
                  confirmation: str | None = None,
                  correlation_id: str | None = None) -> Any:
        raise NotImplementedError(
            "Lifecycle execution is not configured for this adapter."
        )
