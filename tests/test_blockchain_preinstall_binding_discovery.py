from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CANONICAL_HOOKS = {
    "bch": ROOT / "seymour-bch-node" / "hooks" / "pre-install",
    "monero": ROOT / "seymour-monero-node" / "hooks" / "pre-install",
}


class BlockchainPreinstallBindingDiscoveryTests(unittest.TestCase):
    def test_canonical_hooks_exist(self):
        for name, hook in CANONICAL_HOOKS.items():
            with self.subTest(provider=name):
                self.assertTrue(hook.is_file(), hook)

    def test_bch_prefers_app_local_with_legacy_fallback(self):
        self._assert_contract(
            CANONICAL_HOOKS["bch"],
            "seymour-bch-node.env",
        )

    def test_monero_prefers_app_local_with_legacy_fallback(self):
        self._assert_contract(
            CANONICAL_HOOKS["monero"],
            "$app_id.env",
        )

    def test_canonical_hooks_have_valid_shell_syntax(self):
        for name, hook in CANONICAL_HOOKS.items():
            with self.subTest(provider=name):
                result = subprocess.run(
                    ["bash", "-n", str(hook)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    result.stderr,
                )

    def _assert_contract(
        self,
        hook: Path,
        legacy_filename: str,
    ):
        text = hook.read_text(encoding="utf-8")

        local = (
            'APP_LOCAL_BINDING_FILE='
            '"$APP_DATA_DIR/data/runtime-binding.env"'
        )

        legacy = (
            'LEGACY_BINDING_FILE='
            '"$UMBREL_ROOT/app-data/'
            'seymour-blockchain-manager/data/evidence/'
            f'runtime-bindings/{legacy_filename}"'
        )

        choose = (
            'if [[ -f "$APP_LOCAL_BINDING_FILE" ]]; then'
        )

        use_local = (
            'BINDING_FILE="$APP_LOCAL_BINDING_FILE"'
        )

        fallback = (
            'BINDING_FILE="$LEGACY_BINDING_FILE"'
        )

        self.assertEqual(text.count(local), 1)
        self.assertEqual(text.count(legacy), 1)
        self.assertEqual(text.count(choose), 1)
        self.assertEqual(text.count(use_local), 1)
        self.assertEqual(text.count(fallback), 1)

        self.assertLess(
            text.index(choose),
            text.index(use_local),
        )
        self.assertLess(
            text.index(use_local),
            text.index(fallback),
        )


if __name__ == "__main__":
    unittest.main()
