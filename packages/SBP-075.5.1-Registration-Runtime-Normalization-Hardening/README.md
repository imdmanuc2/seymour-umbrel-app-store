# SBP-075.5.1 — Registration Runtime Normalization Hardening

Hardens the legacy Nexus registration normalization layer so partial
runtime observations do not prevent registration payload creation.

Optional runtime observation fields are treated defensively while
preserving registration identity, BCH compatibility, managed-runtime
projection, and delivery semantics.
