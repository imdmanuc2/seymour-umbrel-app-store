from __future__ import annotations
import copy, json, os, socket, threading, time
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import quote
from bch_rpc_probe import probe as probe_bch_rpc
from runtime_state import normalize_runtime_state

DOCKER_SOCKET=Path(os.environ.get("DOCKER_SOCKET","/var/run/docker.sock"))
BCH_NODE_CONTAINER=os.environ.get("BCH_NODE_CONTAINER","seymour-bch-node_node_1")
BCH_HEALTH_URL=os.environ.get("BCH_HEALTH_URL","http://seymour-bch-node_status_1:8080/api/health")
BCH_STATUS_URL=os.environ.get("BCH_STATUS_URL","http://seymour-bch-node_status_1:8080/api/status")

BCH_RUNTIME_CACHE_TTL_SECONDS=max(
    5,
    int(os.environ.get("BCH_RUNTIME_CACHE_TTL_SECONDS","30")),
)

_CACHE_LOCK=threading.Lock()
_CACHE_VALUE=None
_CACHE_AT=0.0
_LAST_GOOD=None
_LAST_GOOD_AT=0.0
_REFRESHING=False


def _decode_chunked(body: bytes) -> bytes:
 out = bytearray()
 pos = 0

 while pos < len(body):
  line_end = body.find(b"\r\n", pos)
  if line_end == -1:
   break

  size_line = body[pos:line_end].split(b";", 1)[0]

  try:
   size = int(size_line, 16)
  except ValueError:
   break

  pos = line_end + 2

  if size == 0:
   break

  out.extend(
   body[pos:pos + size]
  )

  pos += size + 2

 return bytes(out)


def _decode(raw: bytes):
 head,_,body=raw.partition(b"\r\n\r\n")

 try:
  code=int(
   head.splitlines()[0].split()[1]
  )
 except Exception:
  code=0

 headers = {}

 for line in head.splitlines()[1:]:
  if b":" not in line:
   continue

  key, value = line.split(b":", 1)

  headers[
   key.decode(
    "latin-1"
   ).strip().lower()
  ] = value.decode(
   "latin-1"
  ).strip().lower()

 if (
  headers.get("transfer-encoding")
  == "chunked"
 ):
  body = _decode_chunked(body)

 return code,body

def docker_container_inspect(name: str=BCH_NODE_CONTAINER)->dict[str,Any]:
 out={"available":False,"found":False,"name":name,"status":"docker-unavailable","running":False,"health":"unknown","error":None}
 if not DOCKER_SOCKET.exists(): out["error"]=f"Docker socket not found: {DOCKER_SOCKET}"; return out
 try:
  s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.settimeout(3); s.connect(str(DOCKER_SOCKET))
  path=f"/containers/{quote(name,safe='')}/json"
  s.sendall(f"GET {path} HTTP/1.1\r\nHost: docker\r\nConnection: close\r\n\r\n".encode())
  chunks=[]
  while True:
   c=s.recv(65536)
   if not c: break
   chunks.append(c)
  s.close(); code,body=_decode(b''.join(chunks)); out["available"]=True
  if code==404: out["status"]="not-found"; return out
  if code!=200: out["status"]="docker-error"; out["error"]=f"Docker API HTTP {code}"; return out
  payload=json.loads(body.decode()); state=payload.get("State") if isinstance(payload.get("State"),dict) else {}; health=state.get("Health") if isinstance(state.get("Health"),dict) else {}
  out.update({"found":True,"status":str(state.get("Status") or "unknown"),"running":bool(state.get("Running")),"health":str(health.get("Status") or "none"),"containerId":str(payload.get("Id") or '')[:12] or None}); return out
 except Exception as exc: out["error"]=str(exc); return out

