# SBP-040 — Blockchain Manager Live Runtime Status UI Fix

Makes `/api/dashboard` consume the same canonical BCH runtime probe already used by lifecycle and Nexus.

This fixes the contradictory card state where BCH can show `Not installed` or `RPC Unavailable` while live synchronization telemetry is present.

Expected live card while BCH is in initial block download:

- Status: Syncing
- RPC: Healthy
- Progress: live verification progress
- Height: live BCH height
- Headers: live header height
- Peers: live peer count

The package also replaces generated BCH status container hostnames with the stable Compose service alias `status`.

No lifecycle write is executed by doctor/install/verify.
