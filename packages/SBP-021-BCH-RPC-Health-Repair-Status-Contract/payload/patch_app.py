from pathlib import Path
p=Path("seymour-blockchain-manager/data/web/app.py")
t=p.read_text()
imp="from bch_rpc_probe import probe as probe_bch_rpc\n"
if imp not in t:
    anchor="from bch_runtime_probe import probe as probe_bch_runtime\n"
    if anchor not in t: raise SystemExit("Could not locate BCH runtime import.")
    t=t.replace(anchor,anchor+imp,1)
route='''        if self.path == "/api/runtime/bch-rpc":\n            self.send_json(probe_bch_rpc())\n            return\n\n'''
anchor='        if self.path == "/api/runtime/bch-health":\n'
if "/api/runtime/bch-rpc" not in t:
    if anchor not in t: raise SystemExit("Could not locate BCH health route.")
    t=t.replace(anchor,route+anchor,1)
p.write_text(t)
print("BCH direct RPC diagnostics API added.")
