from __future__ import annotations
from .adapter import ManagedRuntimeAdapter

class ManagedRuntimeAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, ManagedRuntimeAdapter] = {}

    def register(self, adapter: ManagedRuntimeAdapter, *, replace: bool = False) -> None:
        key = str(adapter.adapter_type).strip().lower()
        if not key:
            raise ValueError("adapter_type is required.")
        if key in self._adapters and not replace:
            raise ValueError(f"Adapter already registered: {key}")
        self._adapters[key] = adapter

    def resolve(self, adapter_type: str) -> ManagedRuntimeAdapter:
        key = str(adapter_type).strip().lower()
        if key not in self._adapters:
            raise KeyError(f"Managed runtime adapter not registered: {key}")
        return self._adapters[key]

    def types(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))
