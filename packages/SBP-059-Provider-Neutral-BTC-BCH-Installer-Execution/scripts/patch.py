#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
installer = repo / 'seymour-blockchain-manager/data/web/installer.py'
appjs = repo / 'seymour-blockchain-manager/data/web/app.js'

text = installer.read_text()

# Replace BCH-only constant block.
start = text.find('INSTALL_SCRIPT = Path(')
end = text.find('\nclass InstallStatus', start)
if start < 0 or end < 0:
    raise SystemExit('SBP-059 constants anchor not found')
replacement = '''CONTROL_SCRIPT = Path(os.environ.get(
    "SEYMOUR_UMBREL_CONTROL_SCRIPT",
    "/control/seymour-umbrel-app",
))
EVIDENCE_PATH = Path(os.environ.get(
    "INSTALL_EVIDENCE_PATH",
    "/evidence/installations.jsonl",
))
OPERATIONS_PATH = Path(os.environ.get(
    "INSTALL_OPERATION_DIRECTORY",
    "/evidence/install-operations",
))

PROVIDERS = {
    "bitcoin-mainnet": {
        "appId": os.environ.get("BTC_APP_ID", "seymour-bitcoin-node"),
        "installScript": Path(os.environ.get(
            "SEYMOUR_BTC_INSTALL_SCRIPT",
            "/control/seymour-install-btc",
        )),
        "rpcPrefix": "BTC",
    },
    "bitcoin-cash-mainnet": {
        "appId": os.environ.get("BCH_APP_ID", "seymour-bch-node"),
        "installScript": Path(os.environ.get(
            "SEYMOUR_BCH_INSTALL_SCRIPT",
            "/control/seymour-install-bch",
        )),
        "rpcPrefix": "BCH",
    },
}
'''
text = text[:start] + replacement + text[end:]

# Parameterize provider lookup and preflight.
old = '''def _provider() -> dict[str, Any]:
    catalog = json.loads(CATALOG_PATH.read_text())
    return next(item for item in catalog["providers"] if item["providerId"] == PROVIDER_ID)

def preflight(storage_target_id: str | None = None) -> dict[str, Any]:
    provider = _provider()
'''
new = '''def _provider(provider_id: str) -> dict[str, Any]:
    catalog = json.loads(CATALOG_PATH.read_text())
    return next(
        item for item in catalog["providers"]
        if item["providerId"] == provider_id
    )

def provider_runtime(provider_id: str) -> dict[str, Any]:
    if provider_id not in PROVIDERS:
        raise ValueError("Provider is not enabled for installation.")
    return PROVIDERS[provider_id]

def preflight(
    storage_target_id: str | None = None,
    provider_id: str = "bitcoin-cash-mainnet",
) -> dict[str, Any]:
    provider = _provider(provider_id)
'''
if old not in text:
    raise SystemExit('SBP-059 provider/preflight anchor not found')
text = text.replace(old, new, 1)
text = text.replace(
    '    if not checks["providerSelectable"]: errors.append("Bitcoin Cash is not selectable.")\n'
    '    if not checks["productionImage"]: errors.append("Bitcoin Cash has no production image.")\n',
    '    if not checks["providerSelectable"]: errors.append(f"{provider_id} is not selectable.")\n'
    '    if not checks["productionImage"]: errors.append(f"{provider_id} has no production image.")\n',
    1,
)

# Generalize request validation.
vstart = text.find('def validate_request(value: InstallRequest) -> None:')
vend = text.find('\nclass Installer:', vstart)
if vstart < 0 or vend < 0:
    raise SystemExit('SBP-059 validate anchor not found')
validate = '''def validate_request(value: InstallRequest) -> None:
    runtime = provider_runtime(value.provider_id)
    expected_app_id = runtime["appId"]
    expected_confirmation = f"INSTALL-{expected_app_id}"

    if value.app_id != expected_app_id:
        raise ValueError("App ID does not match the selected provider.")
    if value.confirmation != expected_confirmation:
        raise ValueError("Installation confirmation token did not match.")
    if not value.node_name:
        raise ValueError("Node name is required.")
    if not value.storage_target_id:
        raise ValueError("Storage target is required.")
    if not value.rpc_user:
        raise ValueError("RPC user is required.")
    if len(value.rpc_password) < 24:
        raise ValueError("RPC password must contain at least 24 characters.")
    if not 1 <= value.rpc_port <= 65535 or not 1 <= value.p2p_port <= 65535:
        raise ValueError("Port is invalid.")
'''
text = text[:vstart] + validate + text[vend:]

