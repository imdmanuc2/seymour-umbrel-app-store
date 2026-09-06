from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from shared.blockchain_install.runtime_binding import (
    RuntimeBinding,
    RuntimeBindingMode,
)
from shared.blockchain_install.storage_preparer import (
    prepare_runtime_storage,
)


class SharedStoragePreparerTests(unittest.TestCase):
    def test_single_path_creates_data_directory(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "storage" / "bitcoin-mainnet"

            binding = RuntimeBinding(
                provider_id="bitcoin-mainnet",
                app_id="seymour-bitcoin-node",
                mode=RuntimeBindingMode.SINGLE_PATH,
                data_path=data,
            )

            result = prepare_runtime_storage(binding)

            self.assertTrue(data.is_dir())
            self.assertEqual(
                result["preparedPaths"],
                [str(data)],
            )
            self.assertEqual(
                result["mode"],
                "single-path",
            )

    def test_single_path_is_idempotent(self):
        with TemporaryDirectory() as temp:
            data = Path(temp) / "bitcoin-mainnet"

            binding = RuntimeBinding(
                provider_id="bitcoin-mainnet",
                app_id="seymour-bitcoin-node",
                mode=RuntimeBindingMode.SINGLE_PATH,
                data_path=data,
            )

            first = prepare_runtime_storage(binding)
            second = prepare_runtime_storage(binding)

            self.assertTrue(data.is_dir())
            self.assertEqual(first, second)

    def test_hybrid_creates_only_blocks_directory(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)

            local_data = (
                root
                / "umbrel-local"
                / "seymour-bch-node"
                / "data"
                / "node"
            )

            blocks = (
                root
                / "remote"
                / "bitcoin-cash-mainnet"
                / "blocks"
            )

            binding = RuntimeBinding(
                provider_id="bitcoin-cash-mainnet",
                app_id="seymour-bch-node",
                mode=RuntimeBindingMode.HYBRID_BLOCKS,
                local_data_path=local_data,
                blocks_path=blocks,
            )

            result = prepare_runtime_storage(binding)

            self.assertTrue(blocks.is_dir())
            self.assertFalse(local_data.exists())
            self.assertEqual(
                result["preparedPaths"],
                [str(blocks)],
            )
            self.assertEqual(
                result["mode"],
                "hybrid-blocks",
            )

    def test_invalid_binding_fails_before_creation(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            candidate = root / "should-not-exist"

            binding = RuntimeBinding(
                provider_id="bitcoin-mainnet",
                app_id="seymour-bitcoin-node",
                mode=RuntimeBindingMode.SINGLE_PATH,
                data_path=None,
            )

            with self.assertRaises(ValueError):
                prepare_runtime_storage(binding)

            self.assertFalse(candidate.exists())


if __name__ == "__main__":
    unittest.main()
