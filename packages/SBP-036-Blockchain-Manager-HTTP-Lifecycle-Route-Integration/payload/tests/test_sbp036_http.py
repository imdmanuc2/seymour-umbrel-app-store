#!/usr/bin/env python3
from pathlib import Path
import importlib.util

repo = Path(__file__).resolve().parents[1]
module_path = repo / "seymour-blockchain-manager" / "data" / "web" / "lifecycle_routes.py"
spec = importlib.util.spec_from_file_location("sbp036_lifecycle_routes", module_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
LifecycleHttpAdapter = module.LifecycleHttpAdapter


class FakeFacade:
    def __init__(self):
        self.calls = []

    def operation(self, payload):
        self.calls.append(("operation", dict(payload)))
        return {
            "contract": "seymour.lifecycle-api-response",
            "version": "1.0",
            "appId": payload.get("appId"),
            "action": payload.get("action"),
            "allowed": True,
            "executed": bool(payload.get("execute")),
            "success": True if payload.get("execute") else None,
            "confirmationRequired": True,
            "confirmationToken": "RESTART-seymour-bch-node",
        }

    def history(self, query):
        self.calls.append(("history", dict(query)))
        return {
            "contract": "seymour.lifecycle-api-history",
            "version": "1.0",
            "count": 0,
            "items": [],
        }

    @staticmethod
    def http_status(payload):
        return 200


fake = FakeFacade()
adapter = LifecycleHttpAdapter(fake)

planned, status = adapter.operation({"appId": "seymour-bch-node", "action": "restart"})
assert status == 200
assert planned["contract"] == "seymour.lifecycle-api-response"
assert planned["executed"] is False

legacy, status = adapter.legacy_operation(
    "restart",
    {"appId": "seymour-bch-node", "confirmation": "RESTART-seymour-bch-node"},
)
assert status == 200
assert fake.calls[-1][1]["action"] == "restart"
assert fake.calls[-1][1]["execute"] is True

history, status = adapter.history({"appId": "seymour-bch-node", "limit": "10"})
assert status == 200
assert history["contract"] == "seymour.lifecycle-api-history"

print("SBP-036 lifecycle HTTP adapter verification: PASS")
