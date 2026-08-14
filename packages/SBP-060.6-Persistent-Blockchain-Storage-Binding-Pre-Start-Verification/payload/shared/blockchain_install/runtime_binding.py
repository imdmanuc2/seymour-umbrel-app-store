from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class RuntimeBindingPlan:
    provider_id: str
    app_id: str
    data_path: Path
    compose_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "providerId": self.provider_id,
            "appId": self.app_id,
            "dataPath": str(self.data_path),
            "composePath": str(self.compose_path),
        }

def persist_runtime_binding(*, provider_id: str, app_id: str,
                            compose_path: Path, data_path: Path) -> RuntimeBindingPlan:
    text = compose_path.read_text()
    node_candidates = (
        "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data",
        "${SEYMOUR_BLOCKCHAIN_DATA_PATH}:/data",
    )
    changed = False
    for candidate in node_candidates:
        if candidate in text:
            text = text.replace(candidate, f"{data_path}:/data", 1)
            changed = True
            break

    for candidate in (
        "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data",
        "${SEYMOUR_BLOCKCHAIN_DATA_PATH}:/node-data",
    ):
        if candidate in text:
            text = text.replace(candidate, f"{data_path}:/node-data", 1)
            break

    if not changed and f"{data_path}:/data" not in text:
        raise RuntimeError("runtime-data-volume-anchor-not-found")

    compose_path.write_text(text)
    return RuntimeBindingPlan(provider_id, app_id, data_path, compose_path)

def verify_live_data_mount(*, inspect_mounts: list[dict[str, Any]],
                           expected_data_path: Path) -> dict[str, Any]:
    expected = str(expected_data_path.resolve())
    actual = next(
        (m.get("Source") for m in inspect_mounts if m.get("Destination") == "/data"),
        None,
    )
    try:
        matches = bool(actual) and str(Path(actual).resolve()) == expected
    except Exception:
        matches = actual == expected

    return {
        "expectedDataPath": expected,
        "actualDataPath": actual,
        "matches": matches,
        "healthy": bool(matches),
        "error": None if matches else "storage-binding-mismatch",
    }
