from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Mapping

from bch_runtime_probe import probe as probe_bch_runtime


class LifecycleHttpUnavailable(RuntimeError):
    pass


class LifecycleHttpAdapter:
    """HTTP-facing adapter over the canonical SBP-035 lifecycle facade.

    This module owns no lifecycle state machine or execution implementation.
    The canonical shared lifecycle stack is imported lazily so Blockchain
    Manager can still start and serve non-lifecycle routes if the native
    lifecycle transport is temporarily unavailable.
    """

    def __init__(self, facade: Any | None = None) -> None:
        self._facade = facade

    @staticmethod
    def _platform_root() -> Path:
        return Path(os.environ.get("SEYMOUR_PLATFORM_ROOT", "/seymour-platform"))

    def _build_facade(self) -> Any:
        platform_root = self._platform_root()
        root_text = str(platform_root)
        if root_text not in sys.path:
            sys.path.insert(0, root_text)

        try:
            from shared.app_lifecycle import (
                AppLifecycleEngine,
                CanonicalRuntimeStateProvider,
                LifecycleApiFacade,
                LifecycleAuditRecorder,
                LifecycleAuditStore,
                LifecycleExecutor,
                LifecycleOperationService,
            )
            from shared.umbrel_control import UmbrelAppControlBridge
        except Exception as exc:
            raise LifecycleHttpUnavailable(
                f"Canonical lifecycle modules are unavailable: {exc}"
            ) from exc

        shared_root = platform_root / "shared"
        helper_path = Path(
            os.environ.get(
                "SEYMOUR_UMBREL_NATIVE_HELPER",
                str(shared_root / "umbrel_control" / "native-client.ts"),
            )
        )
        data_directory = Path(
            os.environ.get("SEYMOUR_UMBREL_DATA_DIRECTORY", "/home/umbrel/umbrel")
        )
        endpoint = os.environ.get("SEYMOUR_UMBREL_ENDPOINT", "ws://localhost/trpc")
        evidence_directory = Path(
            os.environ.get(
                "SEYMOUR_LIFECYCLE_NATIVE_EVIDENCE_PATH",
                "/evidence/native-app-control",
            )
        )
        audit_path = Path(
            os.environ.get(
                "SEYMOUR_LIFECYCLE_AUDIT_PATH",
                "/evidence/lifecycle-audit.jsonl",
            )
        )

        bridge = UmbrelAppControlBridge(
            helper_path=helper_path,
            data_directory=data_directory,
            endpoint=endpoint,
            evidence_directory=evidence_directory,
        )
        bch_app_id = os.environ.get('BCH_APP_ID', 'seymour-bch-node')
        state_provider = CanonicalRuntimeStateProvider(
            app_urls={},
            app_probes={bch_app_id: probe_bch_runtime},
            timeout_seconds=3.0,
        )
        executor = LifecycleExecutor(
            bridge,
            AppLifecycleEngine(),
            state_provider=state_provider,
        )
        audit = LifecycleAuditRecorder(LifecycleAuditStore(audit_path))
        operations = LifecycleOperationService(executor, audit_recorder=audit)
        return LifecycleApiFacade(operations)

    @property
    def facade(self) -> Any:
        if self._facade is None:
            self._facade = self._build_facade()
        return self._facade

    def operation(self, payload: Mapping[str, Any]) -> tuple[dict[str, Any], int]:
        try:
            result = self.facade.operation(payload)
            return result, int(self.facade.http_status(result))
        except ValueError as exc:
            return {
                "contract": "seymour.lifecycle-api-error",
                "version": "1.0",
                "error": "invalid-lifecycle-request",
                "message": str(exc),
            }, 400
        except LifecycleHttpUnavailable as exc:
            return {
                "contract": "seymour.lifecycle-api-error",
                "version": "1.0",
                "error": "lifecycle-backend-unavailable",
                "message": str(exc),
            }, 503
        except Exception as exc:
            return {
                "contract": "seymour.lifecycle-api-error",
                "version": "1.0",
                "error": "lifecycle-operation-failure",
                "message": str(exc),
            }, 502

    def history(self, query: Mapping[str, Any]) -> tuple[dict[str, Any], int]:
        try:
            return self.facade.history(query), 200
        except LifecycleHttpUnavailable as exc:
            return {
                "contract": "seymour.lifecycle-api-error",
                "version": "1.0",
                "error": "lifecycle-backend-unavailable",
                "message": str(exc),
            }, 503
        except Exception as exc:
            return {
                "contract": "seymour.lifecycle-api-error",
                "version": "1.0",
                "error": "lifecycle-history-failure",
                "message": str(exc),
            }, 502

    def legacy_operation(
        self,
        action: str,
        payload: Mapping[str, Any],
    ) -> tuple[dict[str, Any], int]:
        """Compatibility bridge for the pre-SBP-036 `/api/lifecycle/<action>` route."""
        canonical = dict(payload)
        canonical["action"] = str(action).strip().lower()
        # The legacy route represented an execute endpoint. Canonical execution
        # still requires the exact confirmation token; no confirmation means the
        # request fails closed and returns that expected token to the caller.
        canonical["execute"] = True
        return self.operation(canonical)


LIFECYCLE_HTTP = LifecycleHttpAdapter()
