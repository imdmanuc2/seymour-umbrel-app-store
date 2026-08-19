#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

if "INSTALL_ADAPTERS = {" not in text:
    text = text.replace("PROVIDERS = {\n", "INSTALL_ADAPTERS = {\n", 1)

anchor = 'def _provider(provider_id: str) -> dict[str, Any]:\n    catalog = json.loads(CATALOG_PATH.read_text())\n    return next(\n        item for item in catalog["providers"]\n        if item["providerId"] == provider_id\n    )\n\n'
helpers = 'def _provider(provider_id: str) -> dict[str, Any]:\n    catalog = json.loads(CATALOG_PATH.read_text())\n    return next(\n        item for item in catalog["providers"]\n        if item["providerId"] == provider_id\n    )\n\ndef _runtime_contract(provider: dict[str, Any]) -> dict[str, Any]:\n    runtime = provider.get("runtime")\n    if not isinstance(runtime, dict):\n        raise ValueError("Provider runtime contract is missing.")\n    return runtime\n\n\ndef _rpc_contract(provider: dict[str, Any]) -> dict[str, Any]:\n    rpc = _runtime_contract(provider).get("rpc")\n    if not isinstance(rpc, dict):\n        raise ValueError("Provider RPC contract is missing.")\n    return rpc\n\n\ndef _p2p_contract(provider: dict[str, Any]) -> dict[str, Any]:\n    p2p = _runtime_contract(provider).get("p2p")\n    if not isinstance(p2p, dict):\n        raise ValueError("Provider P2P contract is missing.")\n    return p2p\n\n\ndef _runtime_port(contract: dict[str, Any], name: str) -> int:\n    value = int(contract.get("port", 0))\n    if not 1 <= value <= 65535:\n        raise ValueError(f"Provider {name} port is invalid.")\n    return value\n\n\ndef _rpc_authentication(provider: dict[str, Any]) -> str:\n    value = str(_rpc_contract(provider).get("authentication") or "").strip()\n    if value not in {"none", "username-password"}:\n        raise ValueError("Provider RPC authentication contract is unsupported.")\n    return value\n\n\n'
if "def _runtime_contract(" not in text:
    if anchor not in text:
        raise SystemExit("ERROR: provider helper anchor not found")
    text = text.replace(anchor, helpers, 1)

old = 'def provider_runtime(provider_id: str) -> dict[str, Any]:\n    if provider_id not in PROVIDERS:\n        raise ValueError("Provider is not enabled for installation.")\n    return PROVIDERS[provider_id]\n'
new = 'def provider_runtime(provider_id: str) -> dict[str, Any]:\n    provider = _provider(provider_id)\n    runtime = _runtime_contract(provider)\n\n    adapter = INSTALL_ADAPTERS.get(provider_id)\n\n    result = dict(runtime)\n    result["providerId"] = provider_id\n    result["selectable"] = bool(provider.get("selectable"))\n    result["productionImage"] = provider.get("productionImage")\n    result["installAdapterEnabled"] = adapter is not None\n\n    if adapter is not None:\n        result.update(adapter)\n\n    return result\n'
if old in text:
    text = text.replace(old, new, 1)
elif "installAdapterEnabled" not in text:
    raise SystemExit("ERROR: provider_runtime anchor not found")

old = '        "ports": {\n            "rpc": {"port": 8332, "available": _port_available(8332)},\n            "p2p": {"port": 8333, "available": _port_available(8333)},\n        },\n'
new = '        "ports": {\n            "rpc": {\n                "port": _runtime_port(_rpc_contract(provider), "RPC"),\n                "available": _port_available(\n                    _runtime_port(_rpc_contract(provider), "RPC")\n                ),\n            },\n            "p2p": {\n                "port": _runtime_port(_p2p_contract(provider), "P2P"),\n                "available": _port_available(\n                    _runtime_port(_p2p_contract(provider), "P2P")\n                ),\n            },\n        },\n        "rpcAuthentication": _rpc_authentication(provider),\n'
if old in text:
    text = text.replace(old, new, 1)
elif "rpcAuthentication" not in text:
    raise SystemExit("ERROR: preflight port anchor not found")

old = '    if not value.rpc_user:\n        raise ValueError("RPC user is required.")\n    if len(value.rpc_password) < 24:\n        raise ValueError("RPC password must contain at least 24 characters.")\n    if not 1 <= value.rpc_port <= 65535 or not 1 <= value.p2p_port <= 65535:\n        raise ValueError("Port is invalid.")\n'
new = '    provider = _provider(value.provider_id)\n    rpc_authentication = _rpc_authentication(provider)\n\n    if rpc_authentication == "username-password":\n        if not value.rpc_user:\n            raise ValueError("RPC user is required.")\n        if len(value.rpc_password) < 24:\n            raise ValueError(\n                "RPC password must contain at least 24 characters."\n            )\n\n    expected_rpc_port = _runtime_port(_rpc_contract(provider), "RPC")\n    expected_p2p_port = _runtime_port(_p2p_contract(provider), "P2P")\n\n    if value.rpc_port != expected_rpc_port:\n        raise ValueError(\n            f"RPC port does not match provider contract: expected {expected_rpc_port}."\n        )\n\n    if value.p2p_port != expected_p2p_port:\n        raise ValueError(\n            f"P2P port does not match provider contract: expected {expected_p2p_port}."\n        )\n'
if old in text:
    text = text.replace(old, new, 1)
elif "rpc_authentication = _rpc_authentication" not in text:
    raise SystemExit("ERROR: request validation anchor not found")

old = '        runtime = provider_runtime(value.provider_id)\n        active = self._active_install_for_app(value.app_id)\n'
new = '        runtime = provider_runtime(value.provider_id)\n        if not runtime.get("installAdapterEnabled"):\n            raise ValueError("Provider installation adapter is not enabled.")\n        active = self._active_install_for_app(value.app_id)\n'
if old in text:
    text = text.replace(old, new, 1)

path.write_text(text)
print("SBP-069 installer source patch: PASS")
