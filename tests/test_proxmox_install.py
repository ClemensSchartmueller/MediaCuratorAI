import unittest
import re
from pathlib import Path

EXPECTED_SETUP_INVOCATION_COUNT_BOTH_PATHS = 2


class TestProxmoxInstaller(unittest.TestCase):
    def test_lxc_provision_executes_setup_script_from_stdin(self):
        script_path = (
            Path(__file__).resolve().parents[1] / "proxmox" / "lxc_install.sh"
        )
        script = script_path.read_text()

        matches = re.findall(
            r'pct\s+exec\s+["\']?\$CTID["\']?\s+--\s+bash\s+-s', script
        )

        self.assertEqual(
            len(matches),
            EXPECTED_SETUP_INVOCATION_COUNT_BOTH_PATHS,
        )


if __name__ == "__main__":
    unittest.main()
