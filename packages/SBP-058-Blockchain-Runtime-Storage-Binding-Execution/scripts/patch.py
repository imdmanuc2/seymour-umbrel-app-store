#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()

def patch_compose(path):
    text = path.read_text()
    text = text.replace(
        "- ${APP_DATA_DIR}/data/node:/data",
        "- ${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data",
        1,
    )
    text = text.replace(
        "- ${APP_DATA_DIR}/data/node:/node-data:ro",
        "- ${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data:ro",
        1,
    )
    text = text.replace(
        "- ${APP_DATA_DIR}/data/node:/node-data",
        "- ${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data",
        1,
    )
    path.write_text(text)

patch_compose(repo/"seymour-bitcoin-node/docker-compose.yml")
patch_compose(repo/"seymour-bch-node/docker-compose.yml")

path = repo/"seymour-blockchain-manager/data/web/installer.py"
text = path.read_text()

if "from shared.blockchain_install.binding import build_binding_plan" not in text:
    text = text.replace(
        "from shared.blockchain_install.host import profile as host_profile\n",
        "from shared.blockchain_install.host import profile as host_profile\nfrom shared.blockchain_install.binding import build_binding_plan\n",
        1,
    )

anchor = "        env = os.environ.copy()\n        env.update({\"BCH_RPC_USER\": value.rpc_user, \"BCH_RPC_PASSWORD\": value.rpc_password, \"BCH_RPC_PORT\": str(value.rpc_port), \"BCH_P2P_PORT\": str(value.p2p_port), \"SEYMOUR_NODE_NAME\": value.node_name})\n        try:\n"
replacement = '''        env = os.environ.copy()
        selected_target = target_by_id(value.storage_target_id)
        if selected_target is None:
            operation.status = InstallStatus.FAILED
            operation.error = "Selected storage target disappeared before execution."
            operation.updated_at = utc_now()
            self._save(operation)
            return operation

        binding = build_binding_plan(
            provider_id=value.provider_id,
            runtime_host=socket.gethostname(),
            storage_target=selected_target,
        )
        operation.preflight["storageBinding"] = binding.to_dict()

        if not binding.eligible:
            operation.status = InstallStatus.FAILED
            operation.error = "Selected storage target is not eligible for runtime binding."
            operation.updated_at = utc_now()
            self._save(operation)
            return operation

        data_path = Path(binding.data_path)
        try:
            data_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            operation.status = InstallStatus.FAILED
            operation.error = f"Unable to prepare selected blockchain data path: {exc}"
            operation.updated_at = utc_now()
            self._save(operation)
            return operation

        env.update({
            "BCH_RPC_USER": value.rpc_user,
            "BCH_RPC_PASSWORD": value.rpc_password,
            "BCH_RPC_PORT": str(value.rpc_port),
            "BCH_P2P_PORT": str(value.p2p_port),
            "SEYMOUR_NODE_NAME": value.node_name,
            "SEYMOUR_BLOCKCHAIN_DATA_PATH": str(data_path),
        })
        try:
'''
if anchor not in text:
    raise SystemExit("SBP-058 installer env anchor not found")
text = text.replace(anchor, replacement, 1)

anchor2 = '            operation.result = json.loads(completed.stdout)\n            state = subprocess.run([str(self.control_script), "state", BCH_APP_ID], capture_output=True, text=True, timeout=120, check=False)\n            operation.verification = {"state": json.loads(state.stdout) if state.stdout else None, "verified": state.returncode == 0}\n            operation.status = InstallStatus.SUCCEEDED if operation.verification["verified"] else InstallStatus.FAILED\n'
replacement2 = '''            operation.result = json.loads(completed.stdout)
            state = subprocess.run([str(self.control_script), "state", BCH_APP_ID], capture_output=True, text=True, timeout=120, check=False)

            mount_verify = subprocess.run(
                ["docker", "inspect", f"{BCH_APP_ID}_node_1", "--format", "{{json .Mounts}}"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            mount_source = None
            if mount_verify.returncode == 0 and mount_verify.stdout.strip():
                try:
                    mounts = json.loads(mount_verify.stdout)
                    for item in mounts:
                        if item.get("Destination") == "/data":
                            mount_source = item.get("Source")
                            break
                except Exception:
                    mount_source = None

            requested_source = str(data_path.resolve())
            mount_matches = (
                mount_source is not None
                and str(Path(mount_source).resolve()) == requested_source
            )

            operation.verification = {
                "state": json.loads(state.stdout) if state.stdout else None,
                "stateVerified": state.returncode == 0,
                "storageBinding": binding.to_dict(),
                "requestedDataPath": requested_source,
                "runtimeDataMountSource": mount_source,
                "runtimeDataMountMatches": mount_matches,
                "verified": state.returncode == 0 and mount_matches,
            }
            operation.status = InstallStatus.SUCCEEDED if operation.verification["verified"] else InstallStatus.FAILED
            if not mount_matches:
                operation.error = "Runtime /data mount does not match the selected storage target."
'''
if anchor2 not in text:
    raise SystemExit("SBP-058 installer verify anchor not found")
text = text.replace(anchor2, replacement2, 1)
path.write_text(text)

print("SBP-058 patch: PASS")
