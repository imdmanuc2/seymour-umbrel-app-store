from pathlib import Path

path = Path(
    "seymour-blockchain-manager/data/web/app.py"
)

text = path.read_text()


# ---------------------------------------------------------
# Scheduler imports
# ---------------------------------------------------------

import_anchor = (
    "from nexus_delivery import deliver, load_status\n"
)

scheduler_import = '''from nexus_scheduler import (
    refresh_once as nexus_refresh_once,
    start as start_nexus_scheduler,
    status as nexus_scheduler_status,
)
'''

if "from nexus_scheduler import (" not in text:
    if import_anchor not in text:
        raise SystemExit(
            "Could not locate nexus_delivery import."
        )

    text = text.replace(
        import_anchor,
        import_anchor + scheduler_import,
        1,
    )


# ---------------------------------------------------------
# GET /api/nexus/scheduler/status
# ---------------------------------------------------------

get_anchor = '''        if self.path == "/api/nexus/delivery/status":
'''

get_route = '''        if self.path == "/api/nexus/scheduler/status":
            self.send_json(
                nexus_scheduler_status()
            )
            return

'''

if "/api/nexus/scheduler/status" not in text:
    if get_anchor not in text:
        raise SystemExit(
            "Could not locate Nexus delivery status route."
        )

    text = text.replace(
        get_anchor,
        get_route + get_anchor,
        1,
    )


# ---------------------------------------------------------
# POST /api/nexus/scheduler/run
# ---------------------------------------------------------

post_anchor = '''        if self.path == "/api/nexus/delivery":
'''

post_route = '''        if self.path == "/api/nexus/scheduler/run":
            result = nexus_refresh_once()

            status = (
                HTTPStatus.OK
                if result.get("status") in {
                    "succeeded",
                    "disabled",
                    "not-configured",
                }
                else HTTPStatus.BAD_GATEWAY
            )

            self.send_json(
                result,
                status=status,
            )
            return

'''

if "/api/nexus/scheduler/run" not in text:
    if post_anchor not in text:
        raise SystemExit(
            "Could not locate Nexus delivery POST route."
        )

    text = text.replace(
        post_anchor,
        post_route + post_anchor,
        1,
    )


# ---------------------------------------------------------
# Scheduler startup
# ---------------------------------------------------------

startup_anchor = '''if __name__ == "__main__":
    ThreadingHTTPServer(
'''

startup_replacement = '''if __name__ == "__main__":
    start_nexus_scheduler()

    ThreadingHTTPServer(
'''

if "start_nexus_scheduler()" not in text:
    if startup_anchor not in text:
        raise SystemExit(
            "Could not locate Blockchain Manager startup."
        )

    text = text.replace(
        startup_anchor,
        startup_replacement,
        1,
    )


path.write_text(text)

print(
    "Nexus scheduler application integration added."
)
