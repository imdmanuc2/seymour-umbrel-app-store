#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "seymour-blockchain-manager/data/web/bch_runtime_probe.py"
TELEMETRY = ROOT / "seymour-blockchain-manager/data/web/telemetry.py"

text = RUNTIME.read_text()

if "BCH_RUNTIME_CACHE_TTL_SECONDS" not in text:
    old = "import json, os, socket\n"
    new = "import copy, json, os, socket, threading, time\n"
    if old not in text:
        raise SystemExit("runtime import anchor not found")
    text = text.replace(old, new, 1)

    anchor = 'BCH_STATUS_URL=os.environ.get("BCH_STATUS_URL","http://seymour-bch-node_status_1:8080/api/status")\n'
    if anchor not in text:
        raise SystemExit("BCH_STATUS_URL anchor not found")

    defs = (
        "\nBCH_RUNTIME_CACHE_TTL_SECONDS=max(\n"
        "    5,\n"
        "    int(os.environ.get(\"BCH_RUNTIME_CACHE_TTL_SECONDS\",\"30\")),\n"
        ")\n\n"
        "_CACHE_LOCK=threading.Lock()\n"
        "_CACHE_VALUE=None\n"
        "_CACHE_AT=0.0\n"
        "_LAST_GOOD=None\n"
        "_LAST_GOOD_AT=0.0\n"
        "_REFRESHING=False\n\n"
    )
    text = text.replace(anchor, anchor + defs, 1)

if "def _probe_uncached()" not in text:
    anchor = "def probe()->dict[str,Any]:\n"
    if anchor not in text:
        raise SystemExit("probe() anchor not found")
    text = text.replace(anchor, "def _probe_uncached()->dict[str,Any]:\n", 1)