def http_json(
    url: str,
    timeout: int = 8,
) -> dict[str, Any]:
    out = {
        "url": url,
        "reachable": False,
        "httpStatus": None,
        "payload": None,
        "error": None,
    }
    try:
        with request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode()
            out["httpStatus"] = int(response.status)
            out["reachable"] = True
            try:
                out["payload"] = json.loads(raw)
            except json.JSONDecodeError:
                out["payload"] = {"raw": raw}
    except error.HTTPError as exc:
        out["httpStatus"] = int(exc.code)
        out["error"] = f"HTTP {exc.code}: {exc.reason}"
        try:
            raw = exc.read().decode()
            out["payload"] = json.loads(raw) if raw else None
        except Exception:
            pass
    except Exception as exc:
        out["error"] = str(exc)
    return out

def _probe_uncached()->dict[str,Any]:
 container=docker_container_inspect()
 legacy_health=http_json(BCH_HEALTH_URL, timeout=8)
 legacy_status=http_json(BCH_STATUS_URL, timeout=25)
 status_payload=(
  legacy_status.get("payload")
  if isinstance(legacy_status.get("payload"),dict)
  else {}
 )

 rpc_reachable=bool(
  status_payload.get("rpcReachable")
  if status_payload.get("rpcReachable") is not None
  else legacy_status.get("reachable")
 )

 rpc_healthy=bool(
  status_payload.get("rpcHealthy")
  if status_payload.get("rpcHealthy") is not None
  else status_payload.get("healthy")
 )

 verification=status_payload.get(
  "verificationProgress"
 )

 rpc_probe={
  "reachable":rpc_reachable,
  "healthy":rpc_healthy,
  "height":status_payload.get("blocks"),
  "headers":status_payload.get("headers"),
  "progressPercent":(
   float(verification)*100.0
   if isinstance(verification,(int,float))
   else None
  ),
  "verificationProgress":verification,
  "initialBlockDownload":status_payload.get(
   "initialBlockDownload"
  ),
  "peers":status_payload.get("peers"),
  "source":"bch-status-service",
 }

 installed=bool(container.get("found"))
 running=bool(container.get("running"))
 rpc=bool(rpc_reachable and rpc_healthy)
 lifecycle="not-installed" if not installed else "stopped" if not running else "running" if rpc else "degraded"
 result = {"providerId":"bitcoin-cash-mainnet","appId":"seymour-bch-node","installed":installed,"running":running,"lifecycleStatus":lifecycle,"container":container,"rpc":{"reachable":rpc,"probe":rpc_probe,"health":legacy_health,"status":legacy_status}}
 result["operationalState"] = normalize_runtime_state(result)
 status_payload = legacy_status.get("payload") if isinstance(legacy_status.get("payload"),dict) else {}
 status_state = str(status_payload.get("status") or "").strip().lower()
 if running and not rpc and status_state in {"starting","verifying","warming-up","recovering"}:
  result["operationalState"] = {**result["operationalState"],"state":"starting","reason":"Runtime is verifying or warming existing blockchain data."}
 result["lifecycleStatus"] = result["operationalState"]["state"]
 return result


def _sync_detail(payload:dict[str,Any])->dict[str,Any]:
    rpc=payload.get("rpc") if isinstance(payload.get("rpc"),dict) else {}
    probe=rpc.get("probe") if isinstance(rpc.get("probe"),dict) else {}
    op=payload.get("operationalState") if isinstance(payload.get("operationalState"),dict) else {}
    return {
        "height":probe.get("height"),
        "headers":probe.get("headers"),
        "progressPercent":probe.get("progressPercent"),
        "verificationProgress":probe.get("verificationProgress"),
        "initialBlockDownload":(
            probe.get("initialBlockDownload")
            if probe.get("initialBlockDownload") is not None
            else op.get("initialBlockDownload")
        ),
        "peers":probe.get("peers"),
        "bestBlockHash":probe.get("bestBlockHash"),
        "difficulty":probe.get("difficulty"),
    }


