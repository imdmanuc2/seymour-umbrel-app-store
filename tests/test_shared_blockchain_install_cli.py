from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts"
    / "seymour-blockchain-install"
)


def load_module():
    name = (
        "seymour_blockchain_install_cli"
    )

    loader = SourceFileLoader(
        name,
        str(SCRIPT),
    )

    spec = importlib.util.spec_from_loader(
        name,
        loader,
    )

    if spec is None:
        raise RuntimeError(
            "Unable to load blockchain install CLI."
        )

    module = importlib.util.module_from_spec(
        spec
    )

    loader.exec_module(
        module
    )

    return module


class BlockchainInstallCliTests(TestCase):
    def test_script_exists_and_is_executable(
        self,
    ):
        self.assertTrue(
            SCRIPT.is_file()
        )
        self.assertTrue(
            SCRIPT.stat().st_mode & 0o111
        )

    def test_parser_has_only_fixed_install_inputs(
        self,
    ):
        module = load_module()
        parser = module.parser()

        destinations = {
            action.dest
            for action in parser._actions
        }

        self.assertEqual(
            destinations,
            {
                "help",
                "provider_id",
                "storage_target_id",
                "execute",
            },
        )

        for forbidden in {
            "command",
            "shell",
            "argv",
            "app_id",
            "rpc_user",
            "rpc_password",
            "rpc_port",
            "p2p_port",
            "confirmation",
        }:
            self.assertNotIn(
                forbidden,
                destinations,
            )

    def test_plan_does_not_materialize_or_execute(
        self,
    ):
        module = load_module()

        output = io.StringIO()

        with (
            patch.object(
                module,
                "materialize_install_request",
            ) as materialize,
            patch.object(
                module,
                "build_umbrel_target_install_adapter",
            ) as build_adapter,
            redirect_stdout(output),
        ):
            code = module.main(
                [
                    "--provider-id",
                    "bitcoin-mainnet",
                    "--storage-target-id",
                    "local-test",
                ]
            )

        self.assertEqual(
            code,
            0,
        )

        materialize.assert_not_called()
        build_adapter.assert_not_called()

        payload = json.loads(
            output.getvalue()
        )

        self.assertEqual(
            payload["mode"],
            "plan",
        )
        self.assertFalse(
            payload["executable"]
        )

    def test_execute_materializes_target_side(
        self,
    ):
        module = load_module()

        request = Mock()
        result = Mock()
        result.succeeded = True
        result.to_dict.return_value = {
            "operationId": "test-operation",
            "status": "succeeded",
            "result": {},
            "verification": {},
            "error": None,
        }

        adapter = Mock()
        orchestrator = Mock()
        orchestrator.execute.return_value = (
            result
        )

        output = io.StringIO()

        with (
            patch.object(
                module,
                "materialize_install_request",
                return_value=request,
            ) as materialize,
            patch.object(
                module,
                "build_umbrel_target_install_adapter",
                return_value=adapter,
            ) as build_adapter,
            patch.object(
                module,
                "SharedInstallOrchestrator",
                return_value=orchestrator,
            ) as orchestrator_class,
            redirect_stdout(output),
        ):
            code = module.main(
                [
                    "--provider-id",
                    "bitcoin-mainnet",
                    "--storage-target-id",
                    "local-test",
                    "--execute",
                ]
            )

        self.assertEqual(
            code,
            0,
        )

        materialize.assert_called_once_with(
            provider_id="bitcoin-mainnet",
            storage_target_id="local-test",
            catalog_path=module.CATALOG_PATH,
        )

        build_adapter.assert_called_once_with(
            repository=module.REPOSITORY,
            umbrel_data_directory=(
                module.UMBREL_DATA_DIRECTORY
            ),
            remote_targets_path=(
                module.neutral_storage_targets_path(
                    module.UMBREL_DATA_DIRECTORY
                )
            ),
        )

        orchestrator_class.assert_called_once_with(
            catalog_path=module.CATALOG_PATH,
            target_adapter=adapter,
        )

        orchestrator.execute.assert_called_once_with(
            request
        )

        payload = json.loads(
            output.getvalue()
        )

        self.assertEqual(
            payload["status"],
            "succeeded",
        )

    def test_failed_result_returns_nonzero(
        self,
    ):
        module = load_module()

        result = Mock()
        result.succeeded = False
        result.to_dict.return_value = {
            "operationId": "test-operation",
            "status": "failed",
            "result": None,
            "verification": None,
            "error": "preflight failed",
        }

        orchestrator = Mock()
        orchestrator.execute.return_value = (
            result
        )

        with (
            patch.object(
                module,
                "materialize_install_request",
                return_value=Mock(),
            ),
            patch.object(
                module,
                "build_umbrel_target_install_adapter",
                return_value=Mock(),
            ),
            patch.object(
                module,
                "SharedInstallOrchestrator",
                return_value=orchestrator,
            ),
            redirect_stdout(
                io.StringIO()
            ),
        ):
            code = module.main(
                [
                    "--provider-id",
                    "bitcoin-mainnet",
                    "--storage-target-id",
                    "local-test",
                    "--execute",
                ]
            )

        self.assertEqual(
            code,
            1,
        )

    def test_public_parser_rejects_umbrel_data_directory(
        self,
    ):
        module = load_module()

        with self.assertRaises(SystemExit) as exc:
            module.parser().parse_args(
                [
                    "--provider-id",
                    "bitcoin-mainnet",
                    "--storage-target-id",
                    "local-test",
                    "--umbrel-data-directory",
                    "/tmp/forbidden",
                ]
            )

        self.assertNotEqual(
            exc.exception.code,
            0,
        )

    def test_public_parser_rejects_remote_targets_path(
        self,
    ):
        module = load_module()

        with self.assertRaises(SystemExit) as exc:
            module.parser().parse_args(
                [
                    "--provider-id",
                    "bitcoin-mainnet",
                    "--storage-target-id",
                    "local-test",
                    "--remote-targets-path",
                    "/tmp/forbidden.json",
                ]
            )

        self.assertNotEqual(
            exc.exception.code,
            0,
        )

    def test_target_local_paths_are_derived_internally(
        self,
    ):
        module = load_module()

        self.assertEqual(
            module.UMBREL_DATA_DIRECTORY,
            Path(
                "/home/umbrel/umbrel"
            ),
        )

        self.assertEqual(
            module.neutral_storage_targets_path(
                module.UMBREL_DATA_DIRECTORY
            ),
            (
                module.UMBREL_DATA_DIRECTORY
                / "seymour-evidence"
                / "blockchain-install"
                / "storage-targets.json"
            ),
        )
