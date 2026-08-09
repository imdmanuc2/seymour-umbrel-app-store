from pathlib import Path

path = Path("shared/umbrel_control/bridge.py")
text = path.read_text()

helper = '''def _native_result_error(payload: object) -> str | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        for key in ("error", "message", "detail", "reason"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        nested = payload.get("result")
        if nested is not None:
            value = _native_result_error(nested)
            if value:
                return value
    if isinstance(payload, str):
        value = payload.strip()
        if value:
            return value
    return None


def _state_matches_action(action: str, state: object) -> bool:
    value = str(state or "").strip().lower()
    if action in {"start", "restart"}:
        return value in {"ready", "running"}
    if action == "stop":
        return value in {"stopped", "not-running", "inactive"}
    return False


'''

if "_state_matches_action(" not in text:
    pos = text.find("class ")
    if pos == -1:
        raise SystemExit("Could not locate lifecycle bridge class marker.")
    text = text[:pos] + helper + text[pos:]

text = text.replace(
    '"Unknown error"',
    '"Umbrel lifecycle operation did not return an error detail."',
)
text = text.replace(
    "'Unknown error'",
    "'Umbrel lifecycle operation did not return an error detail.'",
)

path.write_text(text)
print("Umbrel lifecycle bridge result helpers added.")
