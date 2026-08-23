from __future__ import annotations

from pathlib import Path

from .runtime_binding import (
    load_runtime_binding,
)
from .runtime_binding_materializer import (
    materialize_runtime_binding,
)


def reconcile_installed_runtime_binding(
    *,
    data_directory: Path,
    binding_path: Path,
) -> dict[str, object]:
    binding = load_runtime_binding(
        binding_path
    )

    compose_path = (
        data_directory
        / "app-data"
        / binding.app_id
        / "docker-compose.yml"
    )

    result = materialize_runtime_binding(
        compose_path=compose_path,
        binding=binding,
    )

    return {
        "providerId": binding.provider_id,
        "appId": binding.app_id,
        "bindingPath": str(binding_path),
        **result,
    }
