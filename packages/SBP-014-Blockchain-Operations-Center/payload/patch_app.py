from pathlib import Path
p=Path("seymour-blockchain-manager/data/web/app.py");t=p.read_text()
if "from operations_center import" not in t:
 t=t.replace("from sync_manager import analyze","from sync_manager import analyze\nfrom operations_center import OperationKind, diagnostics, execute_backup, plan, recent_logs, recommendations",1)
if "/api/operations/diagnostics" not in t:
 a='        if self.path == "/api/sync":\n'
 b='        if self.path == "/api/operations/diagnostics":\n            result = diagnostics()\n            payload = result.to_dict()\n            payload["recommendations"] = recommendations(result.result or {})\n            self.send_json(payload)\n            return\n\n        if self.path.startswith("/api/operations/logs"):\n            self.send_json(recent_logs().to_dict())\n            return\n\n'
 if a not in t: raise SystemExit("Expected sync route anchor not found.")
 t=t.replace(a,b+a,1)
if "/api/operations/plan" not in t:
 a='        if self.path == "/api/adoption/plan":\n'
 b='        if self.path == "/api/operations/plan":\n            body = self.read_json_body()\n            self.send_json(plan(OperationKind(str(body.get("kind", ""))), dict(body.get("details", {}))).to_dict())\n            return\n\n        if self.path == "/api/operations/backup":\n            body = self.read_json_body()\n            result = execute_backup(str(body.get("confirmation", "")))\n            status = HTTPStatus.OK if result.status.value == "succeeded" else HTTPStatus.BAD_REQUEST\n            self.send_json(result.to_dict(), status=status)\n            return\n\n'
 if a not in t: raise SystemExit("Expected adoption route anchor not found.")
 t=t.replace(a,b+a,1)
p.write_text(t);print("Blockchain Operations Center API routes added.")
