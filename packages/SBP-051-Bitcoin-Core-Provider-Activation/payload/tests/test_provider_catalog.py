from pathlib import Path

from shared.provider_catalog import (
    CatalogValidationError,
    ProviderCatalog,
)


repo = Path(__file__).resolve().parents[1]

catalog = ProviderCatalog.load(
    repo
    / "shared"
    / "provider_catalog"
    / "providers.v1.json"
)

assert catalog.schema_version == 1
assert catalog.catalog_version == "1.0.0"
assert catalog.release == "SBR-v1.0"
assert catalog.frozen is True
assert len(catalog.providers) == 9

provider_ids = {
    provider.provider_id
    for provider in catalog.providers
}

assert provider_ids == {
    "bitcoin-mainnet",
    "bitcoin-cash-mainnet",
    "litecoin-mainnet",
    "dogecoin-mainnet",
    "dash-mainnet",
    "zcash-mainnet",
    "monero-mainnet",
    "kaspa-mainnet",
    "ergo-mainnet",
}

selectable = catalog.selectable()
assert len(selectable) == 2
assert {
    provider.provider_id
    for provider in selectable
} == {
    "bitcoin-mainnet",
    "bitcoin-cash-mainnet",
}

bch = catalog.validate_install_selection(
    "bitcoin-cash-mainnet",
    "arm64",
)

assert bch.production_image == (
    "ghcr.io/imdmanuc2/"
    "seymour-bitcoin-cash-node:29.1.0"
)

btc = catalog.validate_install_selection(
    "bitcoin-mainnet",
    "arm64",
)

assert btc.production_image == (
    "ghcr.io/imdmanuc2/"
    "seymour-bitcoin-node:29.0.0"
)

payload = catalog.api_payload()
assert payload["providerCount"] == 9
assert payload["liveProviderCount"] == 2
assert len(payload["providers"]) == 9

print(
    "SBP-007 provider catalog contract "
    "verification: PASS"
)
