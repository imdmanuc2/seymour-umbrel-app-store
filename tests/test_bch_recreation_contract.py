from pathlib import Path
repo = Path(__file__).resolve().parents[1]
compose = (repo / "seymour-bch-node" / "docker-compose.yml").read_text()
entrypoint = (repo / "seymour-bch-node" / "data" / "node" / "entrypoint.sh").read_text()
assert "/usr/local/bin/seymour-entrypoint" in compose
assert 'entrypoint: ["/usr/local/bin/seymour-entrypoint"]' in compose
assert "rpcallowip=10.0.0.0/8" in entrypoint
assert "rpcuser=${RPC_USER}" in entrypoint
assert "rpcpassword=${RPC_PASSWORD}" in entrypoint
print("SBP-022 BCH recreation contract verification: PASS")
