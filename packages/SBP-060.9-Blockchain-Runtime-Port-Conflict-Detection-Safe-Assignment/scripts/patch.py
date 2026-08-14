#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# Recovery kind
models = ROOT / "shared/blockchain_recovery/models.py"
text = models.read_text()
if "RUNTIME_PORT_CONFLICT" not in text:
    anchor = '    SUSPICIOUS_FRESH_SYNC="suspicious-fresh-sync"\n'
    if anchor not in text:
        raise SystemExit("RecoveryKind anchor not found")
    text = text.replace(
        anchor,
        anchor + '    RUNTIME_PORT_CONFLICT="runtime-port-conflict"\n',
        1,
    )
models.write_text(text)

# Recovery engine
engine = ROOT / "shared/blockchain_recovery/engine.py"
text = engine.read_text()

import_anchor = "from .models import Finding,RecoveryKind,RecoveryReport,RecoveryState\n"
if "from .port_guard import inspect_port_conflict" not in text:
    if import_anchor not in text:
        raise SystemExit("engine import anchor not found")
    text = text.replace(
        import_anchor,
        import_anchor + "from .port_guard import inspect_port_conflict\n",
        1,
    )

if "def runtime_port_conflict_finding(" not in text:
    anchor = "def suspicious_fresh_sync_finding("
    idx = text.find(anchor)
    if idx < 0:
        raise SystemExit("engine function anchor not found")

    addition = '''def runtime_port_conflict_finding(
    provider_id:str,
    requested_port:int,
    candidate_ports:list[int],
):
    result=inspect_port_conflict(
        requested_port=requested_port,
        candidates=candidate_ports,
    )
    if not result["conflict"]:
        return None
    return Finding(
        RecoveryKind.RUNTIME_PORT_CONFLICT,
        RecoveryState.BLOCKED,
        f"Requested host TCP port {requested_port} is already in use. Existing owner will not be stopped automatically.",
        False,
        evidence={"providerId":provider_id, **result},
    )

'''
    text = text[:idx] + addition + text[idx:]

old_sig = '''def plan(provider_id:str,runtime_host:str,storage_target=None,expected_source=None,expected_fstype=None,
         dns_alias=None,installed_app_path=None,external_data_path=None,rpc_output=None,
         live_blocks=None,live_size_on_disk=None):
'''
new_sig = '''def plan(provider_id:str,runtime_host:str,storage_target=None,expected_source=None,expected_fstype=None,
         dns_alias=None,installed_app_path=None,external_data_path=None,rpc_output=None,
         live_blocks=None,live_size_on_disk=None,requested_host_port=None,candidate_host_ports=None):
'''
if old_sig in text:
    text = text.replace(old_sig, new_sig, 1)

plan_anchor = '''    if external_data_path is not None and live_blocks is not None and live_size_on_disk is not None:
        f=suspicious_fresh_sync_finding(Path(external_data_path),live_blocks,live_size_on_disk)
        if f: fs.append(f)
'''
if "requested_host_port is not None" not in text:
    if plan_anchor not in text:
        raise SystemExit("plan body anchor not found")
    text = text.replace(
        plan_anchor,
        plan_anchor + '''    if requested_host_port is not None:
        f=runtime_port_conflict_finding(
            provider_id,
            int(requested_host_port),
            [int(x) for x in (candidate_host_ports or [])],
        )
        if f: fs.append(f)
''',
        1,
    )

engine.write_text(text)

# Recovery CLI
cli = ROOT / "scripts/seymour-blockchain-heal"
text = cli.read_text()
if '--requested-host-port' not in text:
    anchor = 'p.add_argument("--storage-target"); p.add_argument("--expected-source"); p.add_argument("--expected-fstype")\n'
    if anchor not in text:
        raise SystemExit("recovery CLI argument anchor not found")
    text = text.replace(
        anchor,
        anchor
        + 'p.add_argument("--requested-host-port",type=int)\n'
        + 'p.add_argument("--candidate-host-port",action="append",type=int,default=[])\n',
        1,
    )

call_old = '''r=plan(a.provider_id,a.runtime_host,a.storage_target,a.expected_source,a.expected_fstype,
       a.dns_alias,a.installed_app_path,a.external_data_path,a.rpc_output,a.live_blocks,a.live_size_on_disk)
'''
call_new = '''r=plan(a.provider_id,a.runtime_host,a.storage_target,a.expected_source,a.expected_fstype,
       a.dns_alias,a.installed_app_path,a.external_data_path,a.rpc_output,a.live_blocks,a.live_size_on_disk,
       requested_host_port=a.requested_host_port,
       candidate_host_ports=a.candidate_host_port)
'''
if "requested_host_port=a.requested_host_port" not in text:
    if call_old not in text:
        raise SystemExit("recovery CLI plan-call anchor not found")
    text = text.replace(call_old, call_new, 1)

cli.write_text(text)

# BTC source Compose
compose = ROOT / "seymour-bitcoin-node/docker-compose.yml"
text = compose.read_text()
old = '      - "8333:8333"\n'
new = '      - "${BTC_P2P_HOST_PORT:-8335}:8333"\n'
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("BTC port mapping anchor not found")
compose.write_text(text)

print("SBP-060.9 source patch: PASS")
