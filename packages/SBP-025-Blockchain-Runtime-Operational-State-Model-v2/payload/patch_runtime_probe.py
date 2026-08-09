from pathlib import Path

path = Path(
    "seymour-blockchain-manager/data/web/"
    "bch_runtime_probe.py"
)
text = path.read_text()

import_line = (
    "from runtime_state import "
    "normalize_runtime_state\n"
)

if import_line not in text:
    marker = (
        "from bch_rpc_probe import "
        "probe as probe_bch_rpc\n"
    )
    if marker not in text:
        raise SystemExit(
            "Could not locate bch_rpc_probe import."
        )
    text = text.replace(
        marker,
        marker + import_line,
        1,
    )

if 'result["operationalState"]' in text:
    print(
        "BCH runtime operational state already wired."
    )
    path.write_text(text)
    raise SystemExit(0)

needle = (
    'return {"providerId":"bitcoin-cash-mainnet"'
)

idx = text.find(needle)
if idx == -1:
    raise SystemExit(
        "Could not locate BCH runtime return statement."
    )

line_end = text.find("\n", idx)
if line_end == -1:
    line_end = len(text)

old_line = text[idx:line_end]
payload_expr = old_line[len("return "):]

replacement = (
    "result = "
    + payload_expr
    + '\n result["operationalState"] = '
      'normalize_runtime_state(result)'
    + '\n result["lifecycleStatus"] = '
      'result["operationalState"]["state"]'
    + '\n return result'
)

text = (
    text[:idx]
    + replacement
    + text[line_end:]
)

path.write_text(text)
print(
    "BCH runtime operational state model wired."
)