# Installer no longer owns a fixed BCH script.
old_init = '''class Installer:
    def __init__(self, install_script: Path = INSTALL_SCRIPT, control_script: Path = CONTROL_SCRIPT, evidence_path: Path = EVIDENCE_PATH, operations_path: Path = OPERATIONS_PATH) -> None:
        self.install_script = install_script
        self.control_script = control_script
        self.evidence_path = evidence_path
        self.operations_path = operations_path
'''
new_init = '''class Installer:
    def __init__(
        self,
        control_script: Path = CONTROL_SCRIPT,
        evidence_path: Path = EVIDENCE_PATH,
        operations_path: Path = OPERATIONS_PATH,
    ) -> None:
        self.control_script = control_script
        self.evidence_path = evidence_path
        self.operations_path = operations_path
'''
if old_init not in text:
    raise SystemExit('SBP-059 installer init anchor not found')
text = text.replace(old_init, new_init, 1)

text = text.replace(
    '        checks = preflight(value.storage_target_id)\n',
    '        runtime = provider_runtime(value.provider_id)\n        checks = preflight(value.storage_target_id, value.provider_id)\n',
    1,
)

# Generalize environment and selected installer script.
old_env = '''        env.update({
            "BCH_RPC_USER": value.rpc_user,
            "BCH_RPC_PASSWORD": value.rpc_password,
            "BCH_RPC_PORT": str(value.rpc_port),
            "BCH_P2P_PORT": str(value.p2p_port),
            "SEYMOUR_NODE_NAME": value.node_name,
            "SEYMOUR_BLOCKCHAIN_DATA_PATH": str(data_path),
        })
        try:
            completed = subprocess.run([str(self.install_script), "--execute", "--confirm", CONFIRMATION_TOKEN], capture_output=True, text=True, timeout=900, check=False, env=env)
'''
new_env = '''        prefix = runtime["rpcPrefix"]
        env.update({
            f"{prefix}_RPC_USER": value.rpc_user,
            f"{prefix}_RPC_PASSWORD": value.rpc_password,
            f"{prefix}_RPC_PORT": str(value.rpc_port),
            f"{prefix}_P2P_PORT": str(value.p2p_port),
            "SEYMOUR_NODE_NAME": value.node_name,
            "SEYMOUR_BLOCKCHAIN_DATA_PATH": str(data_path),
        })

        install_script = runtime["installScript"]
        confirmation_token = f"INSTALL-{runtime['appId']}"

        try:
            completed = subprocess.run(
                [
                    str(install_script),
                    "--execute",
                    "--confirm",
                    confirmation_token,
                ],
                capture_output=True,
                text=True,
                timeout=900,
                check=False,
                env=env,
            )
'''
if old_env not in text:
    raise SystemExit('SBP-059 env anchor not found')
text = text.replace(old_env, new_env, 1)

text = text.replace(
    'state = subprocess.run([str(self.control_script), "state", BCH_APP_ID], capture_output=True, text=True, timeout=120, check=False)',
    'state = subprocess.run([str(self.control_script), "state", runtime["appId"]], capture_output=True, text=True, timeout=120, check=False)',
    1,
)
text = text.replace('f"{BCH_APP_ID}_node_1"', 'f"{runtime[\'appId\']}_node_1"', 1)

installer.write_text(text)

# Provider-driven UI labels.
js = appjs.read_text()
js = js.replace('value="Seymour Bitcoin Cash Node"', 'value="Seymour ${provider.displayName} Node"', 1)
js = js.replace('>Install Bitcoin Cash</button>', '>Install ${provider.displayName}</button>', 1)
appjs.write_text(js)

print('SBP-059 provider-neutral BTC/BCH installer patch: PASS')
