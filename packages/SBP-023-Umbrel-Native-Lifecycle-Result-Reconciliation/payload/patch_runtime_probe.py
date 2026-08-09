from pathlib import Path
import re

path = Path("seymour-blockchain-manager/data/web/bch_runtime_probe.py")
text = path.read_text()

pattern = re.compile(
    r"def http_json\(url: str\)->dict\[str,Any\]:\n.*?\n return out\n",
    re.S,
)

replacement = '''def http_json(
    url: str,
    timeout: int = 8,
) -> dict[str, Any]:
    out = {
        "url": url,
        "reachable": False,
        "httpStatus": None,
        "payload": None,
        "error": None,
    }
    try:
        with request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode()
            out["httpStatus"] = int(response.status)
            out["reachable"] = True
            try:
                out["payload"] = json.loads(raw)
            except json.JSONDecodeError:
                out["payload"] = {"raw": raw}
    except error.HTTPError as exc:
        out["httpStatus"] = int(exc.code)
        out["error"] = f"HTTP {exc.code}: {exc.reason}"
        try:
            raw = exc.read().decode()
            out["payload"] = json.loads(raw) if raw else None
        except Exception:
            pass
    except Exception as exc:
        out["error"] = str(exc)
    return out
'''

if not pattern.search(text):
    raise SystemExit("Could not locate bch_runtime_probe.http_json helper.")

text = pattern.sub(replacement, text, count=1)
text = text.replace(
    "legacy_health=http_json(BCH_HEALTH_URL)",
    "legacy_health=http_json(BCH_HEALTH_URL, timeout=8)",
)
text = text.replace(
    "legacy_status=http_json(BCH_STATUS_URL)",
    "legacy_status=http_json(BCH_STATUS_URL, timeout=25)",
)

path.write_text(text)
print("BCH sidecar observation timeout contract patched.")
