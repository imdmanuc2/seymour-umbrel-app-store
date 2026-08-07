from pathlib import Path
repo=Path(__file__).resolve().parents[1]
app=(repo/"seymour-blockchain-manager/data/web/app.py").read_text()
runtime=(repo/"seymour-blockchain-manager/data/web/bch_runtime_probe.py").read_text()
compose=(repo/"seymour-blockchain-manager/docker-compose.yml").read_text()
assert "/api/runtime/bch-rpc" in app
assert "probe_bch_rpc()" in runtime
assert "BCH_RPC_URL:" in compose
assert "BCH_RPC_USER:" in compose
assert "BCH_RPC_PASSWORD:" in compose
print("SBP-021 BCH RPC contract verification: PASS")
