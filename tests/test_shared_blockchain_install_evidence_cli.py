from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


REPOSITORY = Path(__file__).resolve().parents[1]

SCRIPT = (
    REPOSITORY
    / "scripts"
    / "seymour-blockchain-install-evidence"
)


def load_module():
    loader = importlib.machinery.SourceFileLoader(
        "seymour_blockchain_install_evidence",
        str(SCRIPT),
    )

    spec = importlib.util.spec_from_loader(
        loader.name,
        loader,
    )

    if spec is None:
        raise RuntimeError(
            "Unable to load evidence query CLI"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    loader.exec_module(module)

    return module


def installed_evidence(
    *,
    provider_id="bitcoin-mainnet",
):
    return {
        "contract": "seymour.blockchain-installation",
        "version": 1,
        "operationId": "operation-1",
        "operation": "install",
        "providerId": provider_id,
        "storageTargetId": "storage-main",
        "status": "installed",
        "verified": True,
        "stateVerified": True,
        "runtimeDataMountMatches": True,
        "runtimeBlocksMountMatches": True,
        "bindingMode": "single-path",
        "recordedAt": "2026-09-10T00:00:00+00:00",
    }


class ProviderInstallEvidenceCliTests(
    unittest.TestCase
):
    def test_script_exists_and_is_executable(self):
        self.assertTrue(SCRIPT.is_file())

        self.assertTrue(
            SCRIPT.stat().st_mode & 0o111
        )

    def test_parser_has_only_provider_id(self):
        module = load_module()

        actions = {
            action.dest
            for action in module.parser()._actions
            if action.dest != "help"
        }

        self.assertEqual(
            actions,
            {"provider_id"},
        )

    def test_public_parser_rejects_path(self):
        module = load_module()

        with self.assertRaises(SystemExit):
            module.parser().parse_args([
                "--provider-id",
                "bitcoin-mainnet",
                "--path",
                "/tmp/forbidden",
            ])

    def test_reads_exact_provider_current(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            current = (
                root
                / "seymour-evidence"
                / "blockchain-install"
                / "installations"
                / "current"
            )

            current.mkdir(
                parents=True
            )

            payload = installed_evidence()

            (
                current
                / "bitcoin-mainnet.json"
            ).write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            output = io.StringIO()

            with (
                patch.object(
                    module,
                    "UMBREL_DATA_DIRECTORY",
                    root,
                ),
                redirect_stdout(output),
            ):
                code = module.main([
                    "--provider-id",
                    "bitcoin-mainnet",
                ])

            self.assertEqual(code, 0)

            returned = json.loads(
                output.getvalue()
            )

            self.assertEqual(
                returned,
                payload,
            )

    def test_provider_identity_mismatch_fails_closed(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            current = (
                root
                / "seymour-evidence"
                / "blockchain-install"
                / "installations"
                / "current"
            )

            current.mkdir(
                parents=True
            )

            (
                current
                / "bitcoin-mainnet.json"
            ).write_text(
                json.dumps(
                    installed_evidence(
                        provider_id="wrong-provider"
                    )
                ),
                encoding="utf-8",
            )

            output = io.StringIO()

            with (
                patch.object(
                    module,
                    "UMBREL_DATA_DIRECTORY",
                    root,
                ),
                redirect_stdout(output),
            ):
                code = module.main([
                    "--provider-id",
                    "bitcoin-mainnet",
                ])

            self.assertEqual(code, 1)

    def test_missing_current_fails_closed(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as temp:
            output = io.StringIO()

            with (
                patch.object(
                    module,
                    "UMBREL_DATA_DIRECTORY",
                    Path(temp),
                ),
                redirect_stdout(output),
            ):
                code = module.main([
                    "--provider-id",
                    "bitcoin-mainnet",
                ])

            self.assertEqual(code, 1)

    def test_invalid_provider_fails_closed(self):
        module = load_module()

        output = io.StringIO()

        with redirect_stdout(output):
            code = module.main([
                "--provider-id",
                "../escape",
            ])

        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
