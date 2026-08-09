from pathlib import Path

path = Path("seymour-blockchain-manager/data/web/nexus_integration.py")
text = path.read_text()

if 'telemetry["runtimeState"]' in text:
    print("Nexus runtime-state metric projection already wired.")
    raise SystemExit(0)

marker = (
    '        telemetry["operationalState"] = runtime.get("operationalState")\n'
    '        telemetry["rpc"] = runtime["rpc"]\n'
    '        asset["operationalState"] = runtime.get("operationalState")\n'
    '        asset["status"] = runtime["lifecycleStatus"]\n'
)

replacement = (
    '        telemetry["operationalState"] = runtime.get("operationalState")\n'
    '\n'
    '        operational_state = (\n'
    '            runtime.get("operationalState")\n'
    '            if isinstance(runtime.get("operationalState"), dict)\n'
    '            else {}\n'
    '        )\n'
    '\n'
    '        telemetry["operationalStateName"] = operational_state.get("state")\n'
    '        telemetry["runtimeState"] = operational_state.get("state")\n'
    '        telemetry["runtimeStateReason"] = operational_state.get("reason")\n'
    '        telemetry["runtimeRpcReachable"] = operational_state.get("rpcReachable")\n'
    '        telemetry["runtimeRpcHealthy"] = operational_state.get("rpcHealthy")\n'
    '        telemetry["runtimeInitialBlockDownload"] = operational_state.get("initialBlockDownload")\n'
    '        telemetry["runtimeVerificationProgress"] = operational_state.get("verificationProgress")\n'
    '\n'
    '        telemetry["rpc"] = runtime["rpc"]\n'
    '        asset["operationalState"] = runtime.get("operationalState")\n'
    '        asset["runtimeState"] = operational_state.get("state")\n'
    '        asset["status"] = runtime["lifecycleStatus"]\n'
)

if marker not in text:
    raise SystemExit(
        "Could not locate SBP-025 Nexus operational-state projection."
    )

path.write_text(text.replace(marker, replacement, 1))
print("Nexus CMDB runtime-state metric projection wired.")
