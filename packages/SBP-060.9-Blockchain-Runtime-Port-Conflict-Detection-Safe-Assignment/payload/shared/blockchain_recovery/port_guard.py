from __future__ import annotations

import json
import socket
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PortOwner:
    port: int
    protocol: str
    owner: str | None
    container: str | None
    project: str | None
    service: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "port": self.port,
            "protocol": self.protocol,
            "owner": self.owner,
            "container": self.container,
            "project": self.project,
            "service": self.service,
        }


def port_is_free(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", int(port)))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def first_free_port(candidates: list[int]) -> int | None:
    for port in candidates:
        if port_is_free(port):
            return port
    return None


def docker_owner_for_port(port: int) -> PortOwner:
    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{json .}}"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    if result.returncode != 0:
        return PortOwner(port, "tcp", "unknown-listener", None, None, None)

    needle = f":{port}->"

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        try:
            item = json.loads(line)
        except Exception:
            continue

        if needle not in str(item.get("Ports") or ""):
            continue

        labels = str(item.get("Labels") or "")
        project = None
        service = None

        for label in labels.split(","):
            if label.startswith("com.docker.compose.project="):
                project = label.split("=", 1)[1]
            elif label.startswith("com.docker.compose.service="):
                service = label.split("=", 1)[1]

        return PortOwner(
            port=port,
            protocol="tcp",
            owner="docker",
            container=str(item.get("Names") or "") or None,
            project=project,
            service=service,
        )

    return PortOwner(port, "tcp", "non-docker-listener", None, None, None)


def inspect_port_conflict(
    *,
    requested_port: int,
    candidates: list[int],
) -> dict[str, Any]:
    if port_is_free(requested_port):
        return {
            "conflict": False,
            "requestedPort": requested_port,
            "recommendedPort": requested_port,
            "owner": None,
        }

    return {
        "conflict": True,
        "requestedPort": requested_port,
        "recommendedPort": first_free_port(candidates),
        "owner": docker_owner_for_port(requested_port).to_dict(),
    }
