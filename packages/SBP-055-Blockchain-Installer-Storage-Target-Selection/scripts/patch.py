#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
installer = repo / 'seymour-blockchain-manager/data/web/installer.py'
app = repo / 'seymour-blockchain-manager/data/web/app.py'
js = repo / 'seymour-blockchain-manager/data/web/app.js'

text = installer.read_text()
if 'from shared.blockchain_install import evaluate as evaluate_install_preflight' not in text:
    text = text.replace('from uuid import uuid4\n', 'from uuid import uuid4\n\nfrom shared.blockchain_install import evaluate as evaluate_install_preflight\nfrom shared.blockchain_install.host import profile as host_profile\nfrom storage_targets import storage_targets, target_by_id\n', 1)

text = text.replace('    p2p_port: int\n    confirmation: str\n', '    p2p_port: int\n    storage_target_id: str\n    confirmation: str\n', 1)
text = text.replace('            p2p_port=int(data.get("p2pPort", 8333)),\n            confirmation=str(data.get("confirmation", "")),\n', '            p2p_port=int(data.get("p2pPort", 8333)),\n            storage_target_id=str(data.get("storageTargetId", "")).strip(),\n            confirmation=str(data.get("confirmation", "")),\n', 1)

start = text.find('def preflight() -> dict[str, Any]:')
end = text.find('\ndef validate_request', start)
if start < 0 or end < 0:
    raise SystemExit('SBP-055 preflight anchor not found')
new_preflight = '''def preflight(storage_target_id: str | None = None) -> dict[str, Any]:
    provider = _provider()
    inventory = storage_targets()
    targets = inventory.get("targets", [])
    selected = target_by_id(storage_target_id) if storage_target_id else None
    if selected is None and targets:
        for item in sorted(targets, key=lambda value: int(value.get("free_bytes", 0)), reverse=True):
            candidate = target_by_id(item["target_id"])
            if candidate is not None:
                selected = candidate
                break
    checks = {
        "providerSelectable": provider["selectable"],
        "productionImage": provider["productionImage"],
        "networkAvailable": _network_available(),
        "ports": {
            "rpc": {"port": 8332, "available": _port_available(8332)},
            "p2p": {"port": 8333, "available": _port_available(8333)},
        },
        "storageTargets": inventory,
        "selectedStorageTargetId": selected.target_id if selected else None,
    }
    errors = []
    if not checks["providerSelectable"]: errors.append("Bitcoin Cash is not selectable.")
    if not checks["productionImage"]: errors.append("Bitcoin Cash has no production image.")
    if not checks["networkAvailable"]: errors.append("Container registry is unreachable.")
    common = None
    if selected is None:
        errors.append("No storage target is selected.")
    else:
        common = evaluate_install_preflight(provider=provider, host=host_profile(), storage_target=selected)
        errors.extend(common.errors)
    return {
        "compatible": not errors,
        "checks": checks,
        "errors": errors,
        "storagePreflight": common.to_dict() if common is not None else None,
    }
'''
text = text[:start] + new_preflight + text[end:]
text = text.replace('    if not value.node_name: raise ValueError("Node name is required.")\n', '    if not value.node_name: raise ValueError("Node name is required.")\n    if not value.storage_target_id: raise ValueError("Storage target is required.")\n', 1)
text = text.replace('        checks = preflight()\n', '        checks = preflight(value.storage_target_id)\n', 1)
installer.write_text(text)

app_text = app.read_text()
if 'from storage_targets import storage_targets' not in app_text:
    app_text = app_text.replace('from installer import Installer\n', 'from installer import Installer\nfrom storage_targets import storage_targets\n', 1)
anchor = '        if self.path == "/api/install/preflight":\n            self.send_json(preflight())\n            return\n'
addition = anchor + '\n        if self.path == "/api/install/storage-targets":\n            self.send_json(storage_targets())\n            return\n'
if anchor not in app_text:
    raise SystemExit('SBP-055 app route anchor not found')
app.write_text(app_text.replace(anchor, addition, 1))

js_text = js.read_text()
fetch_anchor = '  const preflight = await (await fetch("/api/install/preflight", {cache: "no-store"})).json();\n'
if fetch_anchor not in js_text:
    raise SystemExit('SBP-055 JS preflight anchor not found')
fetch_add = fetch_anchor + '  const storageInventory = await (await fetch("/api/install/storage-targets", {cache: "no-store"})).json();\n  const storageTargets = storageInventory.targets || [];\n  const defaultStorageTargetId = preflight?.checks?.selectedStorageTargetId || storageTargets[0]?.target_id || "";\n'
js_text = js_text.replace(fetch_anchor, fetch_add, 1)
dialog_anchor = '<section class="wizard-section"><label>Node name<input id="wizardNodeName"'
dialog_replace = '<section class="wizard-section"><label>Storage target<select id="wizardStorageTarget">${storageTargets.map((target)=>`<option value="${target.target_id}" ${target.target_id===defaultStorageTargetId?"selected":""}>${target.type.toUpperCase()} · ${target.path} · ${formatBytes(target.free_bytes)} free</option>`).join("")}</select></label><label>Node name<input id="wizardNodeName"'
if dialog_anchor not in js_text:
    raise SystemExit('SBP-055 JS wizard anchor not found')
js_text = js_text.replace(dialog_anchor, dialog_replace, 1)
payload_anchor = 'p2pPort: Number(document.getElementById("wizardP2pPort").value),'
if payload_anchor not in js_text:
    raise SystemExit('SBP-055 JS payload anchor not found')
js_text = js_text.replace(payload_anchor, payload_anchor + '\n      storageTargetId: document.getElementById("wizardStorageTarget").value,', 1)
js.write_text(js_text)
print('SBP-055 installer/API/UI patch: PASS')
