from pathlib import Path

path = Path(
    "seymour-blockchain-manager/data/web/"
    "nexus_integration.py"
)
text = path.read_text()

# Current SBP-020 registration wrapper.
current_marker = (
    '        telemetry["lifecycleStatus"] = '
    'runtime["lifecycleStatus"]\n'
    '        telemetry["rpc"] = runtime["rpc"]\n'
    '        asset["status"] = '
    'runtime["lifecycleStatus"]\n'
)

current_replacement = (
    '        telemetry["lifecycleStatus"] = '
    'runtime["lifecycleStatus"]\n'
    '        telemetry["operationalState"] = '
    'runtime.get("operationalState")\n'
    '        telemetry["rpc"] = runtime["rpc"]\n'
    '        asset["operationalState"] = '
    'runtime.get("operationalState")\n'
    '        asset["status"] = '
    'runtime["lifecycleStatus"]\n'
)

# Idempotency.
if (
    'telemetry["operationalState"]'
    in text
):
    print(
        "Normalized runtime state already present "
        "in current Nexus integration."
    )
    raise SystemExit(0)

if current_marker in text:
    path.write_text(
        text.replace(
            current_marker,
            current_replacement,
            1,
        )
    )
    print(
        "Normalized runtime state added to "
        "SBP-020 Nexus registration wrapper."
    )
    raise SystemExit(0)

# Legacy structured payload fallback.
legacy_marker = (
    '"lifecycleStatus": '
    'runtime.get("lifecycleStatus"),'
)

if legacy_marker in text:
    path.write_text(
        text.replace(
            legacy_marker,
            legacy_marker
            + '\n            '
              '"operationalState": '
              'runtime.get("operationalState"),',
            1,
        )
    )
    print(
        "Normalized runtime state added to "
        "legacy Nexus integration."
    )
    raise SystemExit(0)

raise SystemExit(
    "Could not locate a supported Nexus runtime "
    "projection layout."
)
