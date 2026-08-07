# SBP-019 — Live Registration Refresh & Scheduled Telemetry Delivery

Target: /home/umbrel/seymour-umbrel-app-store-git
Branch: master

Adds in-process scheduled registration/telemetry refresh to Nexus using the existing SBP-016 delivery path.

API:
- GET /api/nexus/scheduler/status
- POST /api/nexus/scheduler/run

Defaults: enabled=true, interval=60s, initial delay=15s.
