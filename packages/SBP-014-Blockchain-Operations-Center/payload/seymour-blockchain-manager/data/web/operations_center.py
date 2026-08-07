from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from enum import StrEnum
import json, os, subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4
APP_ID=os.environ.get("BCH_APP_ID","seymour-bch-node")
NODE_CONTAINER=os.environ.get("BCH_NODE_CONTAINER","seymour-bch-node_node_1")
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
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,check=False)
 return {'returnCode':c.returncode,'stdout':c.stdout[-20000:],'stderr':c.stderr[-20000:],'success':c.returncode==0}
def diagnostics():
 r=OperationResult(str(uuid4()),OperationKind.DIAGNOSTICS,OperationStatus.PLANNED,now(),None)
 payload={'state':run([str(CONTROL_SCRIPT),'state',APP_ID]),'container':run(['docker','inspect',NODE_CONTAINER]),'rpc':run(['docker','exec',NODE_CONTAINER,'bitcoin-cli','-rpcwait=0','getblockchaininfo'],20)}
 r.result=payload;r.status=OperationStatus.SUCCEEDED if payload['state']['success'] else OperationStatus.FAILED
 if r.status is OperationStatus.FAILED:r.error='One or more diagnostics failed.'
 evidence(r);HEALTH_HISTORY_PATH.parent.mkdir(parents=True,exist_ok=True);HEALTH_HISTORY_PATH.write_text(json.dumps({'capturedAt':now(),'diagnostics':payload})+'\n')
 return r
def recent_logs(lines=200):
 r=OperationResult(str(uuid4()),OperationKind.LOGS,OperationStatus.PLANNED,now(),None)
 r.result=run(['docker','logs','--tail',str(max(10,min(int(lines),1000))),NODE_CONTAINER]);r.status=OperationStatus.SUCCEEDED if r.result['success'] else OperationStatus.FAILED
 if r.status is OperationStatus.FAILED:r.error='Unable to read node logs.'
 evidence(r);return r
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

