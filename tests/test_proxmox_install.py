import unittest
from pathlib import Path


class TestProxmoxInstaller(unittest.TestCase):
    def test_lxc_provision_executes_setup_script_from_stdin(self):
        script_path = (
            Path(__file__).resolve().parents[1] / "proxmox" / "lxc_install.sh"
        )
        script = script_path.read_text()

        self.assertEqual(script.count('pct exec "$CTID" -- bash -s'), 2)


if __name__ == "__main__":
    unittest.main()
