from __future__ import annotations
from collections import deque
import json, socket, time
from typing import Any
from urllib.parse import quote
from bch_rpc_probe import BCH_NODE_CONTAINER, DOCKER_SOCKET, call_rpc
from bch_runtime_probe import probe as probe_bch_runtime

OBSERVATIONS: deque[dict[str, Any]] = deque(maxlen=180)

def _decode_chunked(body: bytes) -> bytes:
    out=bytearray(); pos=0
    while pos < len(body):
        e=body.find(b'\r\n',pos)
        if e<0: break
        try: size=int(body[pos:e].split(b';',1)[0],16)
        except ValueError: break
        pos=e+2
        if size==0: break
        out.extend(body[pos:pos+size]); pos += size+2
    return bytes(out)

def _docker_json(path: str, timeout: float=8.0) -> dict[str,Any]:
    try:
        sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); sock.settimeout(timeout); sock.connect(DOCKER_SOCKET)
        sock.sendall((f'GET {path} HTTP/1.1\r\nHost: docker\r\nConnection: close\r\n\r\n').encode())
        chunks=[]
        while True:
            c=sock.recv(65536)
            if not c: break
            chunks.append(c)
        sock.close(); raw=b''.join(chunks); head,_,body=raw.partition(b'\r\n\r\n')
        lines=head.splitlines(); code=int(lines[0].split()[1]) if lines else 0
        headers={}
        for line in lines[1:]:
            if b':' in line:
                k,v=line.split(b':',1); headers[k.decode().strip().lower()]=v.decode().strip().lower()
        if headers.get('transfer-encoding')=='chunked': body=_decode_chunked(body)
        return {'available':code==200,'httpStatus':code,'payload':json.loads(body.decode()) if code==200 else None,'error':None if code==200 else body.decode('utf-8','replace')[-1000:]}
    except Exception as exc:
        return {'available':False,'httpStatus':None,'payload':None,'error':str(exc)}

def _cpu_percent(stats: dict[str,Any]) -> float|None:
    cpu=stats.get('cpu_stats') or {}; pre=stats.get('precpu_stats') or {}
    total=((cpu.get('cpu_usage') or {}).get('total_usage')); pre_total=((pre.get('cpu_usage') or {}).get('total_usage'))
    system=cpu.get('system_cpu_usage'); pre_system=pre.get('system_cpu_usage')
    online=cpu.get('online_cpus') or len((cpu.get('cpu_usage') or {}).get('percpu_usage') or []) or 1
    vals=(total,pre_total,system,pre_system)
    if not all(isinstance(v,(int,float)) for v in vals): return None
    cd=total-pre_total; sd=system-pre_system
    return round((cd/sd)*online*100,2) if sd>0 and cd>=0 else None

def _container_metrics() -> dict[str,Any]:
    r=_docker_json(f"/containers/{quote(BCH_NODE_CONTAINER,safe='')}/stats?stream=false")
    if not r['available']: return {'available':False,'error':r['error'],'cpuPercent':None,'memory':{},'blockIo':{}}
    p=r['payload']; mem=p.get('memory_stats') or {}; usage=mem.get('usage'); limit=mem.get('limit'); cache=(mem.get('stats') or {}).get('cache') or 0
    working=max(0,usage-cache) if isinstance(usage,(int,float)) else None
    mp=round(working/limit*100,2) if isinstance(working,(int,float)) and isinstance(limit,(int,float)) and limit>0 else None
    rd=wr=0
    for item in ((p.get('blkio_stats') or {}).get('io_service_bytes_recursive') or []):
        op=str(item.get('op','')).lower(); val=int(item.get('value') or 0)
        if op=='read': rd+=val
        elif op=='write': wr+=val
    return {'available':True,'cpuPercent':_cpu_percent(p),'memory':{'usageBytes':usage,'workingSetBytes':working,'limitBytes':limit,'usedPercent':mp},'blockIo':{'readBytes':rd,'writeBytes':wr}}

def _peer_analysis() -> dict[str,Any]:
    r=call_rpc('getpeerinfo'); raw=r.get('result') if isinstance(r.get('result'),list) else []; peers=[]
    for peer in raw:
        ping=peer.get('pingtime')
        peers.append({'id':peer.get('id'),'address':peer.get('addr'),'inbound':bool(peer.get('inbound')),'connectionType':peer.get('connection_type') or peer.get('connectiontype'),'pingMs':round(float(ping)*1000,2) if isinstance(ping,(int,float)) else None,'syncedHeaders':peer.get('synced_headers'),'syncedBlocks':peer.get('synced_blocks'),'startingHeight':peer.get('startingheight'),'connectedSeconds':max(0,int(time.time())-int(peer.get('conntime'))) if isinstance(peer.get('conntime'),(int,float)) else None,'subver':peer.get('subver')})
    pings=[x['pingMs'] for x in peers if isinstance(x.get('pingMs'),(int,float))]; out=[x for x in peers if not x['inbound']]
    return {'reachable':bool(r.get('reachable')),'count':len(peers),'outboundCount':len(out),'inboundCount':len(peers)-len(out),'averagePingMs':round(sum(pings)/len(pings),2) if pings else None,'bestPingMs':min(pings) if pings else None,'peers':peers,'error':r.get('transportError') or r.get('rpcError')}

