#!/usr/bin/env bash
set -e

create_app () {
  APP_ID="$1"
  NAME="$2"
  TAGLINE="$3"
  CATEGORY="$4"
  PORT="$5"

  mkdir -p "$APP_ID"

  cat > "$APP_ID/umbrel-app.yml" <<APP
manifestVersion: 1
id: $APP_ID
name: $NAME
tagline: $TAGLINE
icon: https://raw.githubusercontent.com/getumbrel/umbrel-apps/master/bitcoin/icon.svg
category: $CATEGORY
version: "0.1.0"
port: $PORT
description: >-
  $TAGLINE
developer: Seymour Mining Suite
website: https://github.com/imdmanuc2/seymour-umbrel-app-store
submitter: Seymour Mitchell
submission: https://github.com/imdmanuc2/seymour-umbrel-app-store
repo: https://github.com/imdmanuc2/seymour-umbrel-app-store
support: https://github.com/imdmanuc2/seymour-umbrel-app-store/issues
gallery: []
releaseNotes: >-
  Initial placeholder app for the Seymour Mining Suite.
dependencies: []
path: ""
defaultUsername: ""
defaultPassword: ""
APP

  cat > "$APP_ID/docker-compose.yml" <<APP
services:
  app_proxy:
    environment:
      APP_HOST: ${APP_ID}_web_1
      APP_PORT: 80

  web:
    image: nginx:alpine
    restart: on-failure
APP
}

create_app "seymour-nexus-command-center" "Nexus Command Center" "Infrastructure command center for mining, nodes, pools, and miners" "Development" "8560"
create_app "seymour-miningcore" "Seymour MiningCore" "MiningCore pool engine for solo and public mining" "Development" "8561"
create_app "seymour-bitcoin-node" "Bitcoin Node" "Bitcoin full node for solo and public mining" "Bitcoin" "8562"
create_app "seymour-bch-node" "Bitcoin Cash Node" "Bitcoin Cash full node for BCH mining" "Bitcoin" "8563"
create_app "seymour-postgres" "Postgres" "Database backend for MiningCore and Nexus" "Development" "8564"
create_app "seymour-redis" "Redis" "Cache and queue backend for mining services" "Development" "8565"
create_app "seymour-dozzle" "Dozzle" "Simple Docker log viewer" "Development" "8566"
create_app "seymour-uptime-kuma" "Uptime Kuma" "Uptime and service monitoring" "Development" "8567"
create_app "seymour-backup-manager" "Backup Manager" "Backup configs, wallets, pool files, and data" "Development" "8568"
