from pathlib import Path

p=Path("seymour-blockchain-manager/data/web/nexus_integration.py"); t=p.read_text()
imp="from bch_runtime_probe import probe as probe_bch_runtime\n"
if imp not in t:
 a="from __future__ import annotations\n"
 if a not in t: raise SystemExit("future import anchor missing")
 t=t.replace(a,a+"\n"+imp,1)
if "_sbp020_registration_payload" not in t:
 t += '\n\n# SBP-020 runtime normalization\n_sbp020_registration_payload = registration_payload\n\ndef registration_payload(dashboard, sync):\n    payload = _sbp020_registration_payload(dashboard, sync)\n    runtime = probe_bch_runtime()\n    document = payload.get("document") if isinstance(payload, dict) else None\n    assets = document.get("assets") if isinstance(document, dict) else None\n    if not isinstance(assets, list):\n        return payload\n    for asset in assets:\n        if not isinstance(asset, dict) or asset.get("providerId") != "bitcoin-cash-mainnet":\n            continue\n        telemetry = asset.get("telemetry")\n        if not isinstance(telemetry, dict):\n            telemetry = {}\n            asset["telemetry"] = telemetry\n        telemetry["installed"] = runtime["installed"]\n        telemetry["running"] = runtime["running"]\n        telemetry["container"] = runtime["container"]\n        telemetry["lifecycleStatus"] = runtime["lifecycleStatus"]\n        telemetry["rpc"] = runtime["rpc"]\n        asset["status"] = runtime["lifecycleStatus"]\n    return payload\n'
p.write_text(t); print("BCH runtime normalization added to Nexus payload.")
