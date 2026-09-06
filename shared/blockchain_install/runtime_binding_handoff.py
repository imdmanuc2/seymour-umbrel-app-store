from __future__ import annotations

import os
import re
from pathlib import Path


RUNTIME_BINDING_FILENAME = "runtime-binding.env"

_APP_ID_RE = re.compile(
    r"^[a-z0-9][a-z0-9._-]*$"
)


def app_runtime_binding_path(
    *,
    data_directory: Path,
    app_id: str,
) -> Path:
    root = Path(data_directory)

    if not root.is_absolute():
        raise ValueError(
            "Umbrel data directory must be absolute."
        )

    identity = str(app_id or "").strip()

    if not _APP_ID_RE.fullmatch(identity):
        raise ValueError(
            "Invalid app id."
        )

    return (
        root
        / "app-data"
        / identity
        / "data"
        / RUNTIME_BINDING_FILENAME
    )


def stage_runtime_binding(
    *,
    binding_path: Path,
    data_directory: Path,
    app_id: str,
) -> dict[str, object]:
    source = Path(binding_path)

    if not source.is_absolute():
        raise ValueError(
            "Runtime binding source must be absolute."
        )

    if not source.is_file():
        raise ValueError(
            "Runtime binding source does not exist."
        )

    target = app_runtime_binding_path(
        data_directory=Path(data_directory),
        app_id=app_id,
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = source.read_bytes()

    temporary = target.with_name(
        f".{target.name}.tmp"
    )

    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

        os.chmod(
            temporary,
            0o600,
        )

        os.replace(
            temporary,
            target,
        )

    finally:
        if temporary.exists():
            temporary.unlink()

    return {
        "appId": app_id,
        "bindingFile": str(target),
        "staged": True,
    }
