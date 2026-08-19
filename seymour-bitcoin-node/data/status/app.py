from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import base64, json, os, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RPC_HOST=os.environ.get("BTC_RPC_HOST","node")
RPC_PORT=int(os.environ.get("BTC_RPC_PORT","8332"))
RPC_USER=os.environ.get("BTC_RPC_USER","seymour_rpc")
RPC_PASSWORD=os.environ.get("BTC_RPC_PASSWORD","change-me-before-production")
DATA_PATH=Path(os.environ.get("BTC_DATA_PATH","/node-data"))
REACHABILITY_TIMEOUT=float(os.environ.get("BTC_RPC_REACHABILITY_TIMEOUT_SECONDS","5"))
HEAVY_TIMEOUT=float(os.environ.get("BTC_RPC_HEAVY_TIMEOUT_SECONDS","120"))
REACHABILITY_TIMEOUT=float(os.environ.get("BTC_RPC_REACHABILITY_TIMEOUT_SECONDS","30"))
REFRESH_INTERVAL=float(os.environ.get("BTC_TELEMETRY_REFRESH_INTERVAL_SECONDS","15"))
STALE_AFTER=float(os.environ.get("BTC_TELEMETRY_STALE_AFTER_SECONDS","180"))

_lock=threading.Lock()
_snapshot=None
_last_error=None
_last_attempt=None

def rpc(method, timeout):
    body=json.dumps({"jsonrpc":"1.0","id":"seymour","method":method,"params":[]}).encode()
    req=urllib.request.Request(
        f"http://{RPC_HOST}:{RPC_PORT}/",
        data=body,
        headers={
            "Content-Type":"application/json",
            "Authorization":"Basic "+base64.b64encode(
                f"{RPC_USER}:{RPC_PASSWORD}".encode()
            ).decode(),
        },
    )
    with urllib.request.urlopen(req,timeout=timeout) as response:
        payload=json.loads(response.read().decode())
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))
    return payload.get("result")

def storage():
    st=os.statvfs(DATA_PATH)
    total=st.f_blocks*st.f_frsize
    free=st.f_bavail*st.f_frsize
    return {
        "path":str(DATA_PATH),
        "totalBytes":total,
        "filesystemUsedBytes":total-free,
        "freeBytes":free,
        "healthy":True,
    }

def reachability():
    try:
        rpc("uptime",REACHABILITY_TIMEOUT)
        return True,None
    except Exception as exc:
        return False,str(exc)

def refresh_once():
    global _snapshot,_last_error,_last_attempt
    _last_attempt=time.time()
    ok,err=reachability()
    if not ok:
        with _lock:
            _last_error=err
        return
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            fc=pool.submit(rpc,"getblockchaininfo",HEAVY_TIMEOUT)
            fn=pool.submit(rpc,"getnetworkinfo",HEAVY_TIMEOUT)
            chain=fc.result()
            network=fn.result()
        if not isinstance(chain,dict) or not isinstance(network,dict):
            raise RuntimeError("invalid heavy RPC payload")
        snap={
            "measuredAt":time.time(),
            "blocks":chain.get("blocks"),
            "headers":chain.get("headers"),
            "verificationProgress":chain.get("verificationprogress"),
            "initialBlockDownload":chain.get("initialblockdownload"),
            "chainSizeBytes":chain.get("size_on_disk"),
            "peers":network.get("connections"),
            "subversion":network.get("subversion"),
        }
        with _lock:
            _snapshot=snap
            _last_error=None
    except Exception as exc:
        with _lock:
            _last_error=str(exc)

def worker():
    while True:
        started=time.monotonic()
        refresh_once()
        time.sleep(max(REFRESH_INTERVAL-(time.monotonic()-started),1.0))

def status_payload():
    ok,reach_error=reachability()
    with _lock:
        snap=dict(_snapshot) if isinstance(_snapshot,dict) else None
        heavy_error=_last_error
        last_attempt=_last_attempt
    age=max(time.time()-float(snap["measuredAt"]),0.0) if snap else None
    fresh=bool(ok and snap and age is not None and age<=STALE_AFTER)
    stale=bool(snap and not fresh)
    if not ok:
        state="degraded"; reason=reach_error or "Bitcoin RPC is unreachable."
    elif not snap:
        state="starting"; reason="Bitcoin RPC is reachable; telemetry snapshot is initializing."
    elif snap.get("initialBlockDownload"):
        state="syncing"
        reason="Bitcoin Core initial block download is active." if fresh else "Bitcoin Core is syncing; heavy telemetry is temporarily stale."
    else:
        state="running"
        reason="Bitcoin Core RPC and telemetry are healthy." if fresh else "Bitcoin Core RPC is reachable; heavy telemetry is temporarily stale."
    verification=snap.get("verificationProgress") if snap else None
    return {
        "healthy":bool(ok),
        "status":"online" if ok else "degraded",
        "chain":"bitcoin",
        "runtimeState":state,
        "runtimeStateReason":reason,
        "runtimeRpcReachable":bool(ok),
        "runtimeRpcHealthy":bool(ok),
        "runtimeInitialBlockDownload":snap.get("initialBlockDownload") if snap else None,
        "runtimeVerificationProgress":verification,
        "blocks":snap.get("blocks") if snap else None,
        "headers":snap.get("headers") if snap else None,
        "verificationProgress":verification,
        "initialBlockDownload":snap.get("initialBlockDownload") if snap else None,
        "chainSizeBytes":snap.get("chainSizeBytes") if snap else None,
        "peers":snap.get("peers") if snap else None,
        "subversion":snap.get("subversion") if snap else None,
        "telemetryFresh":fresh,
        "telemetryStale":stale,
        "telemetryAgeSeconds":round(age,3) if age is not None else None,
        "telemetrySource":"live-cache" if snap else "initializing",
        "telemetryLastAttemptAt":last_attempt,
        "telemetryError":heavy_error,
        "storage":storage(),
    }

class Handler(BaseHTTPRequestHandler):
    def send_json(self,payload):
        body=json.dumps(payload,indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass
    def do_GET(self):
        if self.path in {"/","/api/status"}:
            self.send_json(status_payload()); return
        if self.path=="/api/health":
            p=status_payload()
            self.send_json({
                "healthy":p["healthy"],
                "status":p["status"],
                "runtimeState":p["runtimeState"],
                "runtimeRpcReachable":p["runtimeRpcReachable"],
                "telemetryFresh":p["telemetryFresh"],
                "telemetryStale":p["telemetryStale"],
                "storage":p["storage"],
            }); return
        self.send_error(404)
    def log_message(self,format,*args):
        return

def main():
    threading.Thread(target=worker,daemon=True,name="btc-telemetry-refresh").start()
    ThreadingHTTPServer(("0.0.0.0",8080),Handler).serve_forever()

if __name__=="__main__":
    main()