def _snapshot() -> dict[str,Any]:
    runtime=probe_bch_runtime(); op=runtime.get('operationalState') if isinstance(runtime.get('operationalState'),dict) else {}; probe=((runtime.get('rpc') or {}).get('probe') or {}); status=(((runtime.get('rpc') or {}).get('status') or {}).get('payload') or {}); storage=status.get('storage') if isinstance(status.get('storage'),dict) else {}
    return {'timestamp':time.time(),'state':op.get('state'),'height':probe.get('height'),'headers':probe.get('headers'),'verificationProgress':probe.get('verificationProgress'),'progressPercent':probe.get('progressPercent'),'peers':probe.get('peers'),'chainBytes':storage.get('usedBytes'),'rpcHealthy':op.get('rpcHealthy'),'initialBlockDownload':op.get('initialBlockDownload')}

def _delta(new:dict[str,Any], old:dict[str,Any]) -> dict[str,Any]:
    sec=max(.001,float(new['timestamp'])-float(old['timestamp']))
    def rate(field):
        a,b=new.get(field),old.get(field)
        return (float(a)-float(b))/sec if isinstance(a,(int,float)) and isinstance(b,(int,float)) else None
    bps=rate('height'); vp=rate('verificationProgress'); cb=rate('chainBytes')
    return {'seconds':sec,'blocksPerSecond':bps,'blocksPerMinute':bps*60 if bps is not None else None,'progressPerHour':vp*3600 if vp is not None else None,'chainBytesPerSecond':cb}

def _window(current:dict[str,Any], back:int):
    candidates=[x for x in OBSERVATIONS if x['timestamp'] <= current['timestamp']-back]
    if candidates: return _delta(current,candidates[-1])
    if len(OBSERVATIONS)>=2 and current['timestamp']-OBSERVATIONS[0]['timestamp']>=10: return _delta(current,OBSERVATIONS[0])
    return None

def analyze() -> dict[str,Any]:
    current=_snapshot(); OBSERVATIONS.append(current); peers=_peer_analysis(); resources=_container_metrics(); latest=_window(current,10); five=_window(current,300); fifteen=_window(current,900); rate=five or latest or {}; bps=rate.get('blocksPerSecond'); remaining=(current.get('headers')-current.get('height')) if isinstance(current.get('headers'),int) and isinstance(current.get('height'),int) else None; eta=int(remaining/bps) if isinstance(remaining,int) and isinstance(bps,(int,float)) and bps>0 else None
    recs=[]; pc=int(peers.get('count') or 0); cpu=resources.get('cpuPercent'); bpm=rate.get('blocksPerMinute')
    if pc<=2: recs.append({'severity':'warning','code':'low-peer-count','message':f'Only {pc} peers are connected. Peer availability may be limiting block delivery.'})
    if isinstance(cpu,(int,float)) and cpu>=300: recs.append({'severity':'info','code':'cpu-busy','message':f'Node container CPU is using {cpu:.1f}% across available cores; validation may be CPU-bound.'})
    if isinstance(bpm,(int,float)) and bpm<=1: recs.append({'severity':'warning','code':'low-validation-throughput','message':f'Observed throughput is only {bpm:.2f} blocks/minute.'})
    if not recs: recs.append({'severity':'info','code':'sync-progressing','message':'No obvious bottleneck was detected in this observation window.'})
    bottleneck='peer-limited' if pc<=2 else ('cpu-limited' if isinstance(cpu,(int,float)) and cpu>=300 else ('slow-validation' if isinstance(bpm,(int,float)) and bpm<=1 else 'undetermined'))
    return {'contract':'seymour.bch-sync-performance','version':'1.0','observedAt':current['timestamp'],'snapshot':current,'throughput':{'latest':latest,'fiveMinute':five,'fifteenMinute':fifteen,'etaSeconds':eta,'observationCount':len(OBSERVATIONS)},'peers':peers,'resources':resources,'analysis':{'likelyBottleneck':bottleneck,'recommendations':recs},'safety':{'readOnly':True,'configurationChanged':False,'lifecycleActionExecuted':False}}
