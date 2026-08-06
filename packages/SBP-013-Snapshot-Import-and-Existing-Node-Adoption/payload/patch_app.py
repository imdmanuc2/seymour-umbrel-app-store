from pathlib import Path
path = Path("seymour-blockchain-manager/data/web/app.py")
text = path.read_text()
if "from adoption import AdoptionService" not in text:
    text = text.replace("from installer import", "from adoption import AdoptionService\nfrom installer import", 1)
    text = text.replace("INSTALLER = Installer()", "INSTALLER = Installer()\nADOPTION = AdoptionService()", 1)
get_marker = '        if self.path == "/api/install/preflight":\n'
get_code = '''        if self.path.startswith("/api/adoption/plans/"):\n            operation_id = self.path.rsplit("/", 1)[-1]\n            try:\n                self.send_json(ADOPTION.load(operation_id))\n            except KeyError:\n                self.send_json({"error": "adoption-plan-not-found"}, status=HTTPStatus.NOT_FOUND)\n            return\n\n'''
if "/api/adoption/plans/" not in text:
    if get_marker not in text:
        raise SystemExit("Expected install preflight route not found.")
    text = text.replace(get_marker, get_code + get_marker, 1)
post_marker = '        if self.path == "/api/install/execute":\n'
post_code = '''        if self.path == "/api/adoption/plan":\n            body = self.read_json_body()\n            self.send_json(ADOPTION.plan(Path(str(body.get("sourcePath", "")))).to_dict())\n            return\n\n        if self.path == "/api/adoption/execute":\n            body = self.read_json_body()\n            result = ADOPTION.execute(str(body.get("operationId", "")), str(body.get("confirmation", "")))\n            status = HTTPStatus.OK if result.status.value == "succeeded" else HTTPStatus.BAD_REQUEST\n            self.send_json(result.to_dict(), status=status)\n            return\n\n'''
if "/api/adoption/execute" not in text:
    if post_marker not in text:
        raise SystemExit("Expected install execute route not found.")
    text = text.replace(post_marker, post_code + post_marker, 1)
path.write_text(text)
print("Existing-node adoption API routes added.")
