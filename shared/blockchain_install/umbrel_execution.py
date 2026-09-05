from __future__ import annotations

import json
import os
import socket
import subprocess
from pathlib import Path
from typing import Mapping, Sequence

from .umbrel_target import UmbrelCommandResult


def script_available(path: Path) -> bool:
    value = Path(path)
    return (
        value.is_file()
        and os.access(value, os.X_OK)
    )


def run_guarded_command(
    argv: Sequence[str],
    environment: Mapping[str, str],
    timeout_seconds: int,
) -> UmbrelCommandResult:
    command = tuple(str(value) for value in argv)

    if not command:
        return UmbrelCommandResult(
            return_code=2,
            stdout="",
            stderr="Command argv is empty.",
        )

    executable = Path(command[0])

    if not script_available(executable):
        return UmbrelCommandResult(
            return_code=127,
            stdout="",
            stderr=f"Executable is unavailable: {executable}",
        )

    env = os.environ.copy()
    env.update(
        {
            str(key): str(value)
            for key, value in environment.items()
        }
    )

    try:
        completed = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=int(timeout_seconds),
            check=False,
            env=env,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        return UmbrelCommandResult(
            return_code=124,
            stdout=str(exc.stdout or ""),
            stderr=(
                str(exc.stderr or "")
                or f"Command timed out after {timeout_seconds}s."
            ),
        )
    except Exception as exc:
        return UmbrelCommandResult(
            return_code=1,
            stdout="",
            stderr=str(exc),
        )

    return UmbrelCommandResult(
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _decode_chunked(body: bytes) -> bytes:
    decoded = bytearray()
    position = 0

    while True:
        line_end = body.find(b"\r\n", position)

        if line_end < 0:
            raise ValueError(
                "Invalid chunked Docker response."
            )

        size_text = body[
            position:line_end
        ].split(b";", 1)[0].strip()

        try:
            size = int(size_text, 16)
        except ValueError as exc:
            raise ValueError(
                "Invalid Docker chunk size."
            ) from exc

        position = line_end + 2

        if size == 0:
            return bytes(decoded)

        chunk_end = position + size

        if chunk_end > len(body):
            raise ValueError(
                "Truncated Docker chunk."
            )

        decoded.extend(body[position:chunk_end])
        position = chunk_end

        if body[position:position + 2] != b"\r\n":
            raise ValueError(
                "Invalid Docker chunk terminator."
            )

        position += 2


def inspect_container_mounts(
    container_name: str,
    *,
    socket_path: Path | None = None,
    timeout_seconds: int = 10,
) -> list[dict]:
    name = str(container_name).strip()

    if not name:
        raise ValueError(
            "Container name is required."
        )

    docker_socket = (
        Path(socket_path)
        if socket_path is not None
        else Path(
            os.environ.get(
                "DOCKER_SOCKET",
                "/var/run/docker.sock",
            )
        )
    )

    client = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
    )

    try:
        client.settimeout(timeout_seconds)
        client.connect(str(docker_socket))

        request = (
            f"GET /containers/{name}/json HTTP/1.1\r\n"
            "Host: docker\r\n"
            "Connection: close\r\n"
            "\r\n"
        )

        client.sendall(request.encode())

        chunks: list[bytes] = []

        while True:
            chunk = client.recv(65536)

            if not chunk:
                break

            chunks.append(chunk)

    finally:
        client.close()

    raw = b"".join(chunks)

    if b"\r\n\r\n" not in raw:
        raise RuntimeError(
            "Docker API returned an invalid response."
        )

    header, body = raw.split(b"\r\n\r\n", 1)

    status_line = (
        header.splitlines()[0]
        .decode(errors="replace")
    )

    if " 200 " not in status_line:
        raise RuntimeError(
            "Docker API container inspection failed: "
            + status_line
        )

    if b"transfer-encoding: chunked" in header.lower():
        body = _decode_chunked(body)

    payload = json.loads(body.decode())
    mounts = payload.get("Mounts", [])

    return mounts if isinstance(mounts, list) else []
