from pathlib import Path
import sys

root = Path(sys.argv[1])
web = root / "seymour-blockchain-manager/data/web"
js = web / "app.js"
ops = web / "operations_center.py"

# ---------------------------------------------------------------------------
# app.js — preserve last complete sync metrics and avoid NaN rendering
# ---------------------------------------------------------------------------
s = js.read_text()

# Add completeness helper before presentedRuntime.
if "function hasCompleteSyncTelemetry(telemetry)" not in s:
    anchor = "function presentedRuntime(provider) {"
    idx = s.find(anchor)
    if idx < 0:
        raise SystemExit("SBP-045 patch: presentedRuntime anchor missing")
    helper = r'''function hasCompleteSyncTelemetry(telemetry) {
  const sync = telemetry?.sync || {};
  return (
    Number.isFinite(Number(sync.progressPercent)) &&
    Number.isFinite(Number(sync.height)) &&
    Number.isFinite(Number(sync.headers))
  );
}

'''
    s = s[:idx] + helper + s[idx:]

# Replace good-state snapshot logic so incomplete syncing payloads don't clobber
# the last complete telemetry.
old = '''  const current = state.runtimePresentation[providerId] || null;
  const isGoodLiveState = ["running", "syncing", "starting"].includes(rawState);

  if (isGoodLiveState) {
    state.runtimePresentation[providerId] = {
      state: rawState,
      telemetry,
      lastGoodAt: now,
    };
    return {state: rawState, telemetry, graceHeld: false};
  }
'''
new = '''  const current = state.runtimePresentation[providerId] || null;
  const isGoodLiveState = ["running", "syncing", "starting"].includes(rawState);
  const completeSyncTelemetry =
    rawState !== "syncing" || hasCompleteSyncTelemetry(telemetry);

  if (isGoodLiveState && completeSyncTelemetry) {
    state.runtimePresentation[providerId] = {
      state: rawState,
      telemetry,
      lastGoodAt: now,
    };
    return {state: rawState, telemetry, graceHeld: false};
  }

  if (
    rawState === "syncing" &&
    current &&
    current.state === "syncing" &&
    !completeSyncTelemetry &&
    now - current.lastGoodAt <= RUNTIME_PRESENTATION_GRACE_MS
  ) {
    return {
      state: "syncing",
      telemetry: current.telemetry,
      graceHeld: true,
      rawState,
    };
  }
'''
if old not in s:
    raise SystemExit("SBP-045 patch: presentation snapshot block missing")
s = s.replace(old, new, 1)

# Make runtime-focus block formatting null/NaN safe.
old = '''  const progress = Number(sync.progressPercent || 0);
  const height = sync.height ?? "—";
  const headers = sync.headers ?? "—";
'''
new = '''  const rawProgress = Number(sync.progressPercent);
  const progress = Number.isFinite(rawProgress) ? rawProgress : null;

  const rawHeight = Number(sync.height);
  const rawHeaders = Number(sync.headers);
  const height = Number.isFinite(rawHeight) ? rawHeight : null;
  const headers = Number.isFinite(rawHeaders) ? rawHeaders : null;
'''
if old in s:
    s = s.replace(old, new, 1)

old = '''        presentation.state === "syncing"
          ? `
            <div class="runtime-focus-progress">
              ${progressBar(progress, "Blockchain sync")}
              <div class="runtime-focus-blocks">
                <span>Blocks</span>
                <strong>${Number(height).toLocaleString()} / ${Number(headers).toLocaleString()}</strong>
              </div>
            </div>
          `
          : ""
'''
new = '''        presentation.state === "syncing" && progress !== null
          ? `
            <div class="runtime-focus-progress">
              ${progressBar(progress, "Blockchain sync")}
              <div class="runtime-focus-blocks">
                <span>Blocks</span>
                <strong>${
                  height !== null && headers !== null
                    ? `${height.toLocaleString()} / ${headers.toLocaleString()}`
                    : "Telemetry warming up"
                }</strong>
              </div>
            </div>
          `
          : presentation.state === "syncing"
            ? `
              <div class="telemetry-grace-note">
                Sync telemetry is warming up after a runtime transition.
              </div>
            `
            : ""
'''
if old in s:
    s = s.replace(old, new, 1)

# Lifecycle endpoint gets more time than observation calls.
s = s.replace(
    '''    15000
  );
}

async function lifecyclePlan''',
    '''    30000
  );
}

async function lifecyclePlan''',
    1,
)

js.write_text(s)

# ---------------------------------------------------------------------------
# operations_center.py — canonical diagnostics + Docker socket log reader
# ---------------------------------------------------------------------------
o = ops.read_text()

