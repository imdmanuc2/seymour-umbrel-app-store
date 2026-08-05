# Umbrel Integration

Umbrel owns application container lifecycle and app-scoped persistent storage.

Seymour Umbrel applications must:

- install from the Seymour App Store
- use app-owned persistent data
- avoid host package management and raw disk operations
- publish health and service contracts
- support backup and rollback
- expose supported configuration through the user interface

SPI must respect the Umbrel adapter safety boundary.
