# ADR-0001: Product Boundaries

## Status

Proposed

## Decision

Blockchain nodes, mining applications, pool engines, lifecycle orchestration, and operations visibility are separate products with independent lifecycles and published service contracts.

## Consequences

- MiningCore does not install or own blockchain nodes.
- Nexus does not own product-private configuration.
- SPI orchestrates but does not become the user-facing product.
