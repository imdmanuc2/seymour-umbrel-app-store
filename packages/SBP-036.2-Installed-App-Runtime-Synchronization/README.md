# SBP-036.2 — Installed App Runtime Synchronization

Synchronizes the installed Seymour Blockchain Manager runtime definition under
Umbrel `app-data` with the verified repository definition.

This package:
- backs up the installed app-data compose and lifecycle HTTP files
- synchronizes installed `docker-compose.yml`
- synchronizes installed `data/web/app.py`
- synchronizes installed `data/web/lifecycle_routes.py`
- verifies canonical lifecycle wiring in the installed runtime
- does not run Docker lifecycle commands
- does not automatically restart Blockchain Manager
- verifies the live running container after a native Umbrel restart

After install:

    cd /home/umbrel/seymour-umbrel-app-store-git
    ./scripts/seymour-umbrel-app restart seymour-blockchain-manager \
      --execute \
      --confirm RESTART-seymour-blockchain-manager

Then:

    cd /home/umbrel/seymour-umbrel-app-store-git/packages/SBP-036.2-Installed-App-Runtime-Synchronization
    sudo ./scripts/verify.sh
