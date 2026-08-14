#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BRIDGE = ROOT / "shared" / "umbrel_control" / "bridge.py"
text = BRIDGE.read_text()

import_block = '''from shared.blockchain_install.start_guard import (
    resolve_storage_expectation,
    verify_expected_path,
    wait_for_live_binding,
)
'''

if import_block not in text:
    anchor = "from uuid import uuid4\n"
    if anchor not in text:
        raise SystemExit("SBP-060.7 import anchor not found")
    text = text.replace(anchor, anchor + "\n" + import_block, 1)

old = '''        operation.mode = "execute"

        try:
            operation.result = self._invoke(
                action,
                app_id,
            )
            operation.executed = True
            operation.success = True
'''

new = '''        operation.mode = "execute"

        storage_expectation = None
        storage_preflight = None

        if app_id is not None and action in {"start", "restart"}:
            try:
                storage_expectation = resolve_storage_expectation(
                    data_directory=self.data_directory,
                    app_id=app_id,
                )
                if storage_expectation is not None:
                    storage_preflight = verify_expected_path(
                        storage_expectation
                    )
                    if not storage_preflight.get("healthy"):
                        raise RuntimeError(
                            "Blockchain storage pre-start guard blocked "
                            f"{app_id}: {storage_preflight}"
                        )
            except Exception as exc:
                operation.executed = False
                operation.success = False
                operation.error = str(exc)
                operation.result = {
                    "storageGuard": {
                        "phase": "pre-start",
                        "preflight": storage_preflight,
                    }
                }
                self.write_evidence(operation)
                return operation

        try:
            operation.result = self._invoke(
                action,
                app_id,
            )
            operation.executed = True
            operation.success = True

            if (
                storage_expectation is not None
                and app_id is not None
                and action in {"start", "restart"}
            ):
                live_binding = wait_for_live_binding(
                    expectation=storage_expectation,
                )
                if not live_binding.get("healthy"):
                    stop_result = None
                    stop_error = None
                    try:
                        stop_result = self._invoke("stop", app_id)
                    except Exception as stop_exc:
                        stop_error = str(stop_exc)

                    operation.success = False
                    operation.error = (
                        "Blockchain storage post-start guard failed "
                        f"for {app_id}: {live_binding}"
                    )
                    operation.result = {
                        "nativeResult": operation.result,
                        "storageGuard": {
                            "phase": "post-start",
                            "preflight": storage_preflight,
                            "liveBinding": live_binding,
                            "protectiveStop": {
                                "attempted": True,
                                "result": stop_result,
                                "error": stop_error,
                            },
                        },
                    }
                else:
                    operation.result = {
                        "nativeResult": operation.result,
                        "storageGuard": {
                            "phase": "verified",
                            "preflight": storage_preflight,
                            "liveBinding": live_binding,
                        },
                    }
'''

if old not in text:
    raise SystemExit("SBP-060.7 execute anchor not found")

BRIDGE.write_text(text.replace(old, new, 1))
print("SBP-060.7 runtime start storage guard integration: PASS")
