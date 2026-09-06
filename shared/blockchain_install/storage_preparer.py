from __future__ import annotations

from pathlib import Path

from .runtime_binding import (
    RuntimeBinding,
    RuntimeBindingMode,
)


def prepare_runtime_storage(
    binding: RuntimeBinding,
) -> dict[str, object]:
    """
    Materialize the target-local directories required by a validated
    blockchain runtime binding.

    This primitive does not mount storage, modify host persistence,
    change ownership, invoke Docker, or perform lifecycle operations.
    """
    binding.validate()

    prepared: list[str] = []

    if binding.mode == RuntimeBindingMode.SINGLE_PATH:
        assert binding.data_path is not None

        path = Path(binding.data_path)
        path.mkdir(
            parents=True,
            exist_ok=True,
        )
        prepared.append(str(path))

    elif binding.mode == RuntimeBindingMode.HYBRID_BLOCKS:
        assert binding.blocks_path is not None

        path = Path(binding.blocks_path)
        path.mkdir(
            parents=True,
            exist_ok=True,
        )
        prepared.append(str(path))

    else:
        raise ValueError(
            "unsupported runtime binding mode: "
            f"{binding.mode}"
        )

    return {
        "providerId": binding.provider_id,
        "appId": binding.app_id,
        "mode": binding.mode.value,
        "preparedPaths": prepared,
    }
