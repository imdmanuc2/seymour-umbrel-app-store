#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BRIDGE = ROOT / "shared" / "umbrel_control" / "bridge.py"

text = BRIDGE.read_text()

import_block = '''from shared.blockchain_install.start_guard import (
    resolve_storage_expectation,
    verify_expected_path,
)
'''

# Remove an older 060.7 import form if present.
text = text.replace(
'''from shared.blockchain_install.start_guard import (
    resolve_storage_expectation,
    verify_expected_path,
    wait_for_live_binding,
)
''',
import_block,
)

if import_block not in text:
    anchor = "from uuid import uuid4\n"

    if anchor not in text:
        raise SystemExit(
            "SBP-060.7 bridge import anchor not found"
        )

    text = text.replace(
        anchor,
        anchor + "\n" + import_block,
        1,
    )

# If the pre-start guard is already installed, do not duplicate it.
if "storage_expectation = None" not in text:
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

        if (
            app_id is not None
            and action in {"start", "restart"}
        ):
            try:
                storage_expectation = (
                    resolve_storage_expectation(
                        data_directory=self.data_directory,
                        app_id=app_id,
                    )
                )

                if storage_expectation is not None:
                    storage_preflight = (
                        verify_expected_path(
                            storage_expectation
                        )
                    )

                    if not storage_preflight.get(
                        "healthy"
                    ):
                        raise RuntimeError(
                            "Blockchain storage pre-start "
                            f"guard blocked {app_id}: "
                            f"{storage_preflight}"
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

            if storage_expectation is not None:
                operation.result = {
                    "nativeResult": operation.result,
                    "storageGuard": {
                        "phase": "pre-start-verified",
                        "preflight": storage_preflight,
                        "postStartInspection": (
                            "delegated-to-privileged-runtime-observer"
                        ),
                    },
                }
'''

    if old not in text:
        raise SystemExit(
            "SBP-060.7 execute anchor not found"
        )

    text = text.replace(old, new, 1)

BRIDGE.write_text(text)

print(
    "SBP-060.7 secure pre-start storage "
    "guard integration: PASS"
)