# Add imports.
if "import socket" not in o:
    o = o.replace(
        "import json, os, subprocess\n",
        "import json, os, socket, subprocess\n",
        1,
    )

if "from urllib.parse import quote" not in o:
    o = o.replace(
        "from uuid import uuid4\n",
        "from uuid import uuid4\nfrom urllib.parse import quote\n",
        1,
    )

if "from bch_runtime_probe import probe as probe_bch_runtime" not in o:
    insert_after = "from urllib.parse import quote\n"
    o = o.replace(
        insert_after,
        insert_after + "from bch_runtime_probe import probe as probe_bch_runtime\n",
        1,
    )

# Add Docker socket constant if absent.
if "DOCKER_SOCKET=" not in o:
    anchor = 'NODE_CONTAINER=os.environ.get("BCH_NODE_CONTAINER","seymour-bch-node_node_1")\n'
    o = o.replace(
        anchor,
        anchor + 'DOCKER_SOCKET=Path(os.environ.get("DOCKER_SOCKET","/var/run/docker.sock"))\n',
        1,
    )

# Harden generic run helper.
old_run = '''def run(cmd,timeout=120):
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,check=False)
 return {'returnCode':c.returncode,'stdout':c.stdout[-20000:],'stderr':c.stderr[-20000:],'success':c.returncode==0}
'''
new_run = '''def run(cmd,timeout=120):
 try:
  c=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,check=False)
  return {'returnCode':c.returncode,'stdout':c.stdout[-20000:],'stderr':c.stderr[-20000:],'success':c.returncode==0}
 except subprocess.TimeoutExpired as exc:
  return {'returnCode':124,'stdout':str(exc.stdout or '')[-20000:],'stderr':f'Command timed out after {timeout}s.','success':False}
 except FileNotFoundError as exc:
  return {'returnCode':127,'stdout':'','stderr':str(exc),'success':False}
 except Exception as exc:
  return {'returnCode':1,'stdout':'','stderr':str(exc),'success':False}
'''
if old_run in o:
    o = o.replace(old_run, new_run, 1)

# Insert Docker Engine socket helpers before diagnostics.
diag_idx = o.find("def diagnostics():")
if diag_idx < 0:
    raise SystemExit("SBP-045 patch: diagnostics anchor missing")

if "def docker_logs_via_socket(" not in o:
    helper = r'''def _decode_chunked(body: bytes) -> bytes:
 out=bytearray();pos=0
 while pos < len(body):
  line_end=body.find(b"\r\n",pos)
  if line_end < 0: break
  try: size=int(body[pos:line_end].split(b";",1)[0],16)
  except ValueError: break
  pos=line_end+2
  if size == 0: break
  out.extend(body[pos:pos+size])
  pos += size + 2
 return bytes(out)

def _docker_http(path: str, timeout: float=5.0) -> tuple[int,dict[str,str],bytes]:
 if not DOCKER_SOCKET.exists():
  return 0,{},f"Docker socket not found: {DOCKER_SOCKET}".encode()
 sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
 sock.settimeout(timeout)
 try:
  sock.connect(str(DOCKER_SOCKET))
  request_bytes=(
   f"GET {path} HTTP/1.1\r\n"
   "Host: docker\r\n"
   "Connection: close\r\n\r\n"
  ).encode()
  sock.sendall(request_bytes)
  chunks=[]
  while True:
   chunk=sock.recv(65536)
   if not chunk: break
   chunks.append(chunk)
 finally:
  sock.close()

 raw=b"".join(chunks)
 head,_,body=raw.partition(b"\r\n\r\n")
 lines=head.splitlines()
 try: code=int(lines[0].split()[1])
 except Exception: code=0
 headers={}
 for line in lines[1:]:
  if b":" not in line: continue
  key,value=line.split(b":",1)
  headers[key.decode("latin-1").strip().lower()]=value.decode("latin-1").strip().lower()
 if headers.get("transfer-encoding") == "chunked":
  body=_decode_chunked(body)
 return code,headers,body

def _decode_docker_log_stream(body: bytes) -> str:
 # Docker multiplex format: 8-byte header + payload. If the stream is plain
 # text (TTY), return it directly.
 if len(body) < 8 or body[0] not in (0,1,2):
  return body.decode("utf-8","replace")

 out=[]
 pos=0
 while pos + 8 <= len(body):
  stream_type=body[pos]
  size=int.from_bytes(body[pos+4:pos+8],"big")
  pos += 8
  if size < 0 or pos + size > len(body):
   break
  payload=body[pos:pos+size]
  pos += size
  if stream_type in (1,2):
   out.append(payload.decode("utf-8","replace"))
 return "".join(out)

def docker_logs_via_socket(lines: int=200) -> dict[str,Any]:
 safe_lines=max(10,min(int(lines),1000))
 path=(
  f"/containers/{quote(NODE_CONTAINER,safe='')}/logs"
  f"?stdout=1&stderr=1&tail={safe_lines}&timestamps=1"
 )
 try:
  code,_,body=_docker_http(path,timeout=8.0)
  if code != 200:
   return {
    'returnCode':code or 1,
    'stdout':'',
    'stderr':body.decode('utf-8','replace')[-20000:],
    'success':False,
    'source':'docker-engine-api',
   }
  return {
   'returnCode':0,
   'stdout':_decode_docker_log_stream(body)[-20000:],
   'stderr':'',
   'success':True,
   'source':'docker-engine-api',
  }
 except Exception as exc:
  return {
   'returnCode':1,
   'stdout':'',
   'stderr':str(exc),
   'success':False,
   'source':'docker-engine-api',
  }

'''
    o = o[:diag_idx] + helper + o[diag_idx:]

