#!/bin/sh
set -eu
mkdir -p /data /generated
cat > /generated/bitcoin.conf <<EOF
server=1
listen=1
daemon=0
printtoconsole=1
datadir=/data
rpcbind=0.0.0.0
rpcallowip=172.16.0.0/12
rpcuser=${BCH_RPC_USER}
rpcpassword=${BCH_RPC_PASSWORD}
rpcport=8332
port=8333
txindex=1
zmqpubrawblock=tcp://0.0.0.0:28332
zmqpubrawtx=tcp://0.0.0.0:28333
EOF
chmod 600 /generated/bitcoin.conf
exec bitcoind -conf=/generated/bitcoin.conf -datadir=/data
