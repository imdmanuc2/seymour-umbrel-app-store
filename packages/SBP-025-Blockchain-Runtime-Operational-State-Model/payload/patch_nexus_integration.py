from pathlib import Path

path = Path("seymour-blockchain-manager/data/web/nexus_integration.py")
text = path.read_text()

if '"operationalState"' in text:
    print("Operational state already present in Nexus integration.")
else:
    marker = '"lifecycleStatus": runtime.get("lifecycleStatus"),'
    if marker not in text:
        raise SystemExit("Could not locate lifecycleStatus in Nexus integration.")
    text = text.replace(
        marker,
        marker + '\n            "operationalState": runtime.get("operationalState"),',
        1,
    )
    path.write_text(text)
    print("Normalized runtime state added to Nexus registration payload.")
