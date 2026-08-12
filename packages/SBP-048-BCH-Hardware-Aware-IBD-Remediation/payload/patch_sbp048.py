from pathlib import Path
import sys

root = Path(sys.argv[1])

prov = root / "seymour-bch-node/data/status/provisioning.py"
entry = root / "seymour-bch-node/data/node/entrypoint.sh"
form = root / "seymour-bch-node/data/status/templates/provision.html"

s = prov.read_text()
s = s.replace('form.get("txindex", "1")', 'form.get("txindex", "0")')
s = s.replace("        txindex = True\n", "        txindex = False\n")
prov.write_text(s)

s = entry.read_text()
s = s.replace('TXINDEX="${BCH_TXINDEX:-1}"', 'TXINDEX="${BCH_TXINDEX:-0}"')
entry.write_text(s)

s = form.read_text()
s = s.replace('<option value="1" selected>', '<option value="1">')
if '<option value="0">' in s and '<option value="0" selected>' not in s:
    s = s.replace('<option value="0">', '<option value="0" selected>', 1)
form.write_text(s)

print("SBP-048 txindex default policy patched")
