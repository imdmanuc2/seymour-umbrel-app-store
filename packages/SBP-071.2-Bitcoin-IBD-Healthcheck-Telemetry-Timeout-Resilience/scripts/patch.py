#!/usr/bin/env python3
from pathlib import Path
import sys

compose = Path(sys.argv[1])
status_app = Path(sys.argv[2])

compose_text = compose.read_text()

old_timeout = "      timeout: 10s\n"
new_timeout = "      timeout: 30s\n"

if old_timeout in compose_text:
    compose_text = compose_text.replace(old_timeout, new_timeout, 1)
elif new_timeout not in compose_text:
    raise SystemExit("ERROR: Bitcoin healthcheck timeout anchor not found")

compose.write_text(compose_text)

text = status_app.read_text()

# Add a dedicated lightweight reachability timeout beside the existing heavy timeout.
heavy_line = 'HEAVY_TIMEOUT=float(os.environ.get("BTC_RPC_HEAVY_TIMEOUT_SECONDS","120"))\n'
reach_line = 'REACHABILITY_TIMEOUT=float(os.environ.get("BTC_RPC_REACHABILITY_TIMEOUT_SECONDS","30"))\n'

if reach_line not in text:
    if heavy_line not in text:
        raise SystemExit("ERROR: HEAVY_TIMEOUT anchor not found")
    text = text.replace(
        heavy_line,
        heavy_line + reach_line,
        1,
    )

# Update the reachability probe only. Do not weaken the heavy telemetry cache contract.
old_call = '        rpc("uptime",5)\n'
new_call = '        rpc("uptime",REACHABILITY_TIMEOUT)\n'

if old_call in text:
    text = text.replace(old_call, new_call, 1)
elif new_call not in text:
    # Accept spacing variant from the compact source.
    old_call = '        rpc("uptime", 5)\n'
    if old_call in text:
        text = text.replace(old_call, new_call, 1)
    elif 'rpc("uptime",REACHABILITY_TIMEOUT)' not in text:
        raise SystemExit("ERROR: reachability uptime timeout anchor not found")

status_app.write_text(text)

print("SBP-071.2 observer timeout patch: PASS")
