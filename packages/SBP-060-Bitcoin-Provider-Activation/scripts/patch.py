#!/usr/bin/env python3
from pathlib import Path
import json
import sys

repo = Path(sys.argv[1]).resolve()

# Activate BTC in both catalogs.
for path in [
    repo / 'shared/provider_catalog/providers.v1.json',
    repo / 'seymour-blockchain-manager/data/catalog/providers.v1.json',
]:
    data = json.loads(path.read_text())
    found = False
    for provider in data.get('providers', []):
        if provider.get('providerId') != 'bitcoin-mainnet':
            continue
        provider['availability'] = 'live'
        provider['selectable'] = True
        provider['productionImage'] = 'ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0'
        provider['installAction'] = {
            'appId': 'seymour-bitcoin-node',
            'confirmation': 'INSTALL-seymour-bitcoin-node',
        }
        found = True
    if not found:
        raise SystemExit(f'Bitcoin provider not found in {path}')
    path.write_text(json.dumps(data, indent=2) + '\n')

# Make preflight route provider-aware.
app = repo / 'seymour-blockchain-manager/data/web/app.py'
text = app.read_text()
if 'from urllib.parse import parse_qs, urlparse' not in text:
    if 'from urllib.parse import urlparse' in text:
        text = text.replace(
            'from urllib.parse import urlparse',
            'from urllib.parse import parse_qs, urlparse',
            1,
        )
    else:
        marker = 'from uuid import uuid4\n'
        if marker not in text:
            raise SystemExit('SBP-060 import anchor not found')
        text = text.replace(marker, marker + 'from urllib.parse import parse_qs, urlparse\n', 1)

old_route = '        if self.path == "/api/install/preflight":\n            self.send_json(preflight())\n            return\n'
new_route = '        if self.path.startswith("/api/install/preflight"):\n            parsed = urlparse(self.path)\n            query = parse_qs(parsed.query)\n            provider_id = query.get("providerId", ["bitcoin-cash-mainnet"])[0]\n            storage_target_id = query.get("storageTargetId", [None])[0]\n            self.send_json(preflight(storage_target_id=storage_target_id, provider_id=provider_id))\n            return\n'
if old_route not in text:
    raise SystemExit('SBP-060 preflight route anchor not found')
text = text.replace(old_route, new_route, 1)
app.write_text(text)

# Request provider-specific preflight in the wizard.
appjs = repo / 'seymour-blockchain-manager/data/web/app.js'
js = appjs.read_text()
old_fetch = '  const preflight = await (await fetch("/api/install/preflight", {cache: "no-store"})).json();\n'
new_fetch = '  const preflight = await (await fetch(`/api/install/preflight?providerId=${encodeURIComponent(provider.providerId)}`, {cache: "no-store"})).json();\n'
if old_fetch not in js:
    raise SystemExit('SBP-060 wizard preflight anchor not found')
js = js.replace(old_fetch, new_fetch, 1)
appjs.write_text(js)

print('SBP-060 Bitcoin provider activation patch: PASS')