def _complete_sync(payload:dict[str,Any])->bool:
    detail=_sync_detail(payload)
    return (
        detail["height"] is not None
        and detail["headers"] is not None
        and (
            detail["progressPercent"] is not None
            or detail["verificationProgress"] is not None
        )
    )


def _with_last_good(payload,last_good,last_good_at):
    result=copy.deepcopy(payload)
    now=time.monotonic()

    if _complete_sync(result):
        result["telemetryFresh"]=True
        result["telemetryStale"]=False
        result["telemetryAgeSeconds"]=0.0
        result["telemetrySource"]="live"
        return result

    if not isinstance(last_good,dict):
        result["telemetryFresh"]=False
        result["telemetryStale"]=False
        result["telemetryAgeSeconds"]=None
        result["telemetrySource"]="unavailable"
        return result

    previous=_sync_detail(last_good)

    rpc=result.get("rpc")
    if not isinstance(rpc,dict):
        rpc={}
        result["rpc"]=rpc

    probe=rpc.get("probe")
    if not isinstance(probe,dict):
        probe={}
        rpc["probe"]=probe

    for key in (
        "height","headers","progressPercent","verificationProgress",
        "initialBlockDownload","peers","bestBlockHash","difficulty",
    ):
        if probe.get(key) is None and previous.get(key) is not None:
            probe[key]=previous[key]

    op=result.get("operationalState")
    if not isinstance(op,dict):
        op={}
        result["operationalState"]=op

    if op.get("verificationProgress") is None and previous.get("verificationProgress") is not None:
        op["verificationProgress"]=previous["verificationProgress"]

    if op.get("initialBlockDownload") is None and previous.get("initialBlockDownload") is not None:
        op["initialBlockDownload"]=previous["initialBlockDownload"]

    #
    # Detailed BCH telemetry may legitimately time out during
    # initial block download. If the current container is still
    # running and the lightweight RPC/status path says RPC is
    # reachable, a slow detailed telemetry refresh must not
    # downgrade a previously healthy runtime.
    #
    current_container = (
        result.get("container")
        if isinstance(result.get("container"), dict)
        else {}
    )

    current_rpc = (
        result.get("rpc")
        if isinstance(result.get("rpc"), dict)
        else {}
    )

    previous_op = (
        last_good.get("operationalState")
        if isinstance(
            last_good.get("operationalState"),
            dict,
        )
        else {}
    )

    current_probe = (
        current_rpc.get("probe")
        if isinstance(current_rpc.get("probe"), dict)
        else {}
    )

    rpc_reachable = bool(
        current_rpc.get("reachable")
        or current_probe.get("reachable")
    )

    if (
        bool(current_container.get("running"))
        and rpc_reachable
        and previous_op.get("state")
        in {"running", "syncing", "starting"}
    ):
        previous_state = previous_op.get("state")

        op["state"] = previous_state
        op["running"] = True
        op["rpcReachable"] = True

        previous_rpc_healthy = previous_op.get(
            "rpcHealthy"
        )

        if previous_rpc_healthy is not None:
            op["rpcHealthy"] = previous_rpc_healthy

        op["reason"] = (
            "Runtime RPC is reachable; detailed blockchain "
            "telemetry is temporarily stale."
        )

        result["lifecycleStatus"] = previous_state

    result["telemetryFresh"]=False
    result["telemetryStale"]=True
    result["telemetryAgeSeconds"]=round(max(0.0,now-last_good_at),3)
    result["telemetrySource"]="last-known-good"
    return result


def _refresh_cache_background()->None:
    global _CACHE_VALUE,_CACHE_AT,_LAST_GOOD,_LAST_GOOD_AT,_REFRESHING

    try:
        fresh=_probe_uncached()
        completed=_complete_sync(fresh)

        with _CACHE_LOCK:
            if completed:
                _LAST_GOOD=copy.deepcopy(fresh)
                _LAST_GOOD_AT=time.monotonic()

            projected=_with_last_good(
                fresh,
                _LAST_GOOD,
                _LAST_GOOD_AT,
            )

            projected["telemetryCacheHit"]=False
            projected["telemetryRefreshInProgress"]=False
            projected["telemetryCacheAgeSeconds"]=0.0

            _CACHE_VALUE=copy.deepcopy(projected)
            _CACHE_AT=time.monotonic()

    finally:
        with _CACHE_LOCK:
            _REFRESHING=False


