from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any


STATE_DIR = Path(
    os.environ.get(
        "BCH_PROVISIONING_STATE_DIR",
        "/state",
    )
)
PLAN_FILE = STATE_DIR / "provisioning-plan.json"
SECRETS_FILE = STATE_DIR / "rpc-secrets.json"


VALID_MODES = {
    "fresh-sync",
    "copy-existing",
    "restore-backup",
    "remote-rpc",
}


def _required(
    form: dict[str, str],
    field: str,
    label: str,
    errors: list[str],
) -> None:
    if not form.get(field, "").strip():
        errors.append(f"{label} is required.")


def build_plan(form: dict[str, str]) -> dict[str, Any]:
    experience = form.get("experience", "recommended")
    mode = form.get("mode", "fresh-sync")
    errors: list[str] = []

    if experience not in {"recommended", "advanced"}:
        errors.append("Unknown setup experience.")

    if mode not in VALID_MODES:
        errors.append("Unknown provisioning mode.")

    implementation = form.get(
        "implementation",
        "bitcoin-cash-node",
    )
    version_profile = form.get(
        "versionProfile",
        "seymour-recommended",
    )
    specific_version = (
        form.get("specificVersion") or None
    )
    storage_path = form.get(
        "storagePath",
        "/data",
    )
    prune = int(form.get("prune", "0") or "0")
    txindex = (
        form.get("txindex", "1")
        not in {"0", "false", "False"}
    )

    if experience == "recommended":
        implementation = "bitcoin-cash-node"
        version_profile = "seymour-recommended"
        specific_version = None
        storage_path = "/data"
        prune = 0
        txindex = True

    inputs: dict[str, Any] = {}

    if mode == "copy-existing":
        _required(
            form,
            "sourceHost",
            "Source host",
            errors,
        )
        _required(
            form,
            "sourcePath",
            "Source path",
            errors,
        )
        inputs = {
            "sourceHost": form.get("sourceHost"),
            "sourcePath": form.get("sourcePath"),
        }

    elif mode == "restore-backup":
        _required(
            form,
            "backupPath",
            "Backup path",
            errors,
        )
        inputs = {
            "backupPath": form.get("backupPath"),
        }

    elif mode == "remote-rpc":
        for field, label in (
            ("rpcHost", "RPC host"),
            ("rpcPort", "RPC port"),
            ("rpcUser", "RPC user"),
            ("rpcPassword", "RPC password"),
        ):
            _required(
                form,
                field,
                label,
                errors,
            )

        inputs = {
            "rpcHost": form.get("rpcHost"),
            "rpcPort": form.get("rpcPort"),
            "rpcUser": form.get("rpcUser"),
            "rpcPasswordProvided": bool(
                form.get("rpcPassword")
            ),
            "zmqRawBlock": form.get("zmqRawBlock"),
            "zmqRawTx": form.get("zmqRawTx"),
        }

    else:
        inputs = {
            "peerDiscovery": True,
            "validateBlocks": True,
            "minimumFreeBytes": 600_000_000_000,
        }

    if (
        version_profile == "specific"
        and not specific_version
    ):
        errors.append(
            "Specific version is required."
        )

    if prune < 0:
        errors.append(
            "Prune value cannot be negative."
        )

    return {
        "schemaVersion": 2,
        "chain": "bitcoin-cash",
        "network": "mainnet",
        "experience": experience,
        "mode": mode,
        "implementation": implementation,
        "versionProfile": version_profile,
        "specificVersion": specific_version,
        "storagePath": storage_path,
        "runtime": {
            "prune": prune,
            "txindex": txindex,
            "rpcPort": 8332,
            "p2pPort": 8333,
            "zmqRawBlockPort": 28332,
            "zmqRawTxPort": 28333,
        },
        "executable": (
            mode == "fresh-sync"
            and not errors
        ),
        "validation": {
            "valid": not errors,
            "errors": errors,
            "warnings": [
                "SBP-003 executes only the fresh-sync configuration workflow.",
                "The Umbrel app must still be installed to begin synchronization.",
            ],
        },
        "inputs": inputs,
    }


def save_plan(plan: dict[str, Any]) -> dict[str, Any]:
    STATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PLAN_FILE.write_text(
        json.dumps(
            plan,
            indent=2,
        )
        + "\n"
    )

    return plan


def load_plan() -> dict[str, Any] | None:
    if not PLAN_FILE.exists():
        return None

    return json.loads(
        PLAN_FILE.read_text()
    )


def ensure_rpc_secrets() -> dict[str, str]:
    STATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if SECRETS_FILE.exists():
        return json.loads(
            SECRETS_FILE.read_text()
        )

    values = {
        "rpcUser": "seymour_rpc",
        "rpcPassword": secrets.token_urlsafe(32),
    }

    SECRETS_FILE.write_text(
        json.dumps(
            values,
            indent=2,
        )
        + "\n"
    )

    os.chmod(
        SECRETS_FILE,
        0o600,
    )

    return values
