from __future__ import annotations

VALID_MODES = {
    "fresh-sync",
    "copy-existing",
    "restore-backup",
    "remote-rpc",
}

def build_plan(form: dict[str, str]) -> dict:
    experience = form.get("experience", "recommended")
    mode = form.get("mode", "fresh-sync")
    errors: list[str] = []

    if experience not in {"recommended", "advanced"}:
        errors.append("Unknown setup experience.")
    if mode not in VALID_MODES:
        errors.append("Unknown provisioning mode.")

    implementation = form.get("implementation", "bitcoin-cash-node")
    version_profile = form.get("versionProfile", "seymour-recommended")
    specific_version = form.get("specificVersion") or None
    storage_path = form.get("storagePath", "/data")

    if experience == "recommended":
        implementation = "bitcoin-cash-node"
        version_profile = "seymour-recommended"
        specific_version = None
        storage_path = "/data"

    inputs: dict = {}

    def required(field: str, label: str) -> None:
        value = form.get(field, "").strip()
        if not value:
            errors.append(f"{label} is required.")

    if mode == "copy-existing":
        required("sourceHost", "Source host")
        required("sourcePath", "Source path")
        inputs = {
            "sourceHost": form.get("sourceHost"),
            "sourcePath": form.get("sourcePath"),
        }
    elif mode == "restore-backup":
        required("backupPath", "Backup path")
        inputs = {"backupPath": form.get("backupPath")}
    elif mode == "remote-rpc":
        for field, label in (
            ("rpcHost", "RPC host"),
            ("rpcPort", "RPC port"),
            ("rpcUser", "RPC user"),
            ("rpcPassword", "RPC password"),
        ):
            required(field, label)
        inputs = {
            "rpcHost": form.get("rpcHost"),
            "rpcPort": form.get("rpcPort"),
            "rpcUser": form.get("rpcUser"),
            "rpcPasswordProvided": bool(form.get("rpcPassword")),
            "zmqRawBlock": form.get("zmqRawBlock"),
            "zmqRawTx": form.get("zmqRawTx"),
        }
    else:
        inputs = {
            "peerDiscovery": True,
            "validateBlocks": True,
        }

    if version_profile == "specific" and not specific_version:
        errors.append("Specific version is required.")

    return {
        "schemaVersion": 1,
        "chain": "bitcoin-cash",
        "network": "mainnet",
        "experience": experience,
        "mode": mode,
        "implementation": implementation,
        "versionProfile": version_profile,
        "specificVersion": specific_version,
        "storagePath": storage_path,
        "executable": False,
        "validation": {
            "valid": not errors,
            "errors": errors,
            "warnings": [
                "SBP-002 creates a plan only.",
                "No blockchain or host changes will be made.",
            ],
        },
        "inputs": inputs,
    }
