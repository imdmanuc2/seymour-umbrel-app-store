#!/usr/bin/env python3
from __future__ import annotations
import shutil, sys
from pathlib import Path

MARKER = "# SBP-050 — canonical managed runtime registration projection"

def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch_sbp050.py REPO_ROOT", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).resolve()
    pkg = Path(__file__).resolve().parents[1]

    src = pkg / "payload/shared/managed_runtime/registration.py"
    dst = repo / "shared/managed_runtime/registration.py"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    csrc = pkg / "payload/shared/contracts/managed-runtime-registration-v1.json"
    cdst = repo / "shared/contracts/managed-runtime-registration-v1.json"
    shutil.copy2(csrc, cdst)

    init_path = repo / "shared/managed_runtime/__init__.py"
    init_text = init_path.read_text()
    if "attach_managed_runtime_projection" not in init_text:
        init_text += """
from .registration import (
    REGISTRATION_CONTRACT,
    REGISTRATION_VERSION,
    attach_managed_runtime_projection,
    project_asset,
    project_registration_payload,
)

__all__ += [
    "REGISTRATION_CONTRACT",
    "REGISTRATION_VERSION",
    "attach_managed_runtime_projection",
    "project_asset",
    "project_registration_payload",
]
"""
        init_path.write_text(init_text)

    nexus = repo / "seymour-blockchain-manager/data/web/nexus_integration.py"
    text = nexus.read_text()
    if MARKER not in text:
        text += f"""

{MARKER}
from shared.managed_runtime import attach_managed_runtime_projection

_sbp050_registration_payload = registration_payload

def registration_payload(dashboard, sync):
    # Preserve the existing registration identity and delivery/idempotency
    # semantics, then attach the generic SBP-049 runtime projection.
    payload = _sbp050_registration_payload(dashboard, sync)
    return attach_managed_runtime_projection(payload)
"""
        nexus.write_text(text)

    print("SBP-050 canonical managed runtime registration projection installed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
