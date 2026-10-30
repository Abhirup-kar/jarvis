import unittest
import tempfile
from pathlib import Path
import yaml
from core.permissions import PermissionGate

class TestPermissionGate(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "permissions.yaml"
        
        sample_config = {
            "default_policy": "require_confirmation",
            "tools": {
                "get_system_status": "auto_approve",
                "read_document": "auto_approve",
                "send_email": "require_confirmation",
                "dangerous_action": "deny"
            }
        }
        with open(self.config_path, "w") as f:
            yaml.dump(sample_config, f)

        self.gate = PermissionGate()
        self.gate.config_path = self.config_path
        self.gate.policies = self.gate._load_policies()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_auto_approve_tool(self):
        policy = self.gate.check_permission("get_system_status")
        self.assertEqual(policy, "auto_approve")

    def test_require_confirmation_tool(self):
        policy = self.gate.check_permission("send_email")
        self.assertEqual(policy, "require_confirmation")

    def test_deny_tool(self):
        policy = self.gate.check_permission("dangerous_action")
        self.assertEqual(policy, "deny")

    def test_unknown_tool_fallback_default(self):
        policy = self.gate.check_permission("unknown_random_tool")
        self.assertEqual(policy, "require_confirmation")

if __name__ == "__main__":
    unittest.main()

