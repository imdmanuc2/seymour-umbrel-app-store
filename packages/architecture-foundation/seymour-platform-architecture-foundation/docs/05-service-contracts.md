# Service Contracts

Every product publishes structured contracts describing the services it provides.

## Minimum contract fields

- service identifier
- product identifier
- instance identifier
- version
- health status
- endpoints
- authentication reference
- capabilities
- observed timestamp

## Example blockchain contract

```json
{
  "service": "bitcoin-rpc",
  "product": "seymour-blockchain-platform",
  "implementation": "bitcoin-core",
  "network": "bitcoin-mainnet",
  "version": "recommended",
  "status": "healthy",
  "endpoints": {
    "rpc": "rpc://service-registry/bitcoin-rpc",
    "zmqRawBlock": "tcp://service-registry/bitcoin-zmq-rawblock"
  }
}
```

Consumers resolve services through contracts rather than hardcoded container names or private paths.
