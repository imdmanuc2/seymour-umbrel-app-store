from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping

from .engine import AppLifecycleEngine
from .model import LifecycleState

CANONICAL_RUNTIME_STATES = (
    "starting", "syncing", "running", "degraded",
    "stopped", "offline", "error", "unknown",
)

@dataclass(frozen=True)
class RuntimeStateObservation:
    app_id: str
    runtime_state: str
    payload: dict[str, Any]
    source: str

    def as_lifecycle_state(self, engine: AppLifecycleEngine) -> LifecycleState:
        state = self.runtime_state
        if state not in CANONICAL_RUNTIME_STATES:
            state = "unknown"

        running = state in {"starting", "syncing", "running", "degraded"}
        healthy = (
            True if state == "running"
            else False if state in {"degraded", "error"}
            else None
        )
        return LifecycleState(
            app_id=self.app_id,
            state=state,
            installed=True,
            running=running,
            healthy=healthy,
            detail={
                "runtimeState": self.runtime_state,
                "runtimeStateSource": self.source,
                "runtime": self.payload,
            },
        )

class CanonicalRuntimeStateProvider:
    """Read canonical Seymour provider runtime state without re-inferring it."""

    def __init__(
        self,
        *,
        app_urls: Mapping[str, str] | None = None,
        app_probes: Mapping[str, Any] | None = None,
        timeout_seconds: float = 3.0,
    ) -> None:
        if app_urls is None:
            app_urls = {}
            bch_app_id = os.environ.get("BCH_APP_ID", "seymour-bch-node").strip()
            bch_url = os.environ.get("BCH_STATUS_URL", "").strip()
            if bch_app_id and bch_url:
                app_urls[bch_app_id] = bch_url
        self.app_urls = {
            str(app_id).strip(): str(url).strip()
            for app_id, url in app_urls.items()
            if str(app_id).strip() and str(url).strip()
        }
        self.app_probes = dict(app_probes or {})
        self.timeout_seconds = float(timeout_seconds)

    def authoritative_for(self, app_id: str) -> bool:
        return app_id in self.app_urls

    @staticmethod
    def _extract_runtime_state(payload: Any) -> str:
        if not isinstance(payload, dict):
            return "unknown"

        value = payload.get("runtimeState")
        if isinstance(value, str) and value.strip():
            return value.strip().lower()

        for key in ("runtime", "runtimeMetrics", "observedState", "metrics"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                value = nested.get("runtimeState")
                if isinstance(value, str) and value.strip():
                    return value.strip().lower()

        return "unknown"

    def observe(self, app_id: str) -> RuntimeStateObservation | None:
        probe = self.app_probes.get(app_id)
        if probe is not None:
            try:
                raw = probe()
                state_payload = raw.get('operationalState') if isinstance(raw, dict) else None
                state_payload = state_payload if isinstance(state_payload, dict) else {}
                runtime_state = str(state_payload.get('state') or 'unknown').strip().lower()
                if runtime_state not in CANONICAL_RUNTIME_STATES:
                    runtime_state = 'unknown'
                return RuntimeStateObservation(
                    app_id=app_id,
                    runtime_state=runtime_state,
                    payload={
                        'runtimeState': runtime_state,
                        'runtimeStateReason': state_payload.get('reason'),
                        'runtimeRpcReachable': state_payload.get('rpcReachable'),
                        'runtimeRpcHealthy': state_payload.get('rpcHealthy'),
                        'runtimeInitialBlockDownload': state_payload.get('initialBlockDownload'),
                        'runtimeVerificationProgress': state_payload.get('verificationProgress'),
                        'operationalState': state_payload,
                    },
                    source='direct-runtime-probe',
                )
            except Exception as exc:
                return RuntimeStateObservation(
                    app_id=app_id,
                    runtime_state='unknown',
                    payload={'runtimeState': 'unknown', 'error': str(exc)},
                    source='direct-runtime-probe',
                )

        url = self.app_urls.get(app_id)
        if not url:
            return None

        try:
            with urllib.request.urlopen(url, timeout=self.timeout_seconds) as response:
                body = response.read().decode()
            payload = json.loads(body)
            if not isinstance(payload, dict):
                payload = {"raw": payload}
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            json.JSONDecodeError,
            OSError,
        ) as exc:
            payload = {
                "runtimeState": "unknown",
                "runtimeStateReason": "canonical runtime state source unavailable",
                "error": str(exc),
            }

        runtime_state = self._extract_runtime_state(payload)
        if runtime_state not in CANONICAL_RUNTIME_STATES:
            runtime_state = "unknown"

        return RuntimeStateObservation(
            app_id=app_id,
            runtime_state=runtime_state,
            payload=payload,
            source=url,
        )

    def read_state(
        self,
        app_id: str,
        engine: AppLifecycleEngine,
    ) -> LifecycleState | None:
        observation = self.observe(app_id)
        if observation is None:
            return None
        return observation.as_lifecycle_state(engine)
