# SBP-045 — BCH Final Hardening & BTC Handoff

Final Bitcoin Cash stabilization milestone before beginning Bitcoin runtime work.

Fixes:
1. Post-restart metric continuity
   - a transient `syncing` payload with missing height/headers/progress no longer
     overwrites the last complete syncing telemetry snapshot
   - UI never renders `NaN / NaN`
   - last confirmed sync telemetry is held briefly while fresh metrics warm up

2. Operations logs
   - removes dependency on a `docker` CLI binary inside the Blockchain Manager
     container
   - reads container logs through the mounted Docker Engine UNIX socket
   - returns structured errors instead of causing app-proxy HTTP 502

3. Diagnostics
   - uses the canonical BCH runtime probe instead of spawning `docker inspect`
     and `docker exec`
   - returns structured canonical runtime/RPC/sync checks
   - remains observational only

4. Lifecycle request resilience
   - lifecycle plan/execute browser timeout increases from 15s to 30s
   - the canonical lifecycle endpoint remains the only execution path

No direct Docker lifecycle commands are introduced.
No live lifecycle action is executed by doctor/install/verify.
