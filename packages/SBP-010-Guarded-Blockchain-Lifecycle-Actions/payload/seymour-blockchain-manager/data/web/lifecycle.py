from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
import json, os, subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4
CONTROL_SCRIPT=Path(os.environ.get('SEYMOUR_UMBREL_CONTROL_SCRIPT','/control/seymour-umbrel-app'))
EVIDENCE_PATH=Path(os.environ.get('LIFECYCLE_EVIDENCE_PATH','/evidence/lifecycle.jsonl'))
ALLOWED_PROVIDER_ID='bitcoin-cash-mainnet'
ALLOWED_APP_ID=os.environ.get('BCH_APP_ID','seymour-bch-node')
class LifecycleAction(StrEnum):
 STATE='state'; START='start'; STOP='stop'; RESTART='restart'
class LifecycleStatus(StrEnum):
 PLANNED='planned'; SUCCEEDED='succeeded'; FAILED='failed'
@dataclass
class LifecycleResult:
 operation_id:str;provider_id:str;app_id:str;action:LifecycleAction;status:LifecycleStatus;created_at:str;required_confirmation:str|None=None;executed:bool=False;result:Any=None;post_action_state:Any=None;error:str|None=None
 def to_dict(self):
  d=asdict(self);d['action']=self.action.value;d['status']=self.status.value;return d
def utc_now(): return datetime.now(UTC).isoformat()
def confirmation_token(action,app_id): return f'{action.value.upper()}-{app_id}'
class LifecycleEvidenceStore:
 def __init__(self,path=EVIDENCE_PATH): self.path=path
 def append(self,result):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  with self.path.open('a',encoding='utf-8') as h:h.write(json.dumps(result.to_dict(),sort_keys=True)+'\n')
class GuardedLifecycleService:
 def __init__(self,control_script=CONTROL_SCRIPT,evidence_store=None): self.control_script=control_script;self.evidence_store=evidence_store or LifecycleEvidenceStore()
 def _validate_target(self,provider_id,app_id):
  if provider_id!=ALLOWED_PROVIDER_ID: raise ValueError('Provider is not enabled for lifecycle actions.')
  if app_id!=ALLOWED_APP_ID: raise ValueError('App ID is not enabled for lifecycle actions.')
 def _invoke(self,action,app_id):
  if not self.control_script.is_file(): raise RuntimeError(f'Control script is unavailable: {self.control_script}')
  cmd=[str(self.control_script),action.value,app_id]
  if action is not LifecycleAction.STATE: cmd += ['--execute','--confirm',confirmation_token(action,app_id)]
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=120,check=False)
  if p.returncode!=0: raise RuntimeError(p.stderr.strip() or p.stdout.strip() or f'Lifecycle command exited {p.returncode}')
  try:return json.loads(p.stdout)
  except json.JSONDecodeError as e: raise RuntimeError('Lifecycle command returned invalid JSON.') from e
 def plan(self,provider_id,app_id,action):
  self._validate_target(provider_id,app_id)
  r=LifecycleResult(str(uuid4()),provider_id,app_id,action,LifecycleStatus.PLANNED,utc_now(),None if action is LifecycleAction.STATE else confirmation_token(action,app_id))
  self.evidence_store.append(r);return r
 def execute(self,provider_id,app_id,action,confirmation):
  r=self.plan(provider_id,app_id,action)
  if action is not LifecycleAction.STATE and confirmation!=r.required_confirmation:
   r.status=LifecycleStatus.FAILED;r.error='Confirmation token did not match.';self.evidence_store.append(r);return r
  try:
   r.result=self._invoke(action,app_id);r.executed=True;r.post_action_state=r.result if action is LifecycleAction.STATE else self._invoke(LifecycleAction.STATE,app_id);r.status=LifecycleStatus.SUCCEEDED
  except Exception as e:r.status=LifecycleStatus.FAILED;r.error=str(e)
  self.evidence_store.append(r);return r
