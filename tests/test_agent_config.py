import sys
import tempfile
import unittest
from pathlib import Path

from app.core.runner.maafw import (
    iter_agent_entries,
    normalize_agent_entry,
    resolve_agent_executable,
    should_start_external_agent,
)


class TestAgentConfig(unittest.TestCase):
    def test_iter_agent_entries_yields_all_list_items(self):
        config = [
            {"child_exec": "agent/go-service", "child_args": []},
            {"child_exec": "agent/cpp-algo", "child_args": []},
        ]
        entries = list(iter_agent_entries(config))
        self.assertEqual(2, len(entries))
        self.assertEqual("agent/go-service", entries[0]["child_exec"])
        self.assertEqual("agent/cpp-algo", entries[1]["child_exec"])

    def test_normalize_list_uses_first_valid_entry(self):
        config = [
            {"child_exec": "agent/go-service", "child_args": []},
            {"child_exec": "agent/cpp-algo", "child_args": []},
        ]
        entry = normalize_agent_entry(config)
        self.assertEqual("agent/go-service", entry["child_exec"])

    def test_should_start_external_agent_for_list(self):
        config = [
            {"child_exec": "agent/go-service", "child_args": []},
        ]
        self.assertTrue(should_start_external_agent(config))

    def test_should_not_start_embedded_dict(self):
        config = {"embedded": True, "child_args": ["agent/main.py"]}
        self.assertFalse(should_start_external_agent(config))

    def test_should_start_external_dict(self):
        config = {
            "child_exec": "python",
            "child_args": ["{PROJECT_DIR}/agent/main.py"],
        }
        self.assertTrue(should_start_external_agent(config))

    def test_resolve_agent_executable_relative_to_project_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            agent_dir = root / "agent"
            agent_dir.mkdir()
            exe_name = "go-service.exe" if sys.platform == "win32" else "go-service"
            (agent_dir / exe_name).write_bytes(b"")

            resolved = resolve_agent_executable("agent/go-service", root)
            self.assertEqual(str((agent_dir / exe_name).resolve()), resolved)

    def test_resolve_agent_executable_keeps_path_command(self):
        self.assertEqual("python", resolve_agent_executable("python", Path.cwd()))


if __name__ == "__main__":
    unittest.main()
