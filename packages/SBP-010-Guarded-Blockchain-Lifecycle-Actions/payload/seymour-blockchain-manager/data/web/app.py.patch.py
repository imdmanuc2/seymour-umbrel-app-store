from pathlib import Path
p=Path.cwd()/'seymour-blockchain-manager/data/web/app.py'
s=p.read_text()
s=s.replace('from telemetry import dashboard_payload','from telemetry import dashboard_payload\nfrom lifecycle import GuardedLifecycleService, LifecycleAction')
s=s.replace('WEB_ROOT = Path(__file__).resolve().parent','WEB_ROOT = Path(__file__).resolve().parent\nLIFECYCLE = GuardedLifecycleService()')
insert="""\n    def do_POST(self) -> None:\n        prefix = "/api/lifecycle/"\n        if not self.path.startswith(prefix):\n            self.send_error(HTTPStatus.NOT_FOUND)\n            return\n        action = LifecycleAction(self.path[len(prefix):])\n        length = int(self.headers.get("Content-Length", "0"))\n        body = json.loads(self.rfile.read(length).decode()) if length else {}\n        result = LIFECYCLE.execute(\n            provider_id=str(body.get("providerId", "")),\n            app_id=str(body.get("appId", "")),\n            action=action,\n            confirmation=body.get("confirmation"),\n        )\n        self.send_json(result.to_dict(), status=HTTPStatus.OK if result.status.value == "succeeded" else HTTPStatus.BAD_REQUEST)\n\n"""
marker='    def log_message('
if marker not in s: raise SystemExit('log_message marker missing')
s=s.replace(marker,insert+marker)
p.write_text(s)
print('Lifecycle API routes installed.')
