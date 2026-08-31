#!/bin/sh

APP_DATA_DIR="${APP_DATA_DIR:-/home/umbrel/umbrel/app-data/seymour-nexus-command-center}"
STATE_FILE="${NEXUS_DISCOVERY_STATE_FILE:-$APP_DATA_DIR/data/runtime/nexus-local-discovery.json}"
PID_FILE="${NEXUS_DISCOVERY_PID_FILE:-$APP_DATA_DIR/data/runtime/nexus-discovery-advertiser.pid}"
SERVICE_TYPE="_seymour-nexus._tcp"
POLL_SECONDS=5

publisher_pid=""

cleanup()
{
    if [ -n "$publisher_pid" ] && kill -0 "$publisher_pid" 2>/dev/null; then
        kill "$publisher_pid" 2>/dev/null || true
        wait "$publisher_pid" 2>/dev/null || true
    fi

    rm -f "$PID_FILE"
}

trap cleanup EXIT
trap 'cleanup; exit 0' INT TERM HUP

mkdir -p "$(dirname "$PID_FILE")" || exit 1
printf '%s\n' "$$" > "$PID_FILE" || exit 1

while :
do
    desired="off"
    name=""
    port=""

    if [ -r "$STATE_FILE" ]; then
        parsed="$(
            python3 - "$STATE_FILE" 2>/dev/null <<'PY'
import json
import sys

try:
    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        state = json.load(handle)

    if (
        state.get("version") == 1
        and state.get("enabled") is True
        and isinstance(state.get("name"), str)
        and state["name"].strip()
        and isinstance(state.get("port"), int)
        and 1 <= state["port"] <= 65535
    ):
        print("on")
        print(state["name"].strip())
        print(state["port"])
except Exception:
    pass
PY
        )"

        desired="$(printf '%s\n' "$parsed" | sed -n '1p')"
        name="$(printf '%s\n' "$parsed" | sed -n '2p')"
        port="$(printf '%s\n' "$parsed" | sed -n '3p')"
    fi

    if [ "$desired" = "on" ]; then
        if [ -z "$publisher_pid" ] || ! kill -0 "$publisher_pid" 2>/dev/null; then
            avahi-publish-service \
                "$name" \
                "$SERVICE_TYPE" \
                "$port" \
                >/dev/null 2>&1 &

            publisher_pid=$!
        fi
    else
        if [ -n "$publisher_pid" ] && kill -0 "$publisher_pid" 2>/dev/null; then
            kill "$publisher_pid" 2>/dev/null || true
            wait "$publisher_pid" 2>/dev/null || true
        fi

        publisher_pid=""
    fi

    sleep "$POLL_SECONDS"
done
