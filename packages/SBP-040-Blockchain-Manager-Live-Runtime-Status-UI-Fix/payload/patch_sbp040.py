from pathlib import Path
import sys

root = Path(sys.argv[1])
telemetry = root / "seymour-blockchain-manager/data/web/telemetry.py"
compose = root / "seymour-blockchain-manager/docker-compose.yml"
runtime_probe = root / "seymour-blockchain-manager/data/web/bch_runtime_probe.py"

s = telemetry.read_text()

if "from bch_runtime_probe import probe as probe_bch_runtime" not in s:
    anchor = "from urllib import request\n"
    if anchor not in s:
        raise SystemExit("SBP-040 patch: telemetry import anchor missing")
    s = s.replace(anchor, anchor + "from bch_runtime_probe import probe as probe_bch_runtime\n", 1)

start = s.find("def bch_telemetry() -> dict[str, Any]:")
end = s.find("\n\ndef dashboard_payload()", start)
if start < 0 or end < 0:
    raise SystemExit("SBP-040 patch: bch_telemetry anchors missing")

replacement = '''def bch_telemetry() -> dict[str, Any]:
    # Project the canonical BCH runtime probe into the dashboard contract.
    runtime = probe_bch_runtime()

    operational_state = (
        runtime.get("operationalState")
        if isinstance(runtime.get("operationalState"), dict)
        else {}
    )
    rpc = runtime.get("rpc") if isinstance(runtime.get("rpc"), dict) else {}
    rpc_probe = rpc.get("probe") if isinstance(rpc.get("probe"), dict) else {}
    legacy_status = rpc.get("status") if isinstance(rpc.get("status"), dict) else {}
    legacy_payload = (
        legacy_status.get("payload")
        if isinstance(legacy_status.get("payload"), dict)
        else {}
    )

    runtime_state = operational_state.get("state") or runtime.get("lifecycleStatus") or "unknown"

    progress = rpc_probe.get("progressPercent")
    if progress is None:
        verification = operational_state.get("verificationProgress")
        if isinstance(verification, (int, float)):
            progress = float(verification) * 100.0

    sync = {
        "height": rpc_probe.get("height"),
        "headers": rpc_probe.get("headers"),
        "progressPercent": progress,
        "initialBlockDownload": (
            rpc_probe.get("initialBlockDownload")
            if rpc_probe.get("initialBlockDownload") is not None
            else operational_state.get("initialBlockDownload")
        ),
    }

    storage = legacy_payload.get("storage") if isinstance(legacy_payload.get("storage"), dict) else {}
    used_bytes = storage.get("usedBytes")
    if used_bytes is None:
        used_bytes = directory_size(BCH_DATA_PATH)

    rpc_reachable = bool(
        operational_state.get("rpcReachable")
        if operational_state.get("rpcReachable") is not None
        else rpc_probe.get("reachable")
    )
    rpc_healthy = bool(
        operational_state.get("rpcHealthy")
        if operational_state.get("rpcHealthy") is not None
        else rpc_probe.get("healthy")
    )

    return {
        "providerId": "bitcoin-cash-mainnet",
        "appId": runtime.get("appId", BCH_APP_ID),
        "installed": bool(runtime.get("installed")),
        "running": bool(runtime.get("running")),
        "lifecycleStatus": runtime_state,
        "runtimeState": runtime_state,
        "runtimeStateReason": operational_state.get("reason"),
        "runtimeRpcReachable": rpc_reachable,
        "runtimeRpcHealthy": rpc_healthy,
        "runtimeInitialBlockDownload": sync["initialBlockDownload"],
        "runtimeVerificationProgress": operational_state.get("verificationProgress"),
        "operationalState": operational_state,
        "container": runtime.get("container", {}),
        "rpc": {
            "reachable": rpc_reachable,
            "healthy": rpc_healthy,
            "probe": rpc_probe,
        },
        "sync": sync,
        "peers": rpc_probe.get("peers"),
        "mempool": None,
        "data": {
            "path": str(BCH_DATA_PATH),
            "usedBytes": used_bytes,
        },
    }
'''

s = s[:start] + replacement + s[end:]
telemetry.write_text(s)

for path in (compose, runtime_probe, telemetry):
    text = path.read_text()
    text = text.replace("http://seymour-bch-node_status_1:8080/api/health", "http://status:8080/api/health")
    text = text.replace("http://seymour-bch-node_status_1:8080/api/status", "http://status:8080/api/status")
    path.write_text(text)
