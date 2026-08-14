# SBP-060.5 — Provider-Neutral Runtime Projection & Startup Classification

Fixes the Blockchain Manager issues exposed by BCH recovery:

- Installed-node totals are based on telemetry-confirmed installation, not catalog availability.
- Managed Blockchains renders all installed runtimes, not only `live[0]`.
- BCH verification/warmup is presented as `starting`, not `degraded`.
- Docker host availability is checked through `/var/run/docker.sock`, not the Docker CLI inside the manager container.
- A provider-neutral runtime registry introduces BTC telemetry without duplicating BCH dashboard code.

No blockchain runtime is installed, restarted, or modified by this package.