# Replace diagnostics implementation with canonical runtime probe.
diag_start = o.find("def diagnostics():")
diag_end = o.find("\ndef recent_logs", diag_start)
if diag_start < 0 or diag_end < 0:
    raise SystemExit("SBP-045 patch: diagnostics boundaries missing")

new_diag = '''def diagnostics():
 r=OperationResult(str(uuid4()),OperationKind.DIAGNOSTICS,OperationStatus.PLANNED,now(),None)
 try:
  runtime=probe_bch_runtime()
  operational=runtime.get('operationalState') if isinstance(runtime.get('operationalState'),dict) else {}
  rpc=runtime.get('rpc') if isinstance(runtime.get('rpc'),dict) else {}
  probe=rpc.get('probe') if isinstance(rpc.get('probe'),dict) else {}

  checks=[
   {
    'name':'runtime-state',
    'status':'passed' if operational.get('state') in {'running','syncing','starting'} else 'warning',
    'message':f"Canonical runtime state: {operational.get('state','unknown')}",
   },
   {
    'name':'rpc-reachable',
    'status':'passed' if operational.get('rpcReachable') else 'failed',
    'message':'RPC is reachable.' if operational.get('rpcReachable') else 'RPC is not reachable.',
   },
   {
    'name':'rpc-health',
    'status':'passed' if operational.get('rpcHealthy') else 'warning',
    'message':'RPC health is good.' if operational.get('rpcHealthy') else 'RPC health is degraded.',
   },
   {
    'name':'peers',
    'status':'passed' if int(probe.get('peers') or 0) > 0 else 'warning',
    'message':f"Connected peers: {probe.get('peers') or 0}",
   },
   {
    'name':'sync-progress',
    'status':'passed' if probe.get('progressPercent') is not None else 'warning',
    'message':(
     f"Sync progress: {probe.get('progressPercent')}%"
     if probe.get('progressPercent') is not None
     else 'Sync progress is temporarily unavailable.'
    ),
   },
  ]

  payload={
   'checks':checks,
   'runtime':runtime,
   'recommendations':(
    [{'severity':'info','code':'continue-syncing','message':'Node is syncing normally; no operator action is required.'}]
    if operational.get('state') == 'syncing'
    else [{'severity':'info','code':'runtime-observed','message':'Review canonical runtime state and diagnostics evidence.'}]
   ),
  }

  r.result=payload
  r.status=OperationStatus.SUCCEEDED
 except Exception as exc:
  r.result={'checks':[]}
  r.status=OperationStatus.FAILED
  r.error=f'Diagnostics failed: {exc}'

 evidence(r)
 HEALTH_HISTORY_PATH.parent.mkdir(parents=True,exist_ok=True)
 HEALTH_HISTORY_PATH.write_text(json.dumps({'capturedAt':now(),'diagnostics':r.result})+'\\n')
 return r
'''
o = o[:diag_start] + new_diag + o[diag_end:]

# Replace recent_logs docker CLI.
log_start = o.find("def recent_logs(lines=200):")
log_end = o.find("\ndef plan(", log_start)
if log_start < 0 or log_end < 0:
    raise SystemExit("SBP-045 patch: recent_logs boundaries missing")

new_logs = '''def recent_logs(lines=200):
 r=OperationResult(str(uuid4()),OperationKind.LOGS,OperationStatus.PLANNED,now(),None)
 r.result=docker_logs_via_socket(lines)
 r.status=OperationStatus.SUCCEEDED if r.result.get('success') else OperationStatus.FAILED
 if r.status is OperationStatus.FAILED:
  r.error='Unable to read node logs through Docker Engine API.'
 evidence(r)
 return r
'''
o = o[:log_start] + new_logs + o[log_end:]

ops.write_text(o)