def _stale_cache_payload(
    cached:dict[str,Any],
    age:float,
)->dict[str,Any]:
    result=copy.deepcopy(cached)

    result["telemetryFresh"]=False
    result["telemetryStale"]=True
    result["telemetrySource"]="cache-refreshing"
    result["telemetryCacheHit"]=True
    result["telemetryRefreshInProgress"]=True
    result["telemetryCacheAgeSeconds"]=round(
        max(0.0,age),
        3,
    )
    result["telemetryAgeSeconds"]=round(
        max(
            float(result.get("telemetryAgeSeconds") or 0.0),
            age,
        ),
        3,
    )

    return result


def probe(*,force:bool=False)->dict[str,Any]:
    global _CACHE_VALUE,_CACHE_AT,_REFRESHING

    now=time.monotonic()

    with _CACHE_LOCK:
        cache_exists=isinstance(
            _CACHE_VALUE,
            dict,
        )

        age=(
            max(0.0,now-_CACHE_AT)
            if cache_exists
            else 0.0
        )

        if (
            not force
            and cache_exists
            and age<BCH_RUNTIME_CACHE_TTL_SECONDS
        ):
            cached=copy.deepcopy(_CACHE_VALUE)
            cached["telemetryCacheHit"]=True
            cached["telemetryRefreshInProgress"]=False
            cached["telemetryCacheAgeSeconds"]=round(
                age,
                3,
            )
            return cached

        if (
            not force
            and cache_exists
        ):
            if not _REFRESHING:
                _REFRESHING=True

                threading.Thread(
                    target=_refresh_cache_background,
                    name="bch-runtime-refresh",
                    daemon=True,
                ).start()

            return _stale_cache_payload(
                _CACHE_VALUE,
                age,
            )

        if _REFRESHING and cache_exists:
            return _stale_cache_payload(
                _CACHE_VALUE,
                age,
            )

        _REFRESHING=True

        if not force and not cache_exists:
            threading.Thread(
                target=_refresh_cache_background,
                name="bch-runtime-initial-refresh",
                daemon=True,
            ).start()

            return {
                "providerId":"bitcoin-cash-mainnet",
                "appId":"seymour-bch-node",
                "installed":True,
                "running":True,
                "lifecycleStatus":"starting",
                "operationalState":{
                    "state":"starting",
                    "reason":"Telemetry snapshot is initializing.",
                },
                "rpc":{
                    "probe":{},
                },
                "telemetryFresh":False,
                "telemetryStale":False,
                "telemetryAgeSeconds":None,
                "telemetrySource":"initializing",
                "telemetryCacheHit":False,
                "telemetryRefreshInProgress":True,
                "telemetryCacheAgeSeconds":None,
            }

    # Explicit forced probes may block.
    try:
        fresh=_probe_uncached()
        completed=_complete_sync(fresh)

        with _CACHE_LOCK:
            global _LAST_GOOD,_LAST_GOOD_AT

            if completed:
                _LAST_GOOD=copy.deepcopy(fresh)
                _LAST_GOOD_AT=time.monotonic()

            projected=_with_last_good(
                fresh,
                _LAST_GOOD,
                _LAST_GOOD_AT,
            )

            projected["telemetryCacheHit"]=False
            projected["telemetryRefreshInProgress"]=False
            projected["telemetryCacheAgeSeconds"]=0.0

            _CACHE_VALUE=copy.deepcopy(projected)
            _CACHE_AT=time.monotonic()

            return copy.deepcopy(projected)

    finally:
        with _CACHE_LOCK:
            _REFRESHING=False

