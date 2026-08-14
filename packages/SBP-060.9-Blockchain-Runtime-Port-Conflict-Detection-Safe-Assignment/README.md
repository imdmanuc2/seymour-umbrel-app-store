# SBP-060.9 — Blockchain Runtime Port Conflict Detection & Safe Assignment

Adds provider-neutral host-port conflict detection to the blockchain recovery
engine. It never stops an existing owner automatically.

Live discovery that motivated this package:
- Seymour BCH owns host TCP 8333
- retro-mike BCH owns host TCP 8334
- 8335+ are currently free
- Seymour BTC also requested host TCP 8333

The package also changes Seymour BTC's source Compose to use
`${BTC_P2P_HOST_PORT:-8335}:8333`, preserving Bitcoin's internal P2P port 8333.
