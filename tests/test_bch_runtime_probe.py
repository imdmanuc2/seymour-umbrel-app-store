from pathlib import Path
import sys
repo=Path(__file__).resolve().parents[1]; web=repo/"seymour-blockchain-manager/data/web"; sys.path.insert(0,str(web))
import bch_runtime_probe as p
class F:
 def __init__(self,*a,**k): self.done=False
 def settimeout(self,*a): pass
 def connect(self,*a): pass
 def sendall(self,*a): pass
 def recv(self,n):
  if self.done: return b""
  self.done=True; body=b'{"Id":"abc123456789ffff","State":{"Status":"running","Running":true,"Health":{"Status":"unhealthy"}}}'
  return b"HTTP/1.1 200 OK\r\nContent-Length: "+str(len(body)).encode()+b"\r\n\r\n"+body
 def close(self): pass
old=p.socket.socket; oldpath=p.DOCKER_SOCKET
class P:
 def exists(self): return True
 def __str__(self): return "/var/run/docker.sock"
try:
 p.socket.socket=F; p.DOCKER_SOCKET=P(); r=p.docker_container_inspect(); assert r["found"] and r["running"] and r["health"]=="unhealthy"
finally: p.socket.socket=old; p.DOCKER_SOCKET=oldpath
print("SBP-020 Docker runtime probe verification: PASS")
