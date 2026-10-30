import yaml
from pathlib import Path
from config.settings import settings

class PermissionGate:
    def __init__(self):
        self.config_path = settings.CONFIG_DIR / "permissions.yaml"
        self.policies = self._load_policies()

    def _load_policies(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {"default_policy": "require_confirmation", "tools": {}}

    def check_permission(self, tool_name: str) -> str:
        # Dynamically reload policies
        self.policies = self._load_policies()
        tools_policy = self.policies.get("tools", {})
        return tools_policy.get(tool_name, self.policies.get("default_policy", "require_confirmation"))

permission_gate = PermissionGate()