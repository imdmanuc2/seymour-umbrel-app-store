#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys

repo = Path(sys.argv[1]).resolve()
app_dir = repo / "seymour-blockchain-manager"
compose = app_dir / "docker-compose.yml"

text = compose.read_text()

old_env_file = """    env_file:
      - /home/umbrel/seymour-umbrel-app-store-git/private/nexus-registration.env

"""
if old_env_file in text:
    text = text.replace(old_env_file, "", 1)

text = text.replace(
    "- /home/umbrel/seymour-umbrel-app-store-git/scripts:/control:ro",
    "- ${APP_DATA_DIR}/data/control:/control:ro",
    1,
)
text = text.replace(
    "- /home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro",
    "- ${APP_DATA_DIR}/data/shared:/seymour-platform/shared:ro",
    1,
)

anchor = "      SEYMOUR_PLATFORM_ROOT: /seymour-platform\n"
if "      PYTHONPATH: /seymour-platform\n" not in text:
    if anchor not in text:
        raise SystemExit("SBP-060.1 PYTHONPATH anchor not found")
    text = text.replace(anchor, anchor + "      PYTHONPATH: /seymour-platform\n", 1)

compose.write_text(text)

control_dir = app_dir / "data" / "control"
control_dir.mkdir(parents=True, exist_ok=True)

for name in ("seymour-umbrel-app", "seymour-install-bch", "seymour-install-btc"):
    src = repo / "scripts" / name
    if not src.is_file():
        raise SystemExit(f"Required control script missing: {src}")
    dst = control_dir / name
    shutil.copy2(src, dst)
    dst.chmod(0o755)

source_shared = repo / "shared"
target_shared = app_dir / "data" / "shared"

if target_shared.exists():
    shutil.rmtree(target_shared)

shutil.copytree(
    source_shared,
    target_shared,
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
)

print("SBP-060.1 portable Blockchain Manager payload: PASS")
