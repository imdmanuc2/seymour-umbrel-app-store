from __future__ import annotations
import os, platform, shutil, socket, subprocess
from pathlib import Path
from .models import HostProfile

def normalized_architecture(machine: str | None = None) -> str:
    value = (machine or platform.machine()).strip().lower()
    if value in {"x86_64", "amd64"}:
        return "amd64"
    if value in {"aarch64", "arm64"}:
        return "arm64"
    return value

def memory_total_bytes(meminfo_path: Path = Path("/proc/meminfo")) -> int:
    try:
        for line in meminfo_path.read_text().splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024
    except Exception:
        pass
    return 0

def docker_available() -> bool:
    docker = shutil.which("docker")
    if not docker:
        return False
    try:
        r = subprocess.run(
            [docker, "version", "--format", "{{.Server.Version}}"],
            capture_output=True, text=True, timeout=4, check=False
        )
        return r.returncode == 0
    except Exception:
        return False

def umbrel_available(
    data_directory: Path = Path("/home/umbrel/umbrel"),
    daemon_root: Path = Path("/opt/umbreld"),
) -> bool:
    return data_directory.is_dir() and daemon_root.is_dir() and (data_directory/"app-data").is_dir()

def profile(
    *,
    data_directory: Path = Path("/home/umbrel/umbrel"),
    daemon_root: Path = Path("/opt/umbreld"),
) -> HostProfile:
    return HostProfile(
        hostname=socket.gethostname(),
        architecture=normalized_architecture(),
        cpu_count=os.cpu_count() or 0,
        memory_total_bytes=memory_total_bytes(),
        docker_available=docker_available(),
        umbrel_available=umbrel_available(data_directory, daemon_root),
    )
