#!/bin/sh
set -eu

DATA_DIR="${BTC_DATA_DIR:-/data}"
CONFIG_DIR="${BTC_CONFIG_DIR:-/generated}"
STATE_DIR="${BTC_STATE_DIR:-/state}"
NETWORK="${BTC_NETWORK:-main}"

mkdir -p \
  "$DATA_DIR" \
  "$CONFIG_DIR" \
  "$STATE_DIR"

CONFIG_FILE="$CONFIG_DIR/bitcoin.conf"

RPC_USER="${BTC_RPC_USER:-seymour_rpc}"
RPC_PASSWORD="${BTC_RPC_PASSWORD:-change-me-before-production}"
PRUNE="${BTC_PRUNE:-0}"
TXINDEX="${BTC_TXINDEX:-0}"

case "$NETWORK" in
  main)
    CHAIN_ARG=""
    SECTION="main"
    RPC_PORT="${BTC_RPC_PORT:-8332}"
    P2P_PORT="${BTC_P2P_PORT:-8333}"
    ;;
  regtest)
    CHAIN_ARG="-regtest"
    SECTION="regtest"
    RPC_PORT="${BTC_RPC_PORT:-18443}"
    P2P_PORT="${BTC_P2P_PORT:-18444}"
    ;;
  testnet4)
    CHAIN_ARG="-testnet4"
    SECTION="testnet4"
    RPC_PORT="${BTC_RPC_PORT:-48332}"
    P2P_PORT="${BTC_P2P_PORT:-48333}"
    ;;
  *)
    echo "Unsupported BTC_NETWORK: $NETWORK" >&2
    exit 1
    ;;
esac

cat > "$CONFIG_FILE" <<CFG
server=1
listen=1
daemon=0
printtoconsole=1

datadir=${DATA_DIR}

rpcuser=${RPC_USER}
rpcpassword=${RPC_PASSWORD}

txindex=${TXINDEX}
prune=${PRUNE}

[${SECTION}]
rpcbind=0.0.0.0
rpcallowip=172.16.0.0/12
rpcallowip=10.0.0.0/8
rpcallowip=192.168.0.0/16
rpcport=${RPC_PORT}
port=${P2P_PORT}

zmqpubrawblock=tcp://0.0.0.0:28332
zmqpubrawtx=tcp://0.0.0.0:28333
CFG

chmod 600 "$CONFIG_FILE"

if [ -n "$CHAIN_ARG" ]; then
  exec bitcoind \
    -conf="$CONFIG_FILE" \
    -datadir="$DATA_DIR" \
    "$CHAIN_ARG" \
    "$@"
else
  exec bitcoind \
    -conf="$CONFIG_FILE" \
    -datadir="$DATA_DIR" \
    "$@"
fi
