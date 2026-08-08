from __future__ import annotations

import base64
import json
import os
import socket
from typing import Any
from urllib import error, request


RPC_URL = os.environ.get(
    "BCH_RPC_URL",
    "http://seymour-bch-node_node_1:8332/",
)

RPC_USER = os.environ.get(
    "BCH_RPC_USER",
    "",
)

RPC_PASSWORD = os.environ.get(
    "BCH_RPC_PASSWORD",
    "",
)

RPC_TIMEOUT_SECONDS = max(
    1,
    int(
        os.environ.get(
            "BCH_RPC_TIMEOUT_SECONDS",
            "20",
        )
    ),
)

BCH_NODE_CONTAINER = os.environ.get(
    "BCH_NODE_CONTAINER",
    "seymour-bch-node_node_1",
)

DOCKER_SOCKET = os.environ.get(
    "DOCKER_SOCKET",
    "/var/run/docker.sock",
)


def _decode_chunked(body: bytes) -> bytes:
    output = bytearray()
    position = 0

    while position < len(body):
        line_end = body.find(
            b"\r\n",
            position,
        )

        if line_end == -1:
            break

        size_line = body[
            position:line_end
        ].split(
            b";",
            1,
        )[0]

        try:
            size = int(
                size_line,
                16,
            )
        except ValueError:
            break

        position = line_end + 2

        if size == 0:
            break

        output.extend(
            body[
                position:
                position + size
            ]
        )

        position += size + 2

    return bytes(output)


def _docker_container_environment() -> dict[str, str]:
    try:
        sock = socket.socket(
            socket.AF_UNIX,
            socket.SOCK_STREAM,
        )

        sock.settimeout(3)
        sock.connect(DOCKER_SOCKET)

        endpoint = (
            f"/containers/"
            f"{BCH_NODE_CONTAINER}/json"
        )

        sock.sendall(
            (
                f"GET {endpoint} HTTP/1.1\r\n"
                "Host: docker\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode()
        )

        chunks = []

        while True:
            chunk = sock.recv(65536)

            if not chunk:
                break

            chunks.append(chunk)

        sock.close()

        raw = b"".join(chunks)

        head, _, body = raw.partition(
            b"\r\n\r\n"
        )

        headers = {}

        for line in head.splitlines()[1:]:
            if b":" not in line:
                continue

            key, value = line.split(
                b":",
                1,
            )

            headers[
                key.decode("latin-1")
                .strip()
                .lower()
            ] = (
                value.decode("latin-1")
                .strip()
                .lower()
            )

        if (
            headers.get("transfer-encoding")
            == "chunked"
        ):
            body = _decode_chunked(body)

        payload = json.loads(
            body.decode()
        )

        config = payload.get(
            "Config",
            {},
        )

        environment = {}

        for item in config.get(
            "Env",
            [],
        ):
            if "=" not in item:
                continue

            key, value = item.split(
                "=",
                1,
            )

            environment[key] = value

        return environment

    except Exception:
        return {}


_CACHED_RPC_CREDENTIALS: tuple[str, str] | None = None


def _resolved_credentials() -> tuple[str, str]:
    global _CACHED_RPC_CREDENTIALS

    if RPC_USER and RPC_PASSWORD:
        return (
            RPC_USER,
            RPC_PASSWORD,
        )

    if _CACHED_RPC_CREDENTIALS is not None:
        return _CACHED_RPC_CREDENTIALS

    environment = (
        _docker_container_environment()
    )

    user = (
        RPC_USER
        or environment.get(
            "BCH_RPC_USER",
            "",
        )
    )

    password = (
        RPC_PASSWORD
        or environment.get(
            "BCH_RPC_PASSWORD",
            "",
        )
    )

    # Cache only a valid pair. A temporary Docker
    # socket failure must not permanently cache blanks.
    if user and password:
        _CACHED_RPC_CREDENTIALS = (
            user,
            password,
        )

    return (
        user,
        password,
    )


def _rpc_headers() -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": (
            "Seymour-Blockchain-Manager/1.0"
        ),
    }

    user, password = (
        _resolved_credentials()
    )

    if user or password:
        token = base64.b64encode(
            f"{user}:{password}".encode()
        ).decode()

        headers["Authorization"] = (
            f"Basic {token}"
        )

    return headers


