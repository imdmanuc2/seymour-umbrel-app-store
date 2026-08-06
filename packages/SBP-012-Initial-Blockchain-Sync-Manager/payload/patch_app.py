from pathlib import Path

path = Path("seymour-blockchain-manager/data/web/app.py")
text = path.read_text()
if "from sync_manager import analyze" not in text:
    text = text.replace(
        "from telemetry import dashboard_payload",
        "from telemetry import dashboard_payload\nfrom sync_manager import analyze",
        1,
    )
anchor = '''        if self.path == "/api/dashboard":
            self.send_json(dashboard_payload())
            return
'''
replacement = anchor + '''
        if self.path == "/api/sync":
            self.send_json(analyze(dashboard_payload()))
            return
'''
if "/api/sync" not in text:
    if anchor not in text:
        raise SystemExit("Expected dashboard route was not found.")
    text = text.replace(anchor, replacement, 1)
path.write_text(text)
print("Sync Manager API route added.")
