from __future__ import annotations
import json
import subprocess
from pathlib import Path
from .runtime_binding import verify_live_data_mount

def docker_mounts(container_name: str) -> list[dict]:
    result = subprocess.run(
        ["docker","inspect",container_name,"--format","{{json .Mounts}}"],
        capture_output=True, text=True, timeout=10, check=False
    )
    if result.returncode != 0:
        return []
    try:
        value = json.loads(result.stdout.strip())
        return value if isinstance(value, list) else []
    except Exception:
        return []

def verify_pre_start_binding(*, container_name: str,
                             expected_data_path: Path) -> dict:
    return verify_live_data_mount(
        inspect_mounts=docker_mounts(container_name),
        expected_data_path=expected_data_path,
    )
