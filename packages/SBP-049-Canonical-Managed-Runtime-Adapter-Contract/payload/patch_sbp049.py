#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
package = Path(__file__).resolve().parents[1]
payload = package / "payload"

dst = repo / "shared" / "managed_runtime"
dst.mkdir(parents=True, exist_ok=True)
for src in (payload / "shared" / "managed_runtime").iterdir():
    if src.is_file():
        shutil.copy2(src, dst / src.name)

contracts = repo / "shared" / "contracts"
shutil.copy2(
    payload / "shared" / "contracts" / "managed-runtime-adapter-v1.json",
    contracts / "managed-runtime-adapter-v1.json",
)

path = contracts / "app-lifecycle-v1.json"
data = json.loads(path.read_text())
order = [
    "not-installed", "installing", "stopped", "starting", "syncing", "running",
    "restarting", "updating", "uninstalling", "degraded", "offline", "error", "unknown"
]
existing = set(data.get("states") or [])
existing.update({"syncing", "offline"})
data["states"] = [x for x in order if x in existing]
path.write_text(json.dumps(data, indent=2) + "\n")
print("SBP-049 managed runtime adapter contract installed")
