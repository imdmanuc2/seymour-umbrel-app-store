from pathlib import Path
p=Path("seymour-blockchain-manager/docker-compose.yml"); t=p.read_text()
a='      NEXUS_DELIVERY_STATUS_PATH: /evidence/nexus-delivery-status.json\n'
add=a+'      NEXUS_REFRESH_ENABLED: "true"\n      NEXUS_REFRESH_INTERVAL_SECONDS: "60"\n      NEXUS_REFRESH_INITIAL_DELAY_SECONDS: "15"\n      NEXUS_REFRESH_STATE_PATH: /evidence/nexus-refresh-state.json\n'
if 'NEXUS_REFRESH_ENABLED' not in t:
    if a not in t: raise SystemExit("Could not locate Nexus delivery status environment")
    t=t.replace(a,add,1)
p.write_text(t); print("Nexus scheduler environment added.")
