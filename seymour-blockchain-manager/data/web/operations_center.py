from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from enum import StrEnum
import json, os, socket, subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4
from urllib.parse import quote
from bch_runtime_probe import probe as probe_bch_runtime
APP_ID=os.environ.get("BCH_APP_ID","seymour-bch-node")
NODE_CONTAINER=os.environ.get("BCH_NODE_CONTAINER","seymour-bch-node_node_1")
DOCKER_SOCKET=Path(os.environ.get("DOCKER_SOCKET","/var/run/docker.sock"))
CONTROL_SCRIPT=Path(os.environ.get("SEYMOUR_UMBREL_CONTROL_SCRIPT","/control/seymour-umbrel-app"))
EVIDENCE_PATH=Path(os.environ.get("OPERATIONS_EVIDENCE_PATH","/evidence/operations.jsonl"))
HEALTH_HISTORY_PATH=Path(os.environ.get("HEALTH_HISTORY_PATH","/evidence/health-history.jsonl"))
BACKUP_ROOT=Path(os.environ.get("BCH_BACKUP_ROOT","/evidence/backups"))
class OperationKind(StrEnum):
 DIAGNOSTICS="diagnostics"; LOGS="logs"; BACKUP="backup"; RESTORE="restore"; UPGRADE="upgrade"
class OperationStatus(StrEnum):
 PLANNED="planned"; SUCCEEDED="succeeded"; FAILED="failed"
@dataclass
class OperationResult:
 operation_id:str; kind:OperationKind; status:OperationStatus; created_at:str; confirmation:str|None; result:Any=None; error:str|None=None
 def to_dict(self):
  d=asdict(self);d['kind']=self.kind.value;d['status']=self.status.value;return d
def now(): return datetime.now(UTC).isoformat()
def token(kind): return None if kind in {OperationKind.DIAGNOSTICS,OperationKind.LOGS} else f"{kind.value.upper()}-{APP_ID}"
def evidence(result):
 EVIDENCE_PATH.parent.mkdir(parents=True,exist_ok=True)
 with EVIDENCE_PATH.open('a') as h:h.write(json.dumps(result.to_dict(),sort_keys=True)+'\n')
def run(cmd,timeout=120):
 try:
  c=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,check=False)
  return {'returnCode':c.returncode,'stdout':c.stdout[-20000:],'stderr':c.stderr[-20000:],'success':c.returncode==0}
 except subprocess.TimeoutExpired as exc:
  return {'returnCode':124,'stdout':str(exc.stdout or '')[-20000:],'stderr':f'Command timed out after {timeout}s.','success':False}
 except FileNotFoundError as exc:
  return {'returnCode':127,'stdout':'','stderr':str(exc),'success':False}
 except Exception as exc:
  return {'returnCode':1,'stdout':'','stderr':str(exc),'success':False}
def _decode_chunked(body: bytes) -> bytes:
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

def diagnostics():
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
 HEALTH_HISTORY_PATH.write_text(json.dumps({'capturedAt':now(),'diagnostics':r.result})+'\n')
 return r

def recent_logs(lines=200):
 r=OperationResult(str(uuid4()),OperationKind.LOGS,OperationStatus.PLANNED,now(),None)
 r.result=docker_logs_via_socket(lines)
 r.status=OperationStatus.SUCCEEDED if r.result.get('success') else OperationStatus.FAILED
 if r.status is OperationStatus.FAILED:
  r.error='Unable to read node logs through Docker Engine API.'
 evidence(r)
 return r

def plan(kind,details):
 if kind not in {OperationKind.BACKUP,OperationKind.RESTORE,OperationKind.UPGRADE}: raise ValueError('Operation does not support planning.')
 r=OperationResult(str(uuid4()),kind,OperationStatus.PLANNED,now(),token(kind),{'appId':APP_ID,'details':details,'destructive':kind is OperationKind.RESTORE})
 evidence(r);return r
def execute_backup(confirmation):
 r=OperationResult(str(uuid4()),OperationKind.BACKUP,OperationStatus.PLANNED,now(),token(OperationKind.BACKUP))
 if confirmation!=r.confirmation:
  r.status=OperationStatus.FAILED;r.error='Backup confirmation token did not match.';evidence(r);return r
 BACKUP_ROOT.mkdir(parents=True,exist_ok=True);dest=BACKUP_ROOT/f"bch-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
 r.result={'destination':str(dest),'command':run(['cp','-a','/bch-data',str(dest)],900)};r.status=OperationStatus.SUCCEEDED if r.result['command']['success'] else OperationStatus.FAILED
 if r.status is OperationStatus.FAILED:r.error='Backup command failed.'
 evidence(r);return r
def recommendations(payload):
 out=[]
 if not payload.get('state',{}).get('success'):out.append({'severity':'critical','code':'umbrel-state-failed','message':'Check Umbrel state and the control bridge.'})
 if not payload.get('container',{}).get('success'):out.append({'severity':'critical','code':'container-inspection-failed','message':'Inspect Docker and the BCH container.'})
 if not payload.get('rpc',{}).get('success'):out.append({'severity':'warning','code':'rpc-diagnostics-failed','message':'Check RPC credentials and recent logs.'})
 return out or [{'severity':'info','code':'operations-healthy','message':'No immediate recovery action is required.'}]

def confirmation_token(kind: OperationKind) -> str | None:
    if kind in {
        OperationKind.DIAGNOSTICS,
        OperationKind.LOGS,
    }:
        return None

    return f"{kind.value.upper()}-{APP_ID}"

