# SBP-036.3 — Blockchain Manager App Proxy Service DNS Repair

Purpose
-------

Repair the Blockchain Manager app proxy target after Umbrel/Compose recreated
containers with hyphenated names.

Observed live failure:

    app proxy target: seymour-blockchain-manager_web_1
    running web container: seymour-blockchain-manager-web-1

Container instance names are implementation details and changed across Compose
behavior. The stable Docker network alias is the Compose service name:

    web

This package changes:

    APP_HOST: seymour-blockchain-manager_web_1

to:

    APP_HOST: web

in both:
- repository source compose
- authoritative installed Umbrel app-data compose

The verifier discovers containers by Compose labels rather than hard-coded
container names, validates DNS resolution of `web` from the app proxy, checks
the lifecycle shared mount/environment, and performs non-executing HTTP
acceptance tests.

No Docker lifecycle commands are used.

After install, restart Blockchain Manager through the native Umbrel lifecycle:

    cd /home/umbrel/seymour-umbrel-app-store-git
    ./scripts/seymour-umbrel-app restart seymour-blockchain-manager \
      --execute \
      --confirm RESTART-seymour-blockchain-manager

Then run:

    cd /home/umbrel/seymour-umbrel-app-store-git/packages/SBP-036.3-Blockchain-Manager-App-Proxy-Service-DNS-Repair
    sudo ./scripts/verify.sh
