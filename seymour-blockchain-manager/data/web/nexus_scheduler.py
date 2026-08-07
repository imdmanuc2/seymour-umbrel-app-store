from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json, os, threading
from pathlib import Path
from typing import Any
from nexus_delivery import REGISTRATION_TOKEN, REGISTRATION_URL, deliver
from nexus_integration import registration_payload
from sync_manager import analyze
from telemetry import dashboard_payload

ENABLED=os.environ.get("NEXUS_REFRESH_ENABLED","true").strip().lower() in {"1","true","yes","on"}
INTERVAL_SECONDS=max(30,int(os.environ.get("NEXUS_REFRESH_INTERVAL_SECONDS","60")))
INITIAL_DELAY_SECONDS=max(0,int(os.environ.get("NEXUS_REFRESH_INITIAL_DELAY_SECONDS","15")))
STATE_PATH=Path(os.environ.get("NEXUS_REFRESH_STATE_PATH","/evidence/nexus-refresh-state.json"))
_lock=threading.Lock(); _stop_event=threading.Event(); _thread=None

@dataclass
class SchedulerState:
    enabled: bool
    configured: bool
    running: bool
    interval_seconds: int
    initial_delay_seconds: int
    last_started_at: str|None=None
    last_completed_at: str|None=None
    last_status: str="never-run"
    last_delivery_id: str|None=None
    last_registration_id: str|None=None
    last_http_status: int|None=None
    last_error: str|None=None
    run_count: int=0

_state=SchedulerState(ENABLED,bool(REGISTRATION_URL and REGISTRATION_TOKEN),False,INTERVAL_SECONDS,INITIAL_DELAY_SECONDS)
def utc_now(): return datetime.now(UTC).isoformat()
def _save_state():
    STATE_PATH.parent.mkdir(parents=True,exist_ok=True)
    STATE_PATH.write_text(json.dumps(asdict(_state),indent=2))
def status()->dict[str,Any]:
    with _lock: return asdict(_state)
def refresh_once()->dict[str,Any]:
    with _lock:
        _state.running=True; _state.last_started_at=utc_now(); _state.last_error=None; _save_state()
    try:
        if not ENABLED:
            result={"status":"disabled","error":None}
        elif not (REGISTRATION_URL and REGISTRATION_TOKEN):
            result={"status":"not-configured","error":"Nexus registration URL/token are not configured."}
        else:
            dashboard=dashboard_payload(); sync=analyze(dashboard)
            payload=registration_payload(dashboard,sync)
            result=deliver(payload,dry_run=False).to_dict()
        with _lock:
            _state.run_count+=1
            _state.last_completed_at=utc_now()
            _state.last_status=str(result.get("status","unknown"))
            _state.last_delivery_id=result.get("delivery_id")
            _state.last_registration_id=result.get("registration_id")
            _state.last_http_status=result.get("http_status")
            _state.last_error=result.get("error")
            _state.running=False
            _save_state()
        return result
    except Exception as exc:
        with _lock:
            _state.run_count+=1; _state.last_completed_at=utc_now(); _state.last_status="failed"; _state.last_error=str(exc); _state.running=False; _save_state()
        return {"status":"failed","error":str(exc)}
def _loop():
    if INITIAL_DELAY_SECONDS and _stop_event.wait(INITIAL_DELAY_SECONDS): return
    while not _stop_event.is_set():
        refresh_once()
        if _stop_event.wait(INTERVAL_SECONDS): return
def start():
    global _thread
    if not ENABLED or not (REGISTRATION_URL and REGISTRATION_TOKEN): return False
    if _thread is not None and _thread.is_alive(): return True
    _stop_event.clear()
    _thread=threading.Thread(target=_loop,name="nexus-registration-refresh",daemon=True)
    _thread.start(); return True
def stop(): _stop_event.set()
