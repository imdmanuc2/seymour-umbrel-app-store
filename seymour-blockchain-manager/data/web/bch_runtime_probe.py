from __future__ import annotations
import json, os, socket
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import quote
from bch_rpc_probe import probe as probe_bch_rpc

DOCKER_SOCKET=Path(os.environ.get("DOCKER_SOCKET","/var/run/docker.sock"))
BCH_NODE_CONTAINER=os.environ.get("BCH_NODE_CONTAINER","seymour-bch-node_node_1")
BCH_HEALTH_URL=os.environ.get("BCH_HEALTH_URL","http://seymour-bch-node_status_1:8080/api/health")
BCH_STATUS_URL=os.environ.get("BCH_STATUS_URL","http://seymour-bch-node_status_1:8080/api/status")

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

def http_json(url: str)->dict[str,Any]:
 out={"url":url,"reachable":False,"httpStatus":None,"payload":None,"error":None}
 try:
  with request.urlopen(url,timeout=4) as r:
   raw=r.read().decode(); out["httpStatus"]=int(r.status); out["reachable"]=True
   try: out["payload"]=json.loads(raw)
   except json.JSONDecodeError: out["payload"]={"raw":raw}
 except error.HTTPError as exc:
  out["httpStatus"]=int(exc.code); out["error"]=f"HTTP {exc.code}: {exc.reason}"
  try:
   raw=exc.read().decode(); out["payload"]=json.loads(raw) if raw else None
  except Exception: pass
 except Exception as exc: out["error"]=str(exc)
 return out

def probe()->dict[str,Any]:
 container=docker_container_inspect()
 legacy_health=http_json(BCH_HEALTH_URL)
 legacy_status=http_json(BCH_STATUS_URL)
 rpc_probe=probe_bch_rpc()
 installed=bool(container.get("found")); running=bool(container.get("running"))
 rpc=bool(rpc_probe.get("reachable") and rpc_probe.get("healthy"))
 lifecycle="not-installed" if not installed else "stopped" if not running else "running" if rpc else "degraded"
 return {"providerId":"bitcoin-cash-mainnet","appId":"seymour-bch-node","installed":installed,"running":running,"lifecycleStatus":lifecycle,"container":container,"rpc":{"reachable":rpc,"probe":rpc_probe,"health":legacy_health,"status":legacy_status}}
