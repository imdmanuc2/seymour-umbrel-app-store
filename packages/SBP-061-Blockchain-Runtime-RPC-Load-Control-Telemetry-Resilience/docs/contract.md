# Telemetry continuity contract

- Expensive BCH runtime probing is cached process-wide.
- Cache TTL defaults to 30 seconds.
- Concurrent callers reuse the active cached snapshot.
- Transient incomplete probes do not erase last-known-good height, headers,
  progress, peers, or IBD state.
- Dashboard telemetry exposes freshness/staleness metadata.
- `/api/runtime/bch-rpc` stays an explicit uncached diagnostic endpoint.
