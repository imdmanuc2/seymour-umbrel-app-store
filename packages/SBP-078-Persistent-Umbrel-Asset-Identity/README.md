# SBP-078 — Persistent Umbrel Asset Identity

## Purpose

Prevent Seymour Blockchain Manager and managed blockchain runtimes from
creating duplicate Nexus CMDB assets when Umbrel application containers are
recreated.

## Identity contract

Container hostname is runtime evidence only and MUST NOT determine persistent
CMDB identity.

Manager and runtime asset identities are derived from:

    stable Umbrel host identity + application ID

The Umbrel host machine ID is mounted read-only into the Blockchain Manager
container.

Hostname, IP address, container hostname, and container ID remain mutable
observational properties.

## Nexus registration configuration

Nexus registration configuration is loaded from:

    ${APP_DATA_DIR}/data/private/nexus-registration.env

This private environment file is runtime state and must never be committed.

## Proven live identities

For the currently verified Umbrel host:

    Manager: asset-7be2040a1a33c91c
    BCH:     asset-1a3a169d72207de3

The implementation was verified through a native Umbrel restart followed by
repeated authenticated Nexus registration deliveries returning HTTP 200.

## Safety

- Registration secrets are excluded from Git.
- Host identity is mounted read-only.
- Native Umbrel lifecycle remains authoritative.
- No direct Docker lifecycle management is introduced.
