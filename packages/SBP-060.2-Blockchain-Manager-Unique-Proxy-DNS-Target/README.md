# SBP-060.2 — Blockchain Manager Unique Proxy DNS Target

Fixes clean-Umbrel proxy routing collisions caused by the generic Docker alias `web`.

Observed:
- unrelated apps shared alias `web`
- Docker DNS returned multiple IPs
- Blockchain Manager proxy intermittently hit the wrong container
- users saw ECONNREFUSED or incomplete UI loading

This package changes APP_HOST to the unique Blockchain Manager web container name
and records install readiness requirements: unique DNS, port 8080 reachable,
`/api/health` HTTP 200, and proxy-to-backend success.
