from __future__ import annotations

from pathlib import Path

from .runtime_binding import (
    RuntimeBinding,
    RuntimeBindingMode,
)


def materialize_runtime_binding(
    *,
    compose_path: Path,
    binding: RuntimeBinding,
) -> dict[str, object]:
    binding.validate()

    if not compose_path.is_file():
        raise FileNotFoundError(
            f"compose file not found: {compose_path}"
        )

    text = compose_path.read_text()
    original = text

    if binding.mode == RuntimeBindingMode.SINGLE_PATH:
        assert binding.data_path is not None

        text, resolved = _materialize_single_path(
            text=text,
            data_path=binding.data_path,
        )

        expected = 2

    elif binding.mode == RuntimeBindingMode.HYBRID_BLOCKS:
        assert binding.local_data_path is not None
        assert binding.blocks_path is not None

        text, resolved = _materialize_hybrid_blocks(
            text=text,
            local_data_path=binding.local_data_path,
            blocks_path=binding.blocks_path,
        )

        expected = 4

    else:
        raise ValueError(
            f"unsupported runtime binding mode: "
            f"{binding.mode}"
        )

    if resolved != expected:
        raise RuntimeError(
            "runtime storage materialization incomplete: "
            f"expected {expected} anchors, "
            f"resolved {resolved}"
        )

    changed = text != original

    if changed:
        compose_path.write_text(text)

    return {
        "providerId": binding.provider_id,
        "appId": binding.app_id,
        "mode": binding.mode.value,
        "composePath": str(compose_path),
        "anchorsResolved": resolved,
        "anchorsExpected": expected,
        "changed": changed,
    }


def _materialize_single_path(
    *,
    text: str,
    data_path: Path,
) -> tuple[str, int]:
    value = str(data_path)

    replacements = (
        (
            "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-"
            "${APP_DATA_DIR}/data/node}:/data",
            f"{value}:/data",
        ),
        (
            "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-"
            "${APP_DATA_DIR}/data/node}:/node-data",
            f"{value}:/node-data",
        ),
    )

    return _apply_replacements(
        text=text,
        replacements=replacements,
    )


def _materialize_hybrid_blocks(
    *,
    text: str,
    local_data_path: Path,
    blocks_path: Path,
) -> tuple[str, int]:
    local = str(local_data_path)
    blocks = str(blocks_path)

    replacements = (
        (
            "${SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH:-"
            "${APP_DATA_DIR}/data/node}:/data",
            f"{local}:/data",
        ),
        (
            "${SEYMOUR_BLOCKCHAIN_BLOCKS_PATH:-"
            "${APP_DATA_DIR}/data/node/blocks}:/data/blocks",
            f"{blocks}:/data/blocks",
        ),
        (
            "${SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH:-"
            "${APP_DATA_DIR}/data/node}:/node-data",
            f"{local}:/node-data",
        ),
        (
            "${SEYMOUR_BLOCKCHAIN_BLOCKS_PATH:-"
            "${APP_DATA_DIR}/data/node/blocks}:"
            "/node-data/blocks",
            f"{blocks}:/node-data/blocks",
        ),
    )

    return _apply_replacements(
        text=text,
        replacements=replacements,
    )


def _apply_replacements(
    *,
    text: str,
    replacements: tuple[tuple[str, str], ...],
) -> tuple[str, int]:
    resolved = 0

    for source, target in replacements:
        if source in text:
            text = text.replace(
                source,
                target,
                1,
            )
            resolved += 1

        elif target in text:
            resolved += 1

    return text, resolved
