import json
import tempfile
import unittest
from pathlib import Path

from app.core.service.interface_manager import InterfaceManager
from app.core.runner.maafw import MaaFW


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
    def test_load_embedded_agent_custom_imports_source_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_agent_source(
                root,
                '\n'.join(
                    [
                        'from agent_file import *',
                        '',
                    ]
                ),
            )
            (root / "agent" / "agent_file.py").write_text(
                '\n'.join(
                    [
                        'from maa.custom_action import CustomAction',
                        'from maa.custom_recognition import CustomRecognition',
                        'from maa.resource import resource',
                        '',
                        '@resource.custom_action("alpha")',
                        'class AlphaAction(CustomAction):',
                        '    def run(self, context, argv):',
                        '        return True',
                        '',
                        '@resource.custom_recognition("beta")',
                        'class BetaRecognition(CustomRecognition):',
                        '    def analyze(self, context, argv):',
                        '        return None',
                        '',
                    ]
                ),
                encoding="utf-8",
            )

            maafw = MaaFW()
            self.assertTrue(
                maafw.load_embedded_agent_custom(
                    agent_root=root / "agent",
                    agent_entry=root / "agent" / "main.py",
                )
            )
            self.assertIn("alpha", maafw.resource.custom_action_list)
            self.assertIn("beta", maafw.resource.custom_recognition_list)

    def test_load_embedded_agent_custom_scans_non_agent_source_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "plugin_src"
            action_dir = source_root / "nested"
            action_dir.mkdir(parents=True, exist_ok=True)
            (source_root / "boot.py").write_text("", encoding="utf-8")
            (action_dir / "actions.py").write_text(
                '\n'.join(
                    [
                        'from maa.custom_action import CustomAction',
                        'from maa.resource import resource',
                        '',
                        '@resource.custom_action("gamma")',
                        'class GammaAction(CustomAction):',
                        '    def run(self, context, argv):',
                        '        return True',
                        '',
                    ]
                ),
                encoding="utf-8",
            )

            maafw = MaaFW()
            self.assertTrue(
                maafw.load_embedded_agent_custom(
                    agent_root=source_root,
                    agent_entry=source_root / "boot.py",
                )
            )
            self.assertIn("gamma", maafw.resource.custom_action_list)

    def test_load_embedded_aspect_ratio_sink_uses_tasker_decorator(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_agent_source(
                root,
                '\n'.join(
                    [
                        'from maa.custom_action import CustomAction',
                        'from maa.resource import resource',
                        '',
                        '@resource.custom_action("alpha")',
                        'class AlphaAction(CustomAction):',
                        '    def run(self, context, argv):',
                        '        return True',
                        '',
                    ]
                ),
            )
            sink_dir = root / "agent" / "custom" / "sink"
            sink_dir.mkdir(parents=True, exist_ok=True)
            (sink_dir / "aspect_ratio.py").write_text(
                '\n'.join(
                    [
                        'from maa.tasker import TaskerEventSink',
                        '',
                        'class AspectRatioChecker(TaskerEventSink):',
                        '    pass',
                        '',
                    ]
                ),
                encoding="utf-8",
            )

            maafw = MaaFW()
            self.assertTrue(
                maafw.load_embedded_agent_custom(
                    agent_root=root / "agent",
                    agent_entry=root / "agent" / "main.py",
                )
            )
            self.assertTrue(maafw.load_embedded_aspect_ratio_sink())
            self.assertEqual(1, len(maafw._embedded_tasker_sinks))

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
            self.assertEqual("agent", translated_interface.get("custom"))
            self.assertEqual(
                "agent/main.py", translated_interface.get("__embedded_agent_entry")
            )
            self.assertTrue(translated_interface.get("__embedded_generated_custom"))
            self.assertIn("agent", json.loads(interface_path.read_text(encoding="utf-8")))
            self.assertNotIn("custom", json.loads(interface_path.read_text(encoding="utf-8")))

    def test_resolve_agent_entry_falls_back_to_default_main_py(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            interface_path = root / "interface.json"
            bad_interface = {
                **INTERFACE_TEMPLATE,
                "agent": {
                    "embedded": True,
                    "child_args": ["../agent/main.py"],
                },
            }
            interface_path.write_text(
                json.dumps(bad_interface, ensure_ascii=False, indent=2),
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

            self.assertTrue(manager.apply_agent_customization())
            translated = manager.get_interface()
            self.assertEqual("agent", translated.get("custom"))
            self.assertEqual("agent/main.py", translated.get("__embedded_agent_entry"))
            self.assertNotIn("__embedded_agent_error", translated)


if __name__ == "__main__":
    unittest.main()
