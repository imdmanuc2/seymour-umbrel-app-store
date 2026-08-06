from pathlib import Path

path = Path("seymour-blockchain-manager/data/web/app.py")
text = path.read_text()
if "from installer import" not in text:
    text = text.replace("from lifecycle import (", "from installer import Installer, InstallRequest, generate_credentials, preflight\nfrom lifecycle import (", 1)
    text = text.replace("LIFECYCLE = GuardedLifecycleService()", "LIFECYCLE = GuardedLifecycleService()\nINSTALLER = Installer()", 1)
    text = text.replace("    def do_GET(self) -> None:\n", "    def do_GET(self) -> None:\n        if self.path == \"/api/install/preflight\":\n            self.send_json(preflight())\n            return\n\n        if self.path == \"/api/install/credentials\":\n            self.send_json(generate_credentials())\n            return\n\n", 1)
    text = text.replace("    def do_POST(self) -> None:\n", "    def do_POST(self) -> None:\n        if self.path == \"/api/install/execute\":\n            try:\n                operation = INSTALLER.execute(InstallRequest.from_dict(self.read_json_body()))\n                status = HTTPStatus.OK if operation.status.value == \"succeeded\" else HTTPStatus.BAD_REQUEST\n                self.send_json(operation.to_dict(), status=status)\n            except ValueError as exc:\n                self.send_json({\"error\": \"invalid-install-request\", \"message\": str(exc)}, status=HTTPStatus.BAD_REQUEST)\n            except Exception as exc:\n                self.send_json({\"error\": \"installation-failure\", \"message\": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)\n            return\n\n", 1)
    text = text.replace('"label": "Manage Bitcoin Cash",', '"label": "Install Bitcoin Cash",\n            "confirmation": f"INSTALL-{BCH_APP_ID}",', 1)
path.write_text(text)
print("Blockchain Manager installation routes added.")
