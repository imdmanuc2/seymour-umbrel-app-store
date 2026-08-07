from pathlib import Path

path = Path("seymour-blockchain-manager/data/web/app.py")
text = path.read_text()

if "from nexus_integration import" not in text:
    text = text.replace(
        "from operations_center import (",
        "from nexus_integration import (\n"
        "    append_registration_evidence,\n"
        "    discovery_document,\n"
        "    registration_payload,\n"
        ")\n"
        "from operations_center import (",
        1,
    )

anchor = '        if self.path == "/api/operations/diagnostics":\n'
routes = (
    '        if self.path == "/api/nexus/discovery":\n'
    '            dashboard = dashboard_payload()\n'
    '            sync = analyze(dashboard)\n'
    '            self.send_json(discovery_document(dashboard, sync))\n'
    '            return\n\n'
    '        if self.path == "/api/nexus/registration":\n'
    '            dashboard = dashboard_payload()\n'
    '            sync = analyze(dashboard)\n'
    '            payload = registration_payload(dashboard, sync)\n'
    '            append_registration_evidence(payload)\n'
    '            self.send_json(payload)\n'
    '            return\n\n'
)

if "/api/nexus/discovery" not in text:
    if anchor not in text:
        raise SystemExit("Expected Operations Center route anchor not found.")
    text = text.replace(anchor, routes + anchor, 1)

path.write_text(text)
print("Nexus integration API routes added.")
