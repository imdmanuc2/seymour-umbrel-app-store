#!/bin/sh
set -eu

DATA_DIR="${BCH_DATA_DIR:-/data}"
CONFIG_DIR="${BCH_CONFIG_DIR:-/generated}"
STATE_DIR="${BCH_STATE_DIR:-/state}"

mkdir -p \
  "$DATA_DIR" \
  "$CONFIG_DIR" \
  "$STATE_DIR"

PLAN_FILE="$STATE_DIR/provisioning-plan.json"
SECRETS_FILE="$STATE_DIR/rpc-secrets.json"
CONFIG_FILE="$CONFIG_DIR/bitcoin.conf"

RPC_USER="${BCH_RPC_USER:-seymour_rpc}"
RPC_PASSWORD="${BCH_RPC_PASSWORD:-change-me-before-production}"
PRUNE="${BCH_PRUNE:-0}"
TXINDEX="${BCH_TXINDEX:-1}"

if [ -f "$SECRETS_FILE" ]; then
  RPC_USER="$(
    python3 -c '
import json,sys
print(json.load(open(sys.argv[1]))["rpcUser"])
' "$SECRETS_FILE"
  )"

  RPC_PASSWORD="$(
    python3 -c '
import json,sys
print(json.load(open(sys.argv[1]))["rpcPassword"])
' "$SECRETS_FILE"
  )"
fi

if [ -f "$PLAN_FILE" ]; then
  PRUNE="$(
    python3 -c '
import json,sys
print(json.load(open(sys.argv[1]))["runtime"]["prune"])
' "$PLAN_FILE"
  )"

  TXINDEX="$(
    python3 -c '
import json,sys
print(1 if json.load(open(sys.argv[1]))["runtime"]["txindex"] else 0)
' "$PLAN_FILE"
  )"
fi

cat > "$CONFIG_FILE" <<EOF
server=1
listen=1
daemon=0
printtoconsole=1

datadir=${DATA_DIR}

rpcbind=0.0.0.0
rpcallowip=172.16.0.0/12
rpcallowip=10.0.0.0/8
rpcallowip=192.168.0.0/16
rpcuser=${RPC_USER}
rpcpassword=${RPC_PASSWORD}
rpcport=8332

port=8333
txindex=${TXINDEX}
prune=${PRUNE}

zmqpubrawblock=tcp://0.0.0.0:28332
zmqpubrawtx=tcp://0.0.0.0:28333
EOF

chmod 600 "$CONFIG_FILE"

exec bitcoind \
  -conf="$CONFIG_FILE" \
  -datadir="$DATA_DIR"
