# SPI Runtime

SPI is background platform infrastructure, not the primary user interface.

## Version 1.0 responsibilities

- detect supported platforms
- validate adapter capabilities
- resolve product requirements
- create lifecycle operations
- collect evidence
- retry and resume safely
- create transaction checkpoints
- execute rollback workflows
- enforce post-action health gates

## Current implementation constraint

SPI remains conservative until exercised against real product deployments. New packages are added only when a production workflow proves they are needed.
