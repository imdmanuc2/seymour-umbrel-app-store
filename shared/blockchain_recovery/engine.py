from pathlib import Path
import json, shutil, socket, subprocess
from .models import Finding,RecoveryKind,RecoveryReport,RecoveryState

def _findmnt(path:Path):
    r=subprocess.run(["findmnt","-J","-T",str(path)],capture_output=True,text=True)
    if r.returncode or not r.stdout.strip(): return None
    try:
        f=json.loads(r.stdout)["filesystems"][0]
        return {"target":f.get("target",""),"source":f.get("source",""),"fstype":f.get("fstype","")}
    except Exception: return None

def storage_mount_finding(target_path:Path,provider_id:str,expected_source=None,expected_fstype=None):
    if not target_path.exists():
        return Finding(RecoveryKind.STORAGE_MOUNT_MISSING,RecoveryState.BLOCKED,
            f"Configured storage path is missing: {target_path}",True,
            f"RECOVER-STORAGE-{provider_id}",{"path":str(target_path)})
    m=_findmnt(target_path)
    if m is None or Path(m["target"]).resolve()!=target_path.resolve():
        return Finding(RecoveryKind.STORAGE_MOUNT_MISSING,RecoveryState.BLOCKED,
            "Configured storage path exists but is not its own mounted filesystem.",True,
            f"RECOVER-STORAGE-{provider_id}",{"path":str(target_path),"mount":m})
    errors=[]
    if expected_source and m["source"]!=expected_source: errors.append("source-mismatch")
    if expected_fstype and m["fstype"]!=expected_fstype: errors.append("filesystem-mismatch")
    if errors:
        return Finding(RecoveryKind.STORAGE_MOUNT_MISSING,RecoveryState.BLOCKED,
            "Mounted storage identity does not match configured target.",False,
            evidence={"mount":m,"errors":errors})
    return None

def warmup_finding(rpc_output:str):
    t=rpc_output.lower()
    if "error code: -28" in t or "verifying blocks" in t or "loading block index" in t:
        return Finding(RecoveryKind.STARTUP_WARMUP,RecoveryState.RECOVERING,
            "Blockchain runtime is warming up or verifying existing block data.",
            evidence={"rpcOutput":rpc_output[-1000:]})
    return None

def dns_alias_finding(alias:str):
    try: answers=sorted({x[4][0] for x in socket.getaddrinfo(alias,None,socket.AF_INET)})
    except socket.gaierror as e:
        return Finding(RecoveryKind.DNS_ALIAS_COLLISION,RecoveryState.BLOCKED,
            f"DNS alias does not resolve: {alias}",evidence={"error":str(e)})
    if len(answers)>1:
        return Finding(RecoveryKind.DNS_ALIAS_COLLISION,RecoveryState.DEGRADED,
            f"DNS alias resolves to multiple endpoints: {alias}",evidence={"addresses":answers})
    return None

def registration_missing_finding(installed_app_path:Path,external_data_path:Path):
    has_chain=(external_data_path/"blocks").is_dir() and (external_data_path/"chainstate").is_dir()
    if has_chain and not (installed_app_path/"umbrel-app.yml").is_file():
        return Finding(RecoveryKind.REGISTRATION_MISSING,RecoveryState.BLOCKED,
            "Existing blockchain data found but Umbrel registration is incomplete.",
            evidence={"installedAppPath":str(installed_app_path),"externalDataPath":str(external_data_path)})
    return None

def suspicious_fresh_sync_finding(external_data_path:Path,live_blocks:int,live_size_on_disk:int):
    try:
        r=subprocess.run(["du","-s","-B1",str(external_data_path)],capture_output=True,text=True,timeout=60)
        ext=int(r.stdout.split()[0]) if r.returncode==0 and r.stdout.strip() else 0
    except Exception: ext=0
    if ext>=10_000_000_000 and live_blocks<100_000 and live_size_on_disk<1_000_000_000:
        return Finding(RecoveryKind.SUSPICIOUS_FRESH_SYNC,RecoveryState.BLOCKED,
            "Large external dataset exists but live runtime looks like a fresh sync. Stop and verify /data binding.",
            evidence={"externalSizeBytes":ext,"liveBlocks":live_blocks,"liveSizeOnDisk":live_size_on_disk})
    return None

def plan(provider_id:str,runtime_host:str,storage_target=None,expected_source=None,expected_fstype=None,
         dns_alias=None,installed_app_path=None,external_data_path=None,rpc_output=None,
         live_blocks=None,live_size_on_disk=None):
    fs=[]
    if storage_target:
        f=storage_mount_finding(Path(storage_target),provider_id,expected_source,expected_fstype)
        if f: fs.append(f)
    if dns_alias:
        f=dns_alias_finding(dns_alias)
        if f: fs.append(f)
    if rpc_output:
        f=warmup_finding(rpc_output)
        if f: fs.append(f)
    if installed_app_path and external_data_path:
        f=registration_missing_finding(Path(installed_app_path),Path(external_data_path))
        if f: fs.append(f)
    if external_data_path is not None and live_blocks is not None and live_size_on_disk is not None:
        f=suspicious_fresh_sync_finding(Path(external_data_path),live_blocks,live_size_on_disk)
        if f: fs.append(f)
    state=RecoveryState.HEALTHY
    if any(x.state==RecoveryState.BLOCKED for x in fs): state=RecoveryState.BLOCKED
    elif any(x.state==RecoveryState.RECOVERING for x in fs): state=RecoveryState.RECOVERING
    elif fs: state=RecoveryState.DEGRADED
    return RecoveryReport(provider_id,runtime_host,state,fs)

def execute_safe_repairs(report,confirmation=None,mount_target=None):
    report.executed=True; report.success=True
    for f in report.findings:
        if not f.repairable: continue
        if confirmation!=f.confirmation:
            report.steps.append({"kind":f.kind.value,"success":False,"error":"confirmation-mismatch",
                                 "requiredConfirmation":f.confirmation})
            report.success=False; continue
        if f.kind==RecoveryKind.STORAGE_MOUNT_MISSING and mount_target:
            r=subprocess.run(["mount",str(mount_target)],capture_output=True,text=True)
            step={"kind":f.kind.value,"command":["mount",str(mount_target)],
                  "returnCode":r.returncode,"stdout":r.stdout.strip(),"stderr":r.stderr.strip(),
                  "success":r.returncode==0}
            report.steps.append(step)
            report.success=report.success and step["success"]
    return report
