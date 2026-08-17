#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"{label}: anchor not found")
    return text.replace(old, new, 1)


def patch_app_js(path: Path) -> None:
    text = path.read_text()
    old = '''  if (provider.availability !== "live") {
    return {state: rawState, telemetry, graceHeld: false};
  }

  const current = state.runtimePresentation[providerId] || null;
'''
    new = '''  if (provider.availability !== "live") {
    return {state: rawState, telemetry, graceHeld: false};
  }

  // Definitive lifecycle states must never be hidden by the sync telemetry
  // grace window. Clear any remembered syncing presentation immediately.
  if (["stopped", "offline", "not-installed"].includes(rawState)) {
    delete state.runtimePresentation[providerId];
    return {
      state: rawState,
      telemetry,
      graceHeld: false,
      authoritativeLifecycle: true,
    };
  }

  const current = state.runtimePresentation[providerId] || null;
'''
    path.write_text(replace_once(text, old, new, "app.js lifecycle precedence"))


def patch_telemetry(path: Path) -> None:
    text = path.read_text()
    old = '''    runtime_state = operational_state.get("state") or runtime.get("lifecycleStatus") or "unknown"

    progress = rpc_probe.get("progressPercent")
'''
    new = '''    runtime_state = operational_state.get("state") or runtime.get("lifecycleStatus") or "unknown"

    # Container/runtime presence is authoritative for terminal lifecycle state.
    # Slow or cached RPC telemetry may describe an earlier syncing state, but it
    # must not make a stopped managed app appear to still be running.
    installed = bool(runtime.get("installed"))
    running = bool(runtime.get("running"))
    if not installed:
        runtime_state = "not-installed"
    elif not running:
        runtime_state = "stopped"

    progress = rpc_probe.get("progressPercent")
'''
    text = replace_once(text, old, new, "telemetry.py runtime precedence")

    old2 = '''        "installed": bool(runtime.get("installed")),
        "running": bool(runtime.get("running")),
'''
    new2 = '''        "installed": installed,
        "running": running,
'''
    text = replace_once(text, old2, new2, "telemetry.py canonical booleans")
    path.write_text(text)