if "def _sync_detail(" not in text:
    text = text.rstrip() + "\n\n" + '\ndef _sync_detail(payload:dict[str,Any])->dict[str,Any]:\n    rpc=payload.get("rpc") if isinstance(payload.get("rpc"),dict) else {}\n    probe=rpc.get("probe") if isinstance(rpc.get("probe"),dict) else {}\n    op=payload.get("operationalState") if isinstance(payload.get("operationalState"),dict) else {}\n    return {\n        "height":probe.get("height"),\n        "headers":probe.get("headers"),\n        "progressPercent":probe.get("progressPercent"),\n        "verificationProgress":probe.get("verificationProgress"),\n        "initialBlockDownload":(\n            probe.get("initialBlockDownload")\n            if probe.get("initialBlockDownload") is not None\n            else op.get("initialBlockDownload")\n        ),\n        "peers":probe.get("peers"),\n        "bestBlockHash":probe.get("bestBlockHash"),\n        "difficulty":probe.get("difficulty"),\n    }\n\n\ndef _complete_sync(payload:dict[str,Any])->bool:\n    detail=_sync_detail(payload)\n    return (\n        detail["height"] is not None\n        and detail["headers"] is not None\n        and (\n            detail["progressPercent"] is not None\n            or detail["verificationProgress"] is not None\n        )\n    )\n\n\ndef _with_last_good(payload,last_good,last_good_at):\n    result=copy.deepcopy(payload)\n    now=time.monotonic()\n\n    if _complete_sync(result):\n        result["telemetryFresh"]=True\n        result["telemetryStale"]=False\n        result["telemetryAgeSeconds"]=0.0\n        result["telemetrySource"]="live"\n        return result\n\n    if not isinstance(last_good,dict):\n        result["telemetryFresh"]=False\n        result["telemetryStale"]=False\n        result["telemetryAgeSeconds"]=None\n        result["telemetrySource"]="unavailable"\n        return result\n\n    previous=_sync_detail(last_good)\n\n    rpc=result.get("rpc")\n    if not isinstance(rpc,dict):\n        rpc={}\n        result["rpc"]=rpc\n\n    probe=rpc.get("probe")\n    if not isinstance(probe,dict):\n        probe={}\n        rpc["probe"]=probe\n\n    for key in (\n        "height","headers","progressPercent","verificationProgress",\n        "initialBlockDownload","peers","bestBlockHash","difficulty",\n    ):\n        if probe.get(key) is None and previous.get(key) is not None:\n            probe[key]=previous[key]\n\n    op=result.get("operationalState")\n    if not isinstance(op,dict):\n        op={}\n        result["operationalState"]=op\n\n    if op.get("verificationProgress") is None and previous.get("verificationProgress") is not None:\n        op["verificationProgress"]=previous["verificationProgress"]\n\n    if op.get("initialBlockDownload") is None and previous.get("initialBlockDownload") is not None:\n        op["initialBlockDownload"]=previous["initialBlockDownload"]\n\n    result["telemetryFresh"]=False\n    result["telemetryStale"]=True\n    result["telemetryAgeSeconds"]=round(max(0.0,now-last_good_at),3)\n    result["telemetrySource"]="last-known-good"\n    return result\n\n\ndef probe(*,force:bool=False)->dict[str,Any]:\n    global _CACHE_VALUE,_CACHE_AT,_LAST_GOOD,_LAST_GOOD_AT,_REFRESHING\n\n    now=time.monotonic()\n\n    with _CACHE_LOCK:\n        if (\n            not force\n            and isinstance(_CACHE_VALUE,dict)\n            and (now-_CACHE_AT)<BCH_RUNTIME_CACHE_TTL_SECONDS\n        ):\n            cached=copy.deepcopy(_CACHE_VALUE)\n            cached["telemetryCacheHit"]=True\n            cached["telemetryCacheAgeSeconds"]=round(max(0.0,now-_CACHE_AT),3)\n            return cached\n\n        if _REFRESHING and isinstance(_CACHE_VALUE,dict):\n            cached=copy.deepcopy(_CACHE_VALUE)\n            cached["telemetryCacheHit"]=True\n            cached["telemetryRefreshInProgress"]=True\n            cached["telemetryCacheAgeSeconds"]=round(max(0.0,now-_CACHE_AT),3)\n            return cached\n\n        _REFRESHING=True\n\n    try:\n        fresh=_probe_uncached()\n        completed=_complete_sync(fresh)\n\n        with _CACHE_LOCK:\n            if completed:\n                _LAST_GOOD=copy.deepcopy(fresh)\n                _LAST_GOOD_AT=time.monotonic()\n\n            projected=_with_last_good(fresh,_LAST_GOOD,_LAST_GOOD_AT)\n            projected["telemetryCacheHit"]=False\n            projected["telemetryRefreshInProgress"]=False\n            projected["telemetryCacheAgeSeconds"]=0.0\n\n            _CACHE_VALUE=copy.deepcopy(projected)\n            _CACHE_AT=time.monotonic()\n            return copy.deepcopy(projected)\n    finally:\n        with _CACHE_LOCK:\n            _REFRESHING=False\n' + "\n"

RUNTIME.write_text(text)

text = TELEMETRY.read_text()
if '"telemetryFresh": runtime.get("telemetryFresh")' not in text:
    anchor = '        "runtimeStateReason": operational_state.get("reason"),\n'
    if anchor not in text:
        raise SystemExit("telemetry projection anchor not found")

    replacement = (
        anchor
        + '        "telemetryFresh": runtime.get("telemetryFresh"),\n'
        + '        "telemetryStale": runtime.get("telemetryStale"),\n'
        + '        "telemetryAgeSeconds": runtime.get("telemetryAgeSeconds"),\n'
        + '        "telemetrySource": runtime.get("telemetrySource"),\n'
        + '        "telemetryCacheHit": runtime.get("telemetryCacheHit"),\n'
        + '        "telemetryCacheAgeSeconds": runtime.get("telemetryCacheAgeSeconds"),\n'
    )
    text = text.replace(anchor, replacement, 1)

TELEMETRY.write_text(text)
print("SBP-061 runtime RPC load-control patch: PASS")
