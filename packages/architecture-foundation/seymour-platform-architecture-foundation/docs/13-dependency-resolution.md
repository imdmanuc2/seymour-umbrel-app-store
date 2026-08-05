# Dependency Resolution

Products declare required capabilities and services.

SPI resolves each requirement by:

1. discovering an existing healthy compatible service;
2. offering to install a compatible Seymour product;
3. accepting an approved remote service;
4. blocking the plan when the requirement cannot be satisfied safely.

Example: Seymour MiningCore requests a healthy Bitcoin Cash RPC and ZMQ service. It does not hardcode a container or install a node directly.
