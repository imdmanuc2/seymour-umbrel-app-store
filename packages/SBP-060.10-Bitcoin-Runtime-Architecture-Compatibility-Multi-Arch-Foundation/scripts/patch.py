#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# Recovery kind
models = ROOT / "shared/blockchain_recovery/models.py"
text = models.read_text()
if "RUNTIME_IMAGE_ARCHITECTURE_MISMATCH" not in text:
    anchor = '    RUNTIME_PORT_CONFLICT="runtime-port-conflict"\n'
    if anchor not in text:
        raise SystemExit("SBP-060.9 RecoveryKind anchor not found")
    text = text.replace(
        anchor,
        anchor + '    RUNTIME_IMAGE_ARCHITECTURE_MISMATCH="runtime-image-architecture-mismatch"\n',
        1,
    )
models.write_text(text)

# Recovery engine
engine = ROOT / "shared/blockchain_recovery/engine.py"
text = engine.read_text()

import_anchor = "from .port_guard import inspect_port_conflict\n"
import_line = "from .image_architecture import image_architecture_finding_payload\n"
if import_line not in text:
    if import_anchor not in text:
        raise SystemExit("SBP-060.9 engine import anchor not found")
    text = text.replace(import_anchor, import_anchor + import_line, 1)

if "def runtime_image_architecture_finding(" not in text:
    marker = "def runtime_port_conflict_finding("
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("runtime_port_conflict_finding anchor not found")

    addition = (
        "def runtime_image_architecture_finding(provider_id:str,image:str):\n"
        "    result=image_architecture_finding_payload(image)\n"
        "    if not result[\"conflict\"]:\n"
        "        return None\n"
        "    return Finding(\n"
        "        RecoveryKind.RUNTIME_IMAGE_ARCHITECTURE_MISMATCH,\n"
        "        RecoveryState.BLOCKED,\n"
        "        \"Runtime container image architecture does not match the runtime host. Install/start is blocked.\",\n"
        "        False,\n"
        "        evidence={\"providerId\":provider_id,**result},\n"
        "    )\n\n"
    )
    text = text[:idx] + addition + text[idx:]

old_sig = (
    "def plan(provider_id:str,runtime_host:str,storage_target=None,expected_source=None,expected_fstype=None,\n"
    "         dns_alias=None,installed_app_path=None,external_data_path=None,rpc_output=None,\n"
    "         live_blocks=None,live_size_on_disk=None,requested_host_port=None,candidate_host_ports=None):\n"
)
new_sig = (
    "def plan(provider_id:str,runtime_host:str,storage_target=None,expected_source=None,expected_fstype=None,\n"
    "         dns_alias=None,installed_app_path=None,external_data_path=None,rpc_output=None,\n"
    "         live_blocks=None,live_size_on_disk=None,requested_host_port=None,candidate_host_ports=None,\n"
    "         runtime_image=None):\n"
)

if old_sig in text:
    text = text.replace(old_sig, new_sig, 1)
elif "runtime_image=None" not in text:
    raise SystemExit("recovery plan signature anchor not found")

plan_anchor = (
    "    if requested_host_port is not None:\n"
    "        f=runtime_port_conflict_finding(\n"
    "            provider_id,\n"
    "            int(requested_host_port),\n"
    "            [int(x) for x in (candidate_host_ports or [])],\n"
    "        )\n"
    "        if f: fs.append(f)\n"
)

if "if runtime_image is not None:" not in text:
    if plan_anchor not in text:
        raise SystemExit("port conflict plan anchor not found")
    text = text.replace(
        plan_anchor,
        plan_anchor
        + "    if runtime_image is not None:\n"
          "        f=runtime_image_architecture_finding(provider_id,str(runtime_image))\n"
          "        if f: fs.append(f)\n",
        1,
    )

engine.write_text(text)

# Recovery CLI
cli = ROOT / "scripts/seymour-blockchain-heal"
text = cli.read_text()

if '--runtime-image' not in text:
    anchor = 'p.add_argument("--candidate-host-port",action="append",type=int,default=[])\n'
    if anchor not in text:
        raise SystemExit("SBP-060.9 CLI candidate-port anchor not found")
    text = text.replace(
        anchor,
        anchor + 'p.add_argument("--runtime-image")\n',
        1,
    )

if "runtime_image=a.runtime_image" not in text:
    old_tail = (
        "       requested_host_port=a.requested_host_port,\n"
        "       candidate_host_ports=a.candidate_host_port)\n"
    )
    new_tail = (
        "       requested_host_port=a.requested_host_port,\n"
        "       candidate_host_ports=a.candidate_host_port,\n"
        "       runtime_image=a.runtime_image)\n"
    )
    if old_tail not in text:
        raise SystemExit("SBP-060.9 CLI plan call anchor not found")
    text = text.replace(old_tail, new_tail, 1)

cli.write_text(text)

# Guard the managed Bitcoin CLI wrapper before install/start.
wrapper = ROOT / "scripts/seymour-bitcoin-managed-runtime"
text = wrapper.read_text()

guard_marker = "# SBP-060.10 architecture guard"
if guard_marker not in text:
    shebang_end = text.find("\n")
    if shebang_end < 0:
        raise SystemExit("Bitcoin managed runtime wrapper shebang not found")

    guard = '''
# SBP-060.10 architecture guard
case " $* " in
  *" install "*|*" start "*)
    "$(dirname "$0")/seymour-bitcoin-architecture-preflight" \
      --require-compatible
    ;;
esac
'''
    text = text[:shebang_end + 1] + guard + text[shebang_end + 1:]

wrapper.write_text(text)

print("SBP-060.10 source patch: PASS")
