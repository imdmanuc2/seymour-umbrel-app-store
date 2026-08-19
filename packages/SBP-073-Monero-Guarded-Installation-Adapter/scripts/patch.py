from pathlib import Path
import json
import sys


root = Path(sys.argv[1])

installer = (
    root
    / "seymour-blockchain-manager"
    / "data"
    / "web"
    / "installer.py"
)

text = installer.read_text()

anchor = '''    "bitcoin-cash-mainnet": {
        "appId": os.environ.get("BCH_APP_ID", "seymour-bch-node"),
        "installScript": Path(os.environ.get(
            "SEYMOUR_BCH_INSTALL_SCRIPT",
            "/control/seymour-install-bch",
        )),
        "rpcPrefix": "BCH",
    },
'''

monero = '''    "monero-mainnet": {
        "appId": os.environ.get("XMR_APP_ID", "seymour-monero-node"),
        "installScript": Path(os.environ.get(
            "SEYMOUR_XMR_INSTALL_SCRIPT",
            "/control/seymour-install-monero",
        )),
        "rpcPrefix": "XMR",
    },
'''

if '"monero-mainnet": {' not in text:
    if anchor not in text:
        raise SystemExit("INSTALL_ADAPTERS anchor not found")
    text = text.replace(anchor, anchor + monero, 1)

installer.write_text(text)


for relative in (
    "shared/provider_catalog/providers.v1.json",
    "seymour-blockchain-manager/data/catalog/providers.v1.json",
    "seymour-blockchain-manager/data/shared/provider_catalog/providers.v1.json",
):
    path = root / relative
    payload = json.loads(path.read_text())

    provider = next(
        p for p in payload["providers"]
        if p["providerId"] == "monero-mainnet"
    )

    provider["availability"] = "available"
    provider["selectable"] = True

    path.write_text(
        json.dumps(payload, indent=2) + "\n"
    )
