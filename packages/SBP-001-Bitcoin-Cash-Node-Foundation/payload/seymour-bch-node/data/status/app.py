import base64,json,os,urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
HOST=os.getenv("BCH_RPC_HOST","node");PORT=int(os.getenv("BCH_RPC_PORT","8332"));USER=os.getenv("BCH_RPC_USER","seymour_rpc");PASSWORD=os.getenv("BCH_RPC_PASSWORD","change-me-before-production")
def rpc(method):
 body=json.dumps({"jsonrpc":"1.0","id":"seymour","method":method,"params":[]}).encode();token=base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode();req=urllib.request.Request(f"http://{HOST}:{PORT}",data=body,headers={"Authorization":f"Basic {token}","Content-Type":"application/json"})
 with urllib.request.urlopen(req,timeout=5) as r:data=json.loads(r.read())
 if data.get("error"):raise RuntimeError(str(data["error"]))
 return data["result"]
def status():
 try:
  c=rpc("getblockchaininfo");n=rpc("getnetworkinfo")
  return {"healthy":True,"status":"online","chain":"bitcoin-cash","blocks":c.get("blocks"),"headers":c.get("headers"),"verificationProgress":c.get("verificationprogress"),"initialBlockDownload":c.get("initialblockdownload"),"peers":n.get("connections"),"subversion":n.get("subversion")}
 except Exception as e:return {"healthy":False,"status":"starting","chain":"bitcoin-cash","error":str(e)}
class H(BaseHTTPRequestHandler):
 def j(self,p,c=200):
  b=json.dumps(p,indent=2).encode();self.send_response(c);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  if self.path=="/":
   b=Path("/app/index.html").read_bytes();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
  elif self.path=="/api/status":self.j(status())
  elif self.path=="/api/health":
   p=status();self.j(p,200 if p["healthy"] else 503)
  elif self.path=="/api/contract":self.j(json.loads(Path("/contracts/bitcoin-cash-node.json").read_text()))
  elif self.path=="/api/provisioning":self.j(json.loads(Path("/provisioning/modes.json").read_text()))
  else:self.j({"error":"Not found"},404)
 def log_message(self,*_):pass
ThreadingHTTPServer(("0.0.0.0",8080),H).serve_forever()
