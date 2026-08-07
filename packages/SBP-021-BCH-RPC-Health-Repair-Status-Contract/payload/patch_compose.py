from pathlib import Path
p=Path("seymour-blockchain-manager/docker-compose.yml")
t=p.read_text()
anchor='      BCH_STATUS_URL: http://seymour-bch-node_status_1:8080/api/status\n'
add=anchor+'      BCH_RPC_URL: ${BCH_RPC_URL:-http://seymour-bch-node_node_1:8332/}\n      BCH_RPC_USER: ${BCH_RPC_USER:-}\n      BCH_RPC_PASSWORD: ${BCH_RPC_PASSWORD:-}\n      BCH_RPC_TIMEOUT_SECONDS: "5"\n'
if "BCH_RPC_URL:" not in t:
    if anchor not in t: raise SystemExit("Could not locate BCH status URL.")
    t=t.replace(anchor,add,1)
p.write_text(t)
print("BCH RPC environment contract added.")
