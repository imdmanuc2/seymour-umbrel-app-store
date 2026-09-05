from __future__ import annotations

from pathlib import Path
import unittest

from shared.blockchain_install import (
    InstallRequest,
    SharedInstallOrchestrator,
    TargetInstallExecution,
    TargetInstallPreflight,
    TargetInstallVerification,
)


CATALOG = Path(
    "shared/provider_catalog/providers.v1.json"
)


def request() -> InstallRequest:
    return InstallRequest.from_dict({
        "providerId": "bitcoin-mainnet",
        "appId": "seymour-bitcoin-node",
        "nodeName": "Test Bitcoin",
        "rpcUser": "seymour_rpc",
        "rpcPassword": "x" * 32,
        "rpcPort": 8332,
        "p2pPort": 8333,
        "storageTargetId": "storage-1",
        "confirmation":
            "INSTALL-seymour-bitcoin-node",
    })


class FakeAdapter:
    adapter_type = "fake"

    def __init__(
        self,
        *,
        preflight_ok=True,
        execute_ok=True,
        verify_ok=True,
    ):
        self.preflight_ok = preflight_ok
        self.execute_ok = execute_ok
        self.verify_ok = verify_ok
        self.calls = []

    def preflight(self, value, provider):
        self.calls.append("preflight")
        return TargetInstallPreflight(
            compatible=self.preflight_ok,
            checks={
                "adapter": self.adapter_type,
                "providerId":
                    provider["providerId"],
            },
            errors=(
                ()
                if self.preflight_ok
                else ("target unavailable",)
            ),
        )

    def execute(self, value, provider):
        self.calls.append("execute")
        return TargetInstallExecution(
            success=self.execute_ok,
            result={"executed": self.execute_ok},
            evidence={"adapter": self.adapter_type},
            error=(
                None
                if self.execute_ok
                else "target execution failed"
            ),
        )

    def verify(
        self,
        value,
        provider,
        execution,
    ):
        self.calls.append("verify")
        return TargetInstallVerification(
            verified=self.verify_ok,
            evidence={
                "adapter": self.adapter_type,
            },
            error=(
                None
                if self.verify_ok
                else "target verification failed"
            ),
        )


class SharedInstallOrchestratorTests(
    unittest.TestCase
):
    def test_successful_install_flow(self):
        adapter = FakeAdapter()

        orchestrator = SharedInstallOrchestrator(
            catalog_path=CATALOG,
            target_adapter=adapter,
        )

        result = orchestrator.execute(
            request()
        )

        self.assertTrue(result.succeeded)
        self.assertEqual(
            adapter.calls,
            [
                "preflight",
                "execute",
                "verify",
            ],
        )

    def test_failed_preflight_stops_execution(self):
        adapter = FakeAdapter(
            preflight_ok=False,
        )

        result = SharedInstallOrchestrator(
            catalog_path=CATALOG,
            target_adapter=adapter,
        ).execute(request())

        self.assertFalse(result.succeeded)
        self.assertEqual(
            adapter.calls,
            ["preflight"],
        )

    def test_failed_execution_skips_verification(self):
        adapter = FakeAdapter(
            execute_ok=False,
        )

        result = SharedInstallOrchestrator(
            catalog_path=CATALOG,
            target_adapter=adapter,
        ).execute(request())

        self.assertFalse(result.succeeded)
        self.assertEqual(
            adapter.calls,
            [
                "preflight",
                "execute",
            ],
        )

    def test_failed_verification_fails_result(self):
        adapter = FakeAdapter(
            verify_ok=False,
        )

        result = SharedInstallOrchestrator(
            catalog_path=CATALOG,
            target_adapter=adapter,
        ).execute(request())

        self.assertFalse(result.succeeded)
        self.assertEqual(
            adapter.calls,
            [
                "preflight",
                "execute",
                "verify",
            ],
        )

    def test_adapter_contract_has_no_management_product_dependency(self):
        import ast

        from shared.blockchain_install import target

        source = Path(
            target.__file__
        ).read_text()

        tree = ast.parse(source)

        imported_modules = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(
                    alias.name
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(
                    node.module or ""
                )

        imported = " ".join(
            imported_modules
        ).lower()

        self.assertNotIn(
            "nexus",
            imported,
        )
        self.assertNotIn(
            "blockchain_manager",
            imported,
        )
        self.assertNotIn(
            "umbrel",
            imported,
        )
        self.assertNotIn(
            "subprocess",
            imported,
        )


if __name__ == "__main__":
    unittest.main()
