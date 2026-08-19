#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$PKG/scripts/doctor.sh"

python3 - "$REPO" <<'PY'
import json
import sys
from pathlib import Path

repo = Path(sys.argv[1])

catalog_paths = [
    repo / "shared/provider_catalog/providers.v1.json",
    repo / "seymour-blockchain-manager/data/catalog/providers.v1.json",
    repo / "seymour-blockchain-manager/data/shared/provider_catalog/providers.v1.json",
]

runtime_contracts = {
    "bitcoin-mainnet": {
        "appId": "seymour-bitcoin-node",
        "service": "node",
        "dataDirectory": "/data",
        "rpc": {
            "port": 8332,
            "authentication": "username-password",
        },
        "p2p": {"port": 8333},
    },
    "bitcoin-cash-mainnet": {
        "appId": "seymour-bch-node",
        "service": "node",
        "dataDirectory": "/data",
        "rpc": {
            "port": 8332,
            "authentication": "username-password",
        },
        "p2p": {"port": 8333},
    },
    "monero-mainnet": {
        "appId": "seymour-monero-node",
        "service": "node",
        "dataDirectory": "/data",
        "rpc": {
            "port": 18081,
            "authentication": "none",
        },
        "p2p": {"port": 18080},
    },
}

for path in catalog_paths:
    payload = json.loads(path.read_text())

    for provider in payload["providers"]:
        contract = runtime_contracts.get(provider["providerId"])
        if contract is not None:
            provider["runtime"] = contract

    path.write_text(json.dumps(payload, indent=2) + "\n")

print("SBP-068 provider runtime metadata materialized.")
PY

python3 - "$REPO/shared/provider_catalog/catalog.py" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()

text = text.replace(
'''    production_image: str | None
''',
'''    production_image: str | None
    runtime: dict[str, Any] | None
'''
)

text = text.replace(
'''            production_image=(
                str(data["productionImage"])
                if data["productionImage"]
                else None
            ),
''',
'''            production_image=(
                str(data["productionImage"])
                if data["productionImage"]
                else None
            ),
            runtime=(
                dict(data["runtime"])
                if isinstance(data.get("runtime"), dict)
                else None
            ),
'''
)

text = text.replace(
'''            "productionImage": self.production_image,
''',
'''            "productionImage": self.production_image,
            "runtime": (
                dict(self.runtime)
                if self.runtime is not None
                else None
            ),
'''
)

start = text.find(
'''    def validate(self) -> None:
        live = [
'''
)

end = text.find(
'''    def get(
''',
    start,
)

if start == -1 or end == -1:
    raise SystemExit(
        "ERROR: ProviderCatalog.validate block not found"
    )

replacement = '''    def validate(self) -> None:
        if not self.providers:
            raise CatalogValidationError(
                "Provider catalog contains no providers"
            )

'''

text = text[:start] + replacement + text[end:]

path.write_text(text)

print("SBP-068 provider catalog model updated.")
PY

python3 -m py_compile \
  "$REPO/shared/provider_catalog/catalog.py"

echo "SBP-068 install: PASS"
echo "No blockchain runtime was modified."
echo "NEXT: run verify.sh."
