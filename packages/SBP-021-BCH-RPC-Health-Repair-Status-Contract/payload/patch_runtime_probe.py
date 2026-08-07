from pathlib import Path
p=Path("seymour-blockchain-manager/data/web/bch_runtime_probe.py")
t=p.read_text()
imp="from bch_rpc_probe import probe as probe_bch_rpc\n"
if imp not in t:
    anchor="from urllib.parse import quote\n"
    if anchor not in t: raise SystemExit("Could not locate urllib import anchor.")
    t=t.replace(anchor,anchor+imp,1)
start=t.find("def probe()->dict[str,Any]:")
if start==-1: raise SystemExit("Could not locate BCH runtime probe().")
replacement='''def probe()->dict[str,Any]:\n container=docker_container_inspect()\n legacy_health=http_json(BCH_HEALTH_URL)\n legacy_status=http_json(BCH_STATUS_URL)\n rpc_probe=probe_bch_rpc()\n installed=bool(container.get("found")); running=bool(container.get("running"))\n rpc=bool(rpc_probe.get("reachable") and rpc_probe.get("healthy"))\n lifecycle="not-installed" if not installed else "stopped" if not running else "running" if rpc else "degraded"\n return {"providerId":"bitcoin-cash-mainnet","appId":"seymour-bch-node","installed":installed,"running":running,"lifecycleStatus":lifecycle,"container":container,"rpc":{"reachable":rpc,"probe":rpc_probe,"health":legacy_health,"status":legacy_status}}\n'''
t=t[:start]+replacement
p.write_text(t)
print("BCH runtime probe wired to direct RPC diagnostics.")
