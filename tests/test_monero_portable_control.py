from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

CANONICAL = (
    ROOT
    / "scripts"
    / "seymour-install-monero"
)

PORTABLE = (
    ROOT
    / "seymour-blockchain-manager"
    / "data"
    / "control"
    / "seymour-install-monero"
)


class MoneroPortableControlTests(unittest.TestCase):
    def test_portable_script_exists(self):
        self.assertTrue(
            PORTABLE.is_file()
        )

    def test_portable_matches_canonical(self):
        self.assertEqual(
            CANONICAL.read_bytes(),
            PORTABLE.read_bytes(),
        )

    def test_app_id_is_canonical(self):
        text = CANONICAL.read_text()

        self.assertIn(
            'APP_ID="seymour-monero-node"',
            text,
        )

        self.assertNotIn(
            "XMR_APP_ID",
            text,
        )

    def test_confirmation_is_guarded(self):
        text = CANONICAL.read_text()

        self.assertIn(
            'EXPECTED="INSTALL-${APP_ID}"',
            text,
        )

        self.assertIn(
            '--confirm "$EXPECTED"',
            text,
        )


if __name__ == "__main__":
    unittest.main()
