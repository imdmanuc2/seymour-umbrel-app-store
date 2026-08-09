from pathlib import Path

path = Path("seymour-blockchain-manager/data/web/bch_runtime_probe.py")
text = path.read_text()

import_line = "from runtime_state import normalize_runtime_state\n"
if import_line not in text:
    marker = "from bch_rpc_probe import probe as probe_bch_rpc\n"
    if marker not in text:
        raise SystemExit("Could not locate bch_rpc_probe import.")
    text = text.replace(marker, marker + import_line, 1)

needle = 'return {"providerId":"bitcoin-cash-mainnet"'
idx = text.find(needle)
if idx == -1:
    raise SystemExit("Could not locate BCH runtime return statement.")
line_end = text.find("\n", idx)
old_line = text[idx:line_end]
if not old_line.startswith("return "):
    raise SystemExit("Unexpected BCH runtime return statement.")
expr = old_line[len("return "):]
new_block = (
    "result = " + expr + "\n"
    " result[\"operationalState\"] = normalize_runtime_state(result)\n"
    " result[\"lifecycleStatus\"] = result[\"operationalState\"][\"state\"]\n"
    " return result"
)
text = text[:idx] + new_block + text[line_end:]
path.write_text(text)
print("BCH runtime operational state model wired.")
