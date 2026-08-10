# SBP-038 — Canonical Runtime State Service

Promotes operational-state normalization into shared Seymour code.

The BCH runtime probe remains responsible for collecting raw observations.
`shared/runtime_state` becomes the only state normalization implementation.
Nexus continues to consume `operationalState`; lifecycle now consumes the same
direct BCH probe instead of performing another HTTP lookup.

Canonical vocabulary:
starting, syncing, running, degraded, stopped, offline, error, unknown.

No live lifecycle write is performed by doctor/install/verify.
