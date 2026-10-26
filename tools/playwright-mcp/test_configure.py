import importlib.util
import json
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location("configure_mcp", Path(__file__).with_name("configure.py"))
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class ConfigureTests(unittest.TestCase):
    def test_claude_preserves_other_settings_and_project_options(self):
        original = {"other": {"keep": True}, "mcpServers": {"other": {"url": "http://localhost"}}, "projects": {"example": {"mcpServers": {"playwright": {"command": "npx", "args": ["-y", "@playwright/mcp@latest", "--extension"]}}}}}
        text, count = setup.update_claude(json.dumps(original))
        changed = json.loads(text)
        self.assertEqual(count, 1)
        self.assertEqual(changed["other"], original["other"])
        self.assertEqual(changed["mcpServers"]["other"], original["mcpServers"]["other"])
        self.assertEqual(changed["projects"]["example"]["mcpServers"]["playwright"]["args"], [str(setup.LAUNCHER), "--extension"])
        self.assertEqual(json.loads(setup.update_claude(text)[0]), changed)

    def test_codex_preserves_profile_and_adjacent_sections(self):
        original = '[unrelated]\nvalue = 1\n\n[mcp_servers.playwright]\ncommand = "npx"\nargs = ["-y", "@playwright/mcp@latest", "--user-data-dir", "/existing/profile"]\nenabled = true\n\n[mcp_servers.other]\ncommand = "keep"\n'
        changed = setup.update_codex(original)
        self.assertIn('"/existing/profile"', changed)
        self.assertIn('enabled = true', changed)
        self.assertEqual(changed.split('[mcp_servers.other]')[1], original.split('[mcp_servers.other]')[1])
        self.assertEqual(changed.split('[mcp_servers.playwright]')[0], original.split('[mcp_servers.playwright]')[0])
        self.assertEqual(setup.update_codex(changed), changed)

    def test_unrecognized_server_is_rejected(self):
        with self.assertRaises(ValueError):
            setup.update_codex('[mcp_servers.playwright]\ncommand = "custom"\nargs = []\n')

    def test_codex_can_add_missing_server(self):
        result = setup.update_codex('model = "example"\n')
        self.assertTrue(result.startswith('model = "example"\n'))
        self.assertIn('[mcp_servers.playwright]', result)
        self.assertEqual(setup.update_codex(result), result)


if __name__ == "__main__":
    unittest.main()
