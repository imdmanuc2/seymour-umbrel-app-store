from pathlib import Path

from shared.provider_catalog import ProviderCatalog


repo = Path(__file__).resolve().parents[1]

catalog = ProviderCatalog.load(
    repo
    / "shared"
    / "provider_catalog"
    / "providers.v1.json"
)

bch = catalog.get("bitcoin-cash-mainnet")

assert bch.availability == "live"
assert bch.selectable is True
assert bch.node_version == "29.1.0"
assert bch.default_ports["rpc"] == 8332
assert bch.default_ports["p2p"] == 8333
assert bch.supported_architectures == (
    "amd64",
    "arm64",
)
assert bch.production_image == (
    "ghcr.io/imdmanuc2/"
    "seymour-bitcoin-cash-node:29.1.0"
)

compose = (
    repo / "seymour-bch-node" / "docker-compose.yml"
).read_text()

assert bch.production_image in compose

manifest = (
    repo / "seymour-bch-node" / "umbrel-app.yml"
).read_text()

assert 'version: "0.2.3-alpha"' in manifest

print(
    "SBP-007 BCH catalog compatibility "
    "verification: PASS"
)
