# SBP-030 — Umbrel App Lifecycle Engine Foundation

Target repository: /home/umbrel/seymour-umbrel-app-store-git

Creates one canonical lifecycle contract for all Seymour Umbrel applications.

Actions:
- install
- start
- stop
- restart
- update
- uninstall

States:
- not-installed
- installing
- stopped
- starting
- running
- restarting
- updating
- uninstalling
- degraded
- error
- unknown

SBP-030 plans lifecycle operations but does not execute live write actions.
