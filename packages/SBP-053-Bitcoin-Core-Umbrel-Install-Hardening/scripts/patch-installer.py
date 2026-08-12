#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
path = repo / "scripts" / "seymour-install-btc"
text = path.read_text()

old = """    cp = subprocess.run(cmd, capture_output=True, text=True, timeout=a.timeout_seconds, check=False)
    try:
        result = json.loads(cp.stdout) if cp.stdout.strip() else None
    except json.JSONDecodeError:
        result = {"raw": cp.stdout}
    payload = {
        "contract":"seymour.bitcoin-install-result",
        "version":"1.0",
        "appId":APP_ID,
        "providerId":PROVIDER_ID,
        "executed":True,
        "success":cp.returncode == 0,
        "result":result,
        "stderr":cp.stderr.strip() or None,
    }
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if cp.returncode == 0 else 1)
"""

new = """    cp = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=a.timeout_seconds,
        check=False,
    )

    try:
        result = json.loads(cp.stdout) if cp.stdout.strip() else None
    except json.JSONDecodeError:
        result = {"raw": cp.stdout}

    native_success = (
        cp.returncode == 0
        and isinstance(result, dict)
        and result.get("success") is True
        and result.get("result") is not False
    )

    final_state = None
    state_error = None

    if native_success:
        state_cmd = [
            str(CONTROL),
            "state",
            APP_ID,
            "--data-directory",
            str(a.data_directory),
            "--endpoint",
            a.endpoint,
        ]
        state_cp = subprocess.run(
            state_cmd,
            capture_output=True,
            text=True,
            timeout=min(a.timeout_seconds, 120),
            check=False,
        )

        try:
            state_payload = json.loads(state_cp.stdout) if state_cp.stdout.strip() else None
        except json.JSONDecodeError:
            state_payload = {"raw": state_cp.stdout}

        if isinstance(state_payload, dict):
            raw_state = state_payload.get("result")
            if isinstance(raw_state, dict):
                final_state = raw_state.get("state")
            state_error = state_payload.get("error")

        if state_cp.returncode != 0 and not state_error:
            state_error = state_cp.stderr.strip() or "state verification failed"

    installed = final_state not in {None, "", "not-installed", "not_installed", "missing"}
    success = native_success and installed

    payload = {
        "contract": "seymour.bitcoin-install-result",
        "version": "1.1",
        "appId": APP_ID,
        "providerId": PROVIDER_ID,
        "executed": True,
        "success": success,
        "nativeSuccess": native_success,
        "finalState": final_state,
        "result": result,
        "stateError": state_error,
        "stderr": cp.stderr.strip() or None,
    }

    if native_success and not installed:
        payload["error"] = "native-install-did-not-register"

    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if success else 1)
"""

if old not in text:
    raise SystemExit("SBP-053 patch anchor not found")
path.write_text(text.replace(old, new, 1))
print("SBP-053 installer hardening patch: PASS")
