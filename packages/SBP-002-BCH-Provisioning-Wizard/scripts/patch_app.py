from pathlib import Path
import sys

repo = Path(sys.argv[1])
path = repo / "seymour-bch-node/data/status/app.py"
text = path.read_text()

if "from provisioning import build_plan" not in text:
    text = text.replace(
        "from pathlib import Path\n",
        "from pathlib import Path\nfrom urllib.parse import parse_qs\nfrom provisioning import build_plan\n",
    )

if "def read_form(self)" not in text:
    text = text.replace(
        "class Handler(BaseHTTPRequestHandler):\n",
        "class Handler(BaseHTTPRequestHandler):\n"
        "    def read_form(self):\n"
        "        length = int(self.headers.get('Content-Length', '0'))\n"
        "        body = self.rfile.read(length).decode()\n"
        "        parsed = parse_qs(body)\n"
        "        return {k: v[-1] for k, v in parsed.items()}\n\n",
    )

if 'self.path == "/provision"' not in text:
    text = text.replace(
        '        if self.path == "/":\n',
        '        if self.path == "/provision":\n'
        '            body = Path("/app/templates/provision.html").read_bytes()\n'
        '            self.send_response(200)\n'
        '            self.send_header("Content-Type", "text/html; charset=utf-8")\n'
        '            self.send_header("Content-Length", str(len(body)))\n'
        '            self.end_headers()\n'
        '            self.wfile.write(body)\n'
        '            return\n\n'
        '        if self.path == "/":\n',
    )

if "def do_POST(self)" not in text:
    text = text.replace(
        "    def log_message(self, format: str, *args) -> None:\n",
        "    def do_POST(self) -> None:\n"
        "        if self.path != '/api/provisioning/plan':\n"
        "            self.send_json({'error': 'Not found'}, 404)\n"
        "            return\n"
        "        plan = build_plan(self.read_form())\n"
        "        self.send_json(plan, 200 if plan['validation']['valid'] else 400)\n\n"
        "    def log_message(self, format: str, *args) -> None:\n",
    )

path.write_text(text)
