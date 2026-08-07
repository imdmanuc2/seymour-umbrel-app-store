from pathlib import Path
p=Path("seymour-blockchain-manager/data/web/app.py"); t=p.read_text()
imp="from bch_runtime_probe import probe as probe_bch_runtime\n"
if imp not in t:
 a="from telemetry import dashboard_payload\n"
 if a not in t: raise SystemExit("telemetry import anchor missing")
 t=t.replace(a,a+imp,1)
route='        if self.path == "/api/runtime/bch-health":\n            self.send_json(probe_bch_runtime())\n            return\n\n'
if "/api/runtime/bch-health" not in t:
 a='        if self.path == "/api/nexus/scheduler/status":\n'
 if a not in t: a='        if self.path == "/api/nexus/delivery/status":\n'
 if a not in t: raise SystemExit("GET route anchor missing")
 t=t.replace(a,route+a,1)
p.write_text(t); print("BCH runtime health API added.")
