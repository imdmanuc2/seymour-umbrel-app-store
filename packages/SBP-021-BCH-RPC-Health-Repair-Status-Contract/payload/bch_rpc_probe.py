from __future__ import annotations
import base64, json, os
from typing import Any
from urllib import error, request

RPC_URL=os.environ.get("BCH_RPC_URL","http://seymour-bch-node_node_1:8332/")
RPC_USER=os.environ.get("BCH_RPC_USER","")
RPC_PASSWORD=os.environ.get("BCH_RPC_PASSWORD","")
RPC_TIMEOUT_SECONDS=max(1,int(os.environ.get("BCH_RPC_TIMEOUT_SECONDS","5")))

def _rpc_headers()->dict[str,str]:
    h={"Content-Type":"application/json","Accept":"application/json","User-Agent":"Seymour-Blockchain-Manager/1.0"}
    if RPC_USER or RPC_PASSWORD:
        token=base64.b64encode(f"{RPC_USER}:{RPC_PASSWORD}".encode()).decode()
        h["Authorization"]=f"Basic {token}"
    return h

def call_rpc(method:str,params:list[Any]|None=None)->dict[str,Any]:
    body=json.dumps({"jsonrpc":"1.0","id":f"seymour-{method}","method":method,"params":params or []}).encode()
    req=request.Request(RPC_URL,data=body,headers=_rpc_headers(),method="POST")
    try:
        with request.urlopen(req,timeout=RPC_TIMEOUT_SECONDS) as r:
            payload=json.loads(r.read().decode())
            return {"reachable":True,"httpStatus":int(r.status),"result":payload.get("result"),"rpcError":payload.get("error"),"transportError":None,"authConfigured":bool(RPC_USER or RPC_PASSWORD),"url":RPC_URL}
    except error.HTTPError as exc:
        raw=""
        try: raw=exc.read().decode()
        except Exception: pass
        parsed=None
        if raw:
            try: parsed=json.loads(raw)
            except Exception: pass
        return {"reachable":False,"httpStatus":int(exc.code),"result":None,"rpcError":parsed.get("error") if isinstance(parsed,dict) else None,"transportError":f"HTTP {exc.code}: {exc.reason}","authConfigured":bool(RPC_USER or RPC_PASSWORD),"url":RPC_URL}
    except Exception as exc:
        return {"reachable":False,"httpStatus":None,"result":None,"rpcError":None,"transportError":str(exc),"authConfigured":bool(RPC_USER or RPC_PASSWORD),"url":RPC_URL}

def probe()->dict[str,Any]:
    bc=call_rpc("getblockchaininfo")
    net=call_rpc("getnetworkinfo")
    if not bc["reachable"]:
        return {"reachable":False,"healthy":False,"status":"rpc-unreachable","authConfigured":bc["authConfigured"],"httpStatus":bc["httpStatus"],"error":bc["transportError"] or bc["rpcError"],"rpcUrl":RPC_URL,"chain":None,"height":None,"headers":None,"peers":None,"progressPercent":None,"initialBlockDownload":None,"verificationProgress":None,"raw":{"blockchain":bc,"network":net}}
    info=bc["result"] if isinstance(bc.get("result"),dict) else {}
    ninfo=net["result"] if isinstance(net.get("result"),dict) else {}
    progress=info.get("verificationprogress")
    return {"reachable":True,"healthy":bc.get("rpcError") is None,"status":"healthy" if bc.get("rpcError") is None else "rpc-error","authConfigured":bc["authConfigured"],"httpStatus":bc["httpStatus"],"error":bc.get("rpcError"),"rpcUrl":RPC_URL,"chain":info.get("chain"),"height":info.get("blocks"),"headers":info.get("headers"),"peers":ninfo.get("connections"),"progressPercent":float(progress)*100.0 if progress is not None else None,"initialBlockDownload":info.get("initialblockdownload"),"verificationProgress":progress,"bestBlockHash":info.get("bestblockhash"),"difficulty":info.get("difficulty"),"raw":{"blockchain":bc,"network":net}}
