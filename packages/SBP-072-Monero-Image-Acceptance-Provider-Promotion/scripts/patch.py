#!/usr/bin/env python3
import json, sys
from pathlib import Path
repo=Path(sys.argv[1])
image="ghcr.io/imdmanuc2/seymour-monero-node:0.18.5.1"
paths=[
 repo/"shared/provider_catalog/providers.v1.json",
 repo/"seymour-blockchain-manager/data/catalog/providers.v1.json",
 repo/"seymour-blockchain-manager/data/shared/provider_catalog/providers.v1.json",
]
for path in paths:
    payload=json.loads(path.read_text())
    providers=payload.get("providers")
    if not isinstance(providers,list):
        raise SystemExit(f"ERROR: providers list missing in {path}")
    xmr=next((p for p in providers if p.get("providerId")=="monero-mainnet"),None)
    if not isinstance(xmr,dict):
        raise SystemExit(f"ERROR: monero-mainnet missing in {path}")
    xmr["productionImage"]=image
    path.write_text(json.dumps(payload,indent=2)+"\n")
print("SBP-072 Monero production image promotion: PASS")
