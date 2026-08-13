# SBP-060.1 — Blockchain Manager Portable Umbrel Installation

Removes development-host path dependencies from Seymour Blockchain Manager so a
clean Umbrel host can install it directly from the Seymour Community App Store.

Fixes clean-install failures caused by hard dependencies on:
- /home/umbrel/seymour-umbrel-app-store-git/private/nexus-registration.env
- /home/umbrel/seymour-umbrel-app-store-git/scripts
- /home/umbrel/seymour-umbrel-app-store-git/shared

The app becomes self-contained under APP_DATA_DIR using:
- data/control
- data/shared
- data/web
- data/catalog
- data/evidence

Nexus registration remains optional.
