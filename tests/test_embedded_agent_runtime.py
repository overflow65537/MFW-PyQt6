import json
import tempfile
import unittest
from pathlib import Path

from app.core.service.interface_manager import InterfaceManager
from app.utils.custom_builder import build_custom_bundle


INTERFACE_TEMPLATE = {
    "name": "DemoProject",
    "agent": {
        "embedded": True,
        "child_args": ["agent/main.py"],
    },
    "task": [],
    "controller": [],
    "resource": [],
}


def _write_agent_source(target_dir: Path, source: str) -> None:
    agent_dir = target_dir / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "main.py").write_text(source, encoding="utf-8")


class EmbeddedAgentRuntimeTests(unittest.TestCase):
    def test_build_custom_bundle_rebuilds_existing_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_agent_source(
                root,
                '\n'.join(
                    [
                        'class AgentServer:',
                        '    @staticmethod',
                        '    def custom_action(name):',
                        '        def decorator(cls):',
                        '            return cls',
                        '        return decorator',
                        '',
                        '@AgentServer.custom_action("alpha")',
                        'class AlphaAction:',
                        '    pass',
                        '',
                    ]
                ),
            )

            entry = root / "agent" / "main.py"
            custom_dir = root / "agent_custom"

            first_bundle = build_custom_bundle(entry, custom_dir)
            self.assertTrue(first_bundle.custom_json.exists())
            self.assertIn("alpha", first_bundle.entries)

            _write_agent_source(
                root,
                '\n'.join(
                    [
                        'class AgentServer:',
                        '    @staticmethod',
                        '    def custom_action(name):',
                        '        def decorator(cls):',
                        '            return cls',
                        '        return decorator',
                        '',
                        '@AgentServer.custom_action("alpha")',
                        'class AlphaAction:',
                        '    pass',
                        '',
                        '@AgentServer.custom_action("beta")',
                        'class BetaAction:',
                        '    pass',
                        '',
                    ]
                ),
            )

            second_bundle = build_custom_bundle(entry, custom_dir)
            self.assertIn("beta", second_bundle.entries)

    def test_interface_manager_mutates_single_in_memory_interface_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            interface_path = root / "interface.json"
            interface_path.write_text(
                json.dumps(INTERFACE_TEMPLATE, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            _write_agent_source(
                root,
                '\n'.join(
                    [
                        'class AgentServer:',
                        '    @staticmethod',
                        '    def custom_action(name):',
                        '        def decorator(cls):',
                        '            return cls',
                        '        return decorator',
                        '',
                        '@AgentServer.custom_action("alpha")',
                        'class AlphaAction:',
                        '    pass',
                        '',
                    ]
                ),
            )

            manager = InterfaceManager()
            manager.reload(interface_path=interface_path, language="zh_cn")

            original_interface = manager.get_original_interface()
            translated_interface = manager.get_interface()
            disk_interface = json.loads(interface_path.read_text(encoding="utf-8"))

            self.assertIn("agent", original_interface)
            self.assertNotIn("custom", original_interface)
            self.assertIn("agent", disk_interface)
            self.assertNotIn("custom", disk_interface)
            self.assertIn("agent", translated_interface)
            self.assertNotIn("custom", translated_interface)

            self.assertTrue(manager.apply_agent_customization())
            self.assertIn("agent", translated_interface)
            self.assertEqual("agent/main.py", translated_interface["agent"]["child_args"][0])
            self.assertEqual("agent_custom/custom.json", translated_interface.get("custom"))
            self.assertTrue(translated_interface.get("__embedded_generated_custom"))

            _write_agent_source(
                root,
                '\n'.join(
                    [
                        'class AgentServer:',
                        '    @staticmethod',
                        '    def custom_action(name):',
                        '        def decorator(cls):',
                        '            return cls',
                        '        return decorator',
                        '',
                        '@AgentServer.custom_action("alpha")',
                        'class AlphaAction:',
                        '    pass',
                        '',
                        '@AgentServer.custom_action("beta")',
                        'class BetaAction:',
                        '    pass',
                        '',
                    ]
                ),
            )

            self.assertTrue(manager.apply_agent_customization())
            custom_json = root / "agent_custom" / "custom.json"
            custom_entries = json.loads(custom_json.read_text(encoding="utf-8"))

            self.assertIn("beta", custom_entries)
            self.assertIn("agent", json.loads(interface_path.read_text(encoding="utf-8")))
            self.assertNotIn("custom", json.loads(interface_path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
