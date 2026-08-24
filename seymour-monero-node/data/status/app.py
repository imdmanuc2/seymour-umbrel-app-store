from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import socket
import threading
import time
import urllib.request
from pathlib import Path


RPC_HOST = os.environ.get("XMR_RPC_HOST", "node")
RPC_PORT = int(os.environ.get("XMR_RPC_PORT", "18081"))
DATA_PATH = Path(os.environ.get("XMR_DATA_PATH", "/node-data"))

RPC_TIMEOUT = float(
    os.environ.get(
        "XMR_RPC_TIMEOUT_SECONDS",
        "120",
    )
)

REFRESH_INTERVAL = float(
    os.environ.get(
        "XMR_TELEMETRY_REFRESH_INTERVAL_SECONDS",
        "15",
    )
)

STALE_AFTER = float(
    os.environ.get(
        "XMR_TELEMETRY_STALE_AFTER_SECONDS",
        "180",
    )
)


_lock = threading.Lock()
_snapshot = None
_last_error = None
_last_attempt = None


def rpc(method: str) -> dict:
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": "seymour",
            "method": method,
        }
    ).encode()

    req = urllib.request.Request(
        f"http://{RPC_HOST}:{RPC_PORT}/json_rpc",
        data=body,
        headers={
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(
        req,
        timeout=RPC_TIMEOUT,
    ) as response:
        payload = json.loads(
            response.read().decode()
        )

    result = payload.get("result")

    if not isinstance(result, dict):
        raise RuntimeError(
            "invalid-monero-rpc-payload"
        )

    return result


def storage() -> dict:
    stat = os.statvfs(DATA_PATH)

    total = (
        stat.f_blocks
        * stat.f_frsize
    )

    free = (
        stat.f_bavail
        * stat.f_frsize
    )

    return {
        "path": str(DATA_PATH),
        "totalBytes": total,
        "filesystemUsedBytes": total - free,
        "freeBytes": free,
        "healthy": True,
    }


def tcp_reachable() -> tuple[bool, str | None]:
    try:
        with socket.create_connection(
            (RPC_HOST, RPC_PORT),
            timeout=2.0,
        ):
            pass

        return True, None

    except Exception as exc:
        return False, str(exc)


def build_snapshot(info: dict) -> dict:
    height = info.get("height")
    target_height = info.get(
        "target_height"
    )

    synchronized = bool(
        info.get("synchronized")
    )

    progress = None

    if (
        isinstance(height, int)
        and isinstance(target_height, int)
        and target_height > 0
    ):
        progress = min(
            max(
                height / target_height,
                0.0,
            ),
            1.0,
        )

    return {
        "measuredAt": time.time(),
        "height": height,
        "targetHeight": target_height,
        "verificationProgress": progress,
        "synchronized": synchronized,
        "peers": {
            "incoming": info.get(
                "incoming_connections_count"
            ),
            "outgoing": info.get(
                "outgoing_connections_count"
            ),
        },
        "nettype": info.get("nettype"),
        "version": info.get("version"),
        "databaseSizeBytes": info.get(
            "database_size"
        ),
    }


def refresh_once() -> None:
    global _snapshot
    global _last_error
    global _last_attempt

    attempt = time.time()

    with _lock:
        _last_attempt = attempt

    try:
        info = rpc("get_info")

        snapshot = build_snapshot(info)

        with _lock:
            _snapshot = snapshot
            _last_error = None

    except Exception as exc:
        with _lock:
            _last_error = str(exc)


def worker() -> None:
    while True:
        started = time.monotonic()

        refresh_once()

        elapsed = (
            time.monotonic()
            - started
        )

        time.sleep(
            max(
                REFRESH_INTERVAL - elapsed,
                1.0,
            )
        )


def status_payload() -> dict:
    reachable, reach_error = (
        tcp_reachable()
    )

    with _lock:
        snap = (
            dict(_snapshot)
            if isinstance(
                _snapshot,
                dict,
            )
            else None
        )

        telemetry_error = _last_error
        last_attempt = _last_attempt

    age = None

    if snap:
        age = max(
            time.time()
            - float(
                snap["measuredAt"]
            ),
            0.0,
        )

    fresh = bool(
        reachable
        and snap
        and age is not None
        and age <= STALE_AFTER
    )

    stale = bool(
        snap
        and not fresh
    )

    if not reachable:
        runtime_state = "degraded"

        reason = (
            reach_error
            or "Monero RPC port is unreachable."
        )

    elif not snap:
        runtime_state = "starting"

        reason = (
            "Monero RPC is reachable; "
            "telemetry snapshot is initializing."
        )

    elif snap.get("synchronized"):
        runtime_state = "running"

        if fresh:
            reason = (
                "Monero daemon is synchronized."
            )
        else:
            reason = (
                "Monero daemon is synchronized; "
                "RPC telemetry is temporarily stale."
            )

    else:
        runtime_state = "syncing"

        if fresh:
            reason = (
                "Monero daemon synchronization "
                "is in progress."
            )
        else:
            reason = (
                "Monero daemon is syncing; "
                "RPC telemetry is temporarily stale."
            )

    verification = (
        snap.get(
            "verificationProgress"
        )
        if snap
        else None
    )

    synchronized = (
        snap.get("synchronized")
        if snap
        else None
    )

    return {
        "healthy": bool(reachable),
        "status": (
            "online"
            if reachable
            else "degraded"
        ),
        "chain": "monero",
        "providerId": "monero-mainnet",
        "runtimeState": runtime_state,
        "runtimeStateReason": reason,
        "runtimeRpcReachable": bool(
            reachable
        ),
        "runtimeRpcHealthy": bool(
            reachable
        ),
        "runtimeInitialBlockDownload": (
            None
            if synchronized is None
            else not synchronized
        ),
        "runtimeVerificationProgress": (
            verification
        ),
        "height": (
            snap.get("height")
            if snap
            else None
        ),
        "targetHeight": (
            snap.get("targetHeight")
            if snap
            else None
        ),
        "verificationProgress": (
            verification
        ),
        "synchronized": synchronized,
        "peers": (
            snap.get("peers")
            if snap
            else None
        ),
        "nettype": (
            snap.get("nettype")
            if snap
            else None
        ),
        "version": (
            snap.get("version")
            if snap
            else None
        ),
        "databaseSizeBytes": (
            snap.get(
                "databaseSizeBytes"
            )
            if snap
            else None
        ),
        "telemetryFresh": fresh,
        "telemetryStale": stale,
        "telemetryAgeSeconds": (
            round(age, 3)
            if age is not None
            else None
        ),
        "telemetrySource": (
            "live-cache"
            if snap
            else "initializing"
        ),
        "telemetryLastAttemptAt": (
            last_attempt
        ),
        "telemetryError": (
            telemetry_error
        ),
        "storage": storage(),
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(
        self,
        payload: dict,
    ) -> None:
        body = json.dumps(
            payload,
            indent=2,
        ).encode()

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "application/json",
        )

        self.send_header(
            "Content-Length",
            str(len(body)),
        )

        self.end_headers()

        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def do_GET(self) -> None:
        if self.path in {
            "/",
            "/api/status",
        }:
            self.send_json(
                status_payload()
            )
            return

        if self.path == "/api/health":
            payload = status_payload()

            self.send_json(
                {
                    "healthy": payload[
                        "healthy"
                    ],
                    "status": payload[
                        "status"
                    ],
                    "runtimeState": payload[
                        "runtimeState"
                    ],
                    "runtimeRpcReachable": (
                        payload[
                            "runtimeRpcReachable"
                        ]
                    ),
                    "telemetryFresh": payload[
                        "telemetryFresh"
                    ],
                    "telemetryStale": payload[
                        "telemetryStale"
                    ],
                    "storage": payload[
                        "storage"
                    ],
                }
            )
            return

        self.send_error(404)

    def log_message(
        self,
        format: str,
        *args,
    ) -> None:
        return


def main() -> None:
    threading.Thread(
        target=worker,
        daemon=True,
        name="xmr-telemetry-refresh",
    ).start()

    ThreadingHTTPServer(
        ("0.0.0.0", 8080),
        Handler,
    ).serve_forever()


if __name__ == "__main__":
    main()
