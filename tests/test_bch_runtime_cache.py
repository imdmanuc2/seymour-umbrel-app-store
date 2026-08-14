from __future__ import annotations

import copy
import time

import bch_runtime_probe as module


def good():
    return {
        "container": {
            "running": True,
            "health": "healthy",
        },
        "rpc": {
            "reachable": True,
            "probe": {
                "reachable": True,
                "healthy": True,
                "height": 840043,
                "headers": 963872,
                "progressPercent": 93.2426,
                "verificationProgress": 0.932426,
                "initialBlockDownload": True,
                "peers": 8,
            },
        },
        "operationalState": {
            "state": "syncing",
            "running": True,
            "rpcReachable": True,
            "rpcHealthy": True,
            "verificationProgress": 0.932426,
            "initialBlockDownload": True,
        },
        "lifecycleStatus": "syncing",
    }


def slow():
    return {
        "container": {
            "running": True,
            "health": "healthy",
        },
        "rpc": {
            "reachable": True,
            "probe": {
                "reachable": True,
                "healthy": True,
                "height": None,
                "headers": None,
                "progressPercent": None,
                "verificationProgress": None,
                "initialBlockDownload": None,
                "peers": None,
            },
        },
        "operationalState": {
            "state": "degraded",
            "running": True,
            "rpcReachable": True,
            "rpcHealthy": True,
            "verificationProgress": None,
            "initialBlockDownload": None,
        },
        "lifecycleStatus": "degraded",
    }


# ------------------------------------------------------------
# Complete telemetry detection
# ------------------------------------------------------------

known = good()

assert module._complete_sync(
    known
) is True

print(
    "SBP-061 complete telemetry detection: PASS"
)


# ------------------------------------------------------------
# Last-known-good continuity
# ------------------------------------------------------------

held = module._with_last_good(
    slow(),
    known,
    time.monotonic(),
)

probe = held["rpc"]["probe"]
op = held["operationalState"]

assert held["telemetryStale"] is True
assert held["telemetrySource"] == "last-known-good"

assert probe["height"] == 840043
assert probe["headers"] == 963872
assert probe["progressPercent"] == 93.2426
assert probe["peers"] == 8

assert op["state"] == "syncing"
assert op["rpcReachable"] is True
assert op["rpcHealthy"] is True
assert held["lifecycleStatus"] == "syncing"

print(
    "SBP-061 slow telemetry continuity: PASS"
)


# ------------------------------------------------------------
# Fresh cache hit
# ------------------------------------------------------------

module._CACHE_VALUE = copy.deepcopy(known)
module._CACHE_VALUE["telemetryFresh"] = True
module._CACHE_VALUE["telemetryStale"] = False
module._CACHE_VALUE["telemetrySource"] = "live"

module._CACHE_AT = time.monotonic()
module._REFRESHING = False

cached = module.probe()

assert cached["telemetryCacheHit"] is True
assert cached["rpc"]["probe"]["height"] == 840043

print(
    "SBP-061 fresh cache hit: PASS"
)


# ------------------------------------------------------------
# Expired cache is stale-while-revalidate, never blocking
# ------------------------------------------------------------

module._CACHE_VALUE = copy.deepcopy(known)
module._CACHE_VALUE["telemetryFresh"] = True
module._CACHE_VALUE["telemetryStale"] = False
module._CACHE_VALUE["telemetrySource"] = "live"

module._CACHE_AT = (
    time.monotonic()
    - module.BCH_RUNTIME_CACHE_TTL_SECONDS
    - 1
)

# Prevent this unit test from actually launching a real refresh.
module._REFRESHING = True

stale = module.probe()

assert stale["telemetryCacheHit"] is True
assert stale["telemetryFresh"] is False
assert stale["telemetryStale"] is True
assert stale["telemetrySource"] == "cache-refreshing"
assert stale["rpc"]["probe"]["height"] == 840043

module._REFRESHING = False

print(
    "SBP-061 stale-while-revalidate: PASS"
)

print(
    "SBP-061 final regression suite: PASS"
)
