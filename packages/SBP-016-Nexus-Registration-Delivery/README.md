# SBP-016 — Nexus Registration Delivery

Adds reliable delivery of the Seymour Blockchain Manager registration payload
to Nexus Command Center.

## Adds

- authenticated HTTPS delivery;
- idempotency keys;
- retry and exponential backoff;
- delivery timeout controls;
- last-known registration status;
- append-only delivery evidence;
- manual delivery API route;
- dry-run verification;
- no live Nexus delivery during package verification.

## Required runtime configuration

- `NEXUS_REGISTRATION_URL`
- `NEXUS_REGISTRATION_TOKEN`

Optional:

- `NEXUS_REGISTRATION_TIMEOUT_SECONDS`
- `NEXUS_REGISTRATION_MAX_ATTEMPTS`
- `NEXUS_REGISTRATION_BACKOFF_SECONDS`
