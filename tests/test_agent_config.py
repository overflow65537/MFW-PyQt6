import unittest

from app.core.runner.maafw import (
    iter_agent_entries,
    normalize_agent_entry,
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


if __name__ == "__main__":
    unittest.main()
