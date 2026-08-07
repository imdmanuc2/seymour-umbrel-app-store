from pathlib import Path

path = Path("seymour-blockchain-manager/data/web/app.py")
text = path.read_text()

if "from nexus_delivery import" not in text:
    text = text.replace(
        "from nexus_integration import (",
        "from nexus_delivery import (\n"
        "    deliver,\n"
        "    load_status,\n"
        ")\n"
        "from nexus_integration import (",
        1,
    )

get_anchor = '        if self.path == "/api/nexus/discovery":\n'

get_routes = (
    '        if self.path == "/api/nexus/delivery/status":\n'
    '            self.send_json(load_status())\n'
    '            return\n\n'
)

if "/api/nexus/delivery/status" not in text:
    if get_anchor not in text:
        raise SystemExit(
            "Expected Nexus discovery route anchor not found."
        )
    text = text.replace(
        get_anchor,
        get_routes + get_anchor,
        1,
    )

post_anchor = '        if self.path == "/api/operations/plan":\n'

post_routes = (
    '        if self.path == "/api/nexus/delivery":\n'
    '            body = self.read_json_body()\n'
    '            dashboard = dashboard_payload()\n'
    '            sync = analyze(dashboard)\n'
    '            payload = registration_payload(dashboard, sync)\n'
    '            result = deliver(\n'
    '                payload,\n'
    '                dry_run=bool(body.get("dryRun", False)),\n'
    '            )\n'
    '            status = (\n'
    '                HTTPStatus.OK\n'
    '                if result.status in {"succeeded", "dry-run"}\n'
    '                else HTTPStatus.BAD_GATEWAY\n'
    '            )\n'
    '            self.send_json(result.to_dict(), status=status)\n'
    '            return\n\n'
)

if "/api/nexus/delivery" not in text:
    if post_anchor not in text:
        raise SystemExit(
            "Expected Operations Center POST anchor not found."
        )
    text = text.replace(
        post_anchor,
        post_routes + post_anchor,
        1,
    )

path.write_text(text)

print("Nexus registration delivery API routes added.")
