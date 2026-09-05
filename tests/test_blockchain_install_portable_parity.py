from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

CANONICAL = (
    ROOT
    / "shared"
    / "blockchain_install"
)

PACKAGED = (
    ROOT
    / "seymour-blockchain-manager"
    / "data"
    / "shared"
    / "blockchain_install"
)

PORTABLE_PARITY_FILES = (
    "__init__.py",
    "host.py",
    "models.py",
    "preflight.py",
    "storage.py",
    "binding.py",
    "materialize.py",
    "request.py",
    "execution.py",
    "validation.py",
    "runtime_binding.py",
    "runtime_binding_materializer.py",
    "runtime_binding_reconciler.py",
)


class PortableBlockchainInstallParityTests(
    unittest.TestCase
):
    def test_expected_files_exist(self):
        for name in PORTABLE_PARITY_FILES:
            with self.subTest(name=name):
                self.assertTrue(
                    (CANONICAL / name).is_file(),
                    f"Canonical shared file missing: {name}",
                )
                self.assertTrue(
                    (PACKAGED / name).is_file(),
                    f"Portable shared file missing: {name}",
                )

    def test_portable_projection_matches_canonical(self):
        for name in PORTABLE_PARITY_FILES:
            with self.subTest(name=name):
                canonical = (
                    CANONICAL / name
                ).read_bytes()

                packaged = (
                    PACKAGED / name
                ).read_bytes()

                self.assertEqual(
                    packaged,
                    canonical,
                    (
                        "Portable Blockchain Manager shared "
                        f"projection drifted: {name}"
                    ),
                )


if __name__ == "__main__":
    unittest.main()