def call_rpc(
    method: str,
    params: list[Any] | None = None,
) -> dict[str, Any]:
    user, password = (
        _resolved_credentials()
    )

    auth_configured = bool(
        user or password
    )

    body = json.dumps({
        "jsonrpc": "1.0",
        "id": f"seymour-{method}",
        "method": method,
        "params": params or [],
    }).encode()

    req = request.Request(
        RPC_URL,
        data=body,
        headers=_rpc_headers(),
        method="POST",
    )

    try:
        with request.urlopen(
            req,
            timeout=RPC_TIMEOUT_SECONDS,
        ) as response:
            payload = json.loads(
                response.read().decode()
            )

            return {
                "reachable": True,
                "httpStatus": int(
                    response.status
                ),
                "result": payload.get(
                    "result"
                ),
                "rpcError": payload.get(
                    "error"
                ),
                "transportError": None,
                "authConfigured": (
                    auth_configured
                ),
                "url": RPC_URL,
            }

    except error.HTTPError as exc:
        raw = ""

        try:
            raw = exc.read().decode()
        except Exception:
            pass

        parsed = None

        if raw:
            try:
                parsed = json.loads(raw)
            except Exception:
                pass

        return {
            "reachable": False,
            "httpStatus": int(
                exc.code
            ),
            "result": None,
            "rpcError": (
                parsed.get("error")
                if isinstance(
                    parsed,
                    dict,
                )
                else None
            ),
            "transportError": (
                f"HTTP {exc.code}: "
                f"{exc.reason}"
            ),
            "authConfigured": (
                auth_configured
            ),
            "url": RPC_URL,
        }

    except Exception as exc:
        return {
            "reachable": False,
            "httpStatus": None,
            "result": None,
            "rpcError": None,
            "transportError": str(exc),
            "authConfigured": (
                auth_configured
            ),
            "url": RPC_URL,
        }


def probe() -> dict[str, Any]:
    # Lightweight RPC liveness check.
    # Do not use getblockchaininfo for liveness because
    # it can be slow while BCHN is in initial block download.
    liveness = call_rpc("uptime")

    if not liveness["reachable"]:
        return {
            "reachable": False,
            "healthy": False,
            "status": "rpc-unreachable",
            "authConfigured": liveness[
                "authConfigured"
            ],
            "httpStatus": liveness[
                "httpStatus"
            ],
            "error": (
                liveness["transportError"]
                or liveness["rpcError"]
            ),
            "rpcUrl": RPC_URL,
            "chain": None,
            "height": None,
            "headers": None,
            "peers": None,
            "progressPercent": None,
            "initialBlockDownload": None,
            "verificationProgress": None,
            "raw": {
                "liveness": liveness,
            },
        }

    # RPC itself is alive. Detailed calls are telemetry,
    # not liveness tests.
    blockchain = call_rpc(
        "getblockchaininfo"
    )

    network = call_rpc(
        "getnetworkinfo"
    )

    network_info = (
        network["result"]
        if isinstance(
            network.get("result"),
            dict,
        )
        else {}
    )

    # BCHN can take a long time to answer getblockchaininfo
    # during IBD. Keep RPC healthy and report the detail
    # request as slow instead of declaring RPC unreachable.
    if not blockchain["reachable"]:
        return {
            "reachable": True,
            "healthy": True,
            "status": "rpc-slow",
            "authConfigured": liveness[
                "authConfigured"
            ],
            "httpStatus": liveness[
                "httpStatus"
            ],
            "error": blockchain[
                "transportError"
            ],
            "rpcUrl": RPC_URL,
            "chain": None,
            "height": None,
            "headers": None,
            "peers": network_info.get(
                "connections"
            ),
            "progressPercent": None,
            "initialBlockDownload": None,
            "verificationProgress": None,
            "raw": {
                "liveness": liveness,
                "blockchain": blockchain,
                "network": network,
            },
        }

    info = (
        blockchain["result"]
        if isinstance(
            blockchain.get("result"),
            dict,
        )
        else {}
    )

    progress = info.get(
        "verificationprogress"
    )

    return {
        "reachable": True,
        "healthy": (
            blockchain.get("rpcError")
            is None
        ),
        "status": (
            "healthy"
            if blockchain.get(
                "rpcError"
            ) is None
            else "rpc-error"
        ),
        "authConfigured": liveness[
            "authConfigured"
        ],
        "httpStatus": blockchain[
            "httpStatus"
        ],
        "error": blockchain.get(
            "rpcError"
        ),
        "rpcUrl": RPC_URL,
        "chain": info.get(
            "chain"
        ),
        "height": info.get(
            "blocks"
        ),
        "headers": info.get(
            "headers"
        ),
        "peers": network_info.get(
            "connections"
        ),
        "progressPercent": (
            float(progress) * 100.0
            if progress is not None
            else None
        ),
        "initialBlockDownload": (
            info.get(
                "initialblockdownload"
            )
        ),
        "verificationProgress": (
            progress
        ),
        "bestBlockHash": info.get(
            "bestblockhash"
        ),
        "difficulty": info.get(
            "difficulty"
        ),
        "raw": {
            "liveness": liveness,
            "blockchain": blockchain,
            "network": network,
        },
    }

