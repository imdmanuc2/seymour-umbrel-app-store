# SBP-004 — Umbrel Runtime Integration

SBP-004 introduces a shared, read-only runtime bridge between Seymour products
and Umbrel.

The runtime can:

- enumerate App Store source apps;
- enumerate installed Umbrel app-data directories;
- inspect Docker Compose containers;
- normalize lifecycle state;
- report versions and declared dependencies;
- probe health endpoints;
- collect recent logs;
- emit structured JSON for Nexus, SPI, and diagnostics tools.

No lifecycle write operations are enabled in SBP-004.
