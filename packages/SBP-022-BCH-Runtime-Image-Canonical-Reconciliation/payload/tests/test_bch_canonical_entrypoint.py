from pathlib import Path
repo = Path(__file__).resolve().parents[1]
entrypoint = (repo / "seymour-bch-node" / "data" / "node" / "entrypoint.sh").read_text()
assert "rpcbind=0.0.0.0" in entrypoint
assert "rpcallowip=10.0.0.0/8" in entrypoint
assert "rpcallowip=172.16.0.0/12" in entrypoint
assert "rpcallowip=192.168.0.0/16" in entrypoint
assert "rpcuser=${RPC_USER}" in entrypoint
assert "rpcpassword=${RPC_PASSWORD}" in entrypoint
print("SBP-022 canonical BCH entrypoint verification: PASS")