def patch_status(path: Path) -> None:
    text = path.read_text()

    marker = "from __future__ import annotations\n"
    imports = "from __future__ import annotations\n\nimport subprocess\nimport threading\nimport time\n"
    if "import threading\n" not in text or "import subprocess\n" not in text or "import time\n" not in text:
        if marker not in text:
            raise RuntimeError("status app imports: future anchor not found")
        # Insert only missing imports while keeping existing import ordering harmless.
        additions = []
        if "import subprocess\n" not in text:
            additions.append("import subprocess")
        if "import threading\n" not in text:
            additions.append("import threading")
        if "import time\n" not in text:
            additions.append("import time")
        text = text.replace(marker, marker + "\n" + "\n".join(additions) + "\n", 1)

    data_anchor = '''DATA_PATH = Path(
    os.environ.get(
        "BCH_DATA_PATH",
        "/node-data",
    )
)


'''
    cache_block = '''DATA_PATH = Path(
    os.environ.get(
        "BCH_DATA_PATH",
        "/node-data",
    )
)

STORAGE_FOOTPRINT_TTL_SECONDS = max(
    60,
    int(os.environ.get("BCH_STORAGE_FOOTPRINT_TTL_SECONDS", "900")),
)
STORAGE_FOOTPRINT_TIMEOUT_SECONDS = max(
    2,
    int(os.environ.get("BCH_STORAGE_FOOTPRINT_TIMEOUT_SECONDS", "8")),
)
_STORAGE_FOOTPRINT_LOCK = threading.Lock()
_STORAGE_FOOTPRINT_CACHE = {
    "measuredAt": 0.0,
    "usedBytes": None,
    "localBytes": None,
    "blocksBytes": None,
}


def _du_bytes(path: Path, *, one_filesystem: bool = False) -> int:
    command = ["du", "-sk"]
    if one_filesystem:
        command.append("-x")
    command.append(str(path))
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=STORAGE_FOOTPRINT_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise RuntimeError(
            completed.stderr.strip()
            or f"du failed for {path}"
        )
    kib = int(completed.stdout.split()[0])
    return kib * 1024


def runtime_storage_footprint() -> dict:
    now = time.monotonic()
    with _STORAGE_FOOTPRINT_LOCK:
        cached_at = float(_STORAGE_FOOTPRINT_CACHE.get("measuredAt") or 0.0)
        if (
            _STORAGE_FOOTPRINT_CACHE.get("usedBytes") is not None
            and now - cached_at < STORAGE_FOOTPRINT_TTL_SECONDS
        ):
            return {
                **_STORAGE_FOOTPRINT_CACHE,
                "source": "cached-directory-footprint",
                "stale": False,
            }

        previous = dict(_STORAGE_FOOTPRINT_CACHE)
        try:
            # Do not cross into the nested remote blocks mount while measuring
            # local runtime metadata/chainstate. Measure blocks exactly once.
            local_bytes = _du_bytes(DATA_PATH, one_filesystem=True)
            blocks_path = DATA_PATH / "blocks"
            blocks_bytes = (
                _du_bytes(blocks_path)
                if blocks_path.exists()
                else 0
            )
            _STORAGE_FOOTPRINT_CACHE.update(
                {
                    "measuredAt": now,
                    "usedBytes": local_bytes + blocks_bytes,
                    "localBytes": local_bytes,
                    "blocksBytes": blocks_bytes,
                }
            )
            return {
                **_STORAGE_FOOTPRINT_CACHE,
                "source": "directory-footprint",
                "stale": False,
            }
        except Exception as exc:
            if previous.get("usedBytes") is not None:
                return {
                    **previous,
                    "source": "cached-directory-footprint",
                    "stale": True,
                    "error": str(exc),
                }
            return {
                "measuredAt": now,
                "usedBytes": None,
                "localBytes": None,
                "blocksBytes": None,
                "source": "unavailable",
                "stale": True,
                "error": str(exc),
            }


'''
    if "def runtime_storage_footprint()" not in text:
        if data_anchor not in text:
            raise RuntimeError("status app storage cache anchor not found")
        text = text.replace(data_anchor, cache_block, 1)

    old_storage = '''def storage_payload() -> dict:
    try:
        usage = shutil.disk_usage(
            DATA_PATH
        )
        return {
            "path": str(DATA_PATH),
            "totalBytes": usage.total,
            "usedBytes": usage.used,
            "freeBytes": usage.free,
            "healthy": True,
        }
    except Exception as exc:
        return {
            "path": str(DATA_PATH),
            "healthy": False,
            "error": str(exc),
        }
'''
    new_storage = '''def storage_payload() -> dict:
    try:
        usage = shutil.disk_usage(
            DATA_PATH
        )
        footprint = runtime_storage_footprint()
        runtime_used = footprint.get("usedBytes")
        return {
            "path": str(DATA_PATH),
            "totalBytes": usage.total,
            "usedBytes": (
                runtime_used
                if runtime_used is not None
                else usage.used
            ),
            "freeBytes": usage.free,
            "filesystemUsedBytes": usage.used,
            "runtimeFootprint": footprint,
            "usageSemantics": (
                "runtime-footprint"
                if runtime_used is not None
                else "filesystem-fallback"
            ),
            "healthy": True,
        }
    except Exception as exc:
        return {
            "path": str(DATA_PATH),
            "healthy": False,
            "error": str(exc),
        }
'''
    text = replace_once(text, old_storage, new_storage, "status app storage semantics")
    path.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-js", type=Path, required=True)
    parser.add_argument("--telemetry", type=Path, required=True)
    parser.add_argument("--status-app", type=Path, required=True)
    args = parser.parse_args()
    patch_app_js(args.app_js)
    patch_telemetry(args.telemetry)
    patch_status(args.status_app)
    print("SBP-063.3.8 source patch: PASS")


if __name__ == "__main__":
    main()
