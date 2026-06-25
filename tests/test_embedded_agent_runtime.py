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

    def test_load_embedded_agent_custom_rewrites_agent_server_decorators(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_agent_source(root, "")
            agent_file = root / "agent" / "agent_file.py"
            agent_file.write_text(
                '\n'.join(
                    [
                        'from maa.agent.agent_server import AgentServer',
                        'from maa.custom_action import CustomAction',
                        'from maa.custom_recognition import CustomRecognition',
                        '',
                        '@AgentServer.custom_action("legacy_action")',
                        'class LegacyAction(CustomAction):',
                        '    def run(self, context, argv):',
                        '        return True',
                        '',
                        '@AgentServer.custom_recognition("legacy_reco")',
                        'class LegacyRecognition(CustomRecognition):',
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
            rewritten = agent_file.read_text(encoding="utf-8")
            self.assertIn("from maa.resource import resource", rewritten)
            self.assertIn('@resource.custom_action("legacy_action")', rewritten)
            self.assertIn('@resource.custom_recognition("legacy_reco")', rewritten)
            self.assertNotIn("AgentServer.custom_action", rewritten)
            self.assertIn("legacy_action", maafw.resource.custom_action_list)
            self.assertIn("legacy_reco", maafw.resource.custom_recognition_list)

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

    def test_load_embedded_agent_custom_rewrites_agent_server_sink_decorators(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_agent_source(
                root,
                '\n'.join(
                    [
                        'from custom.sink.event_sinks import *',
                    ]
                ),
            )
            sink_dir = root / "agent" / "custom" / "sink"
            sink_dir.mkdir(parents=True, exist_ok=True)
            sink_file = sink_dir / "event_sinks.py"
            sink_file.write_text(
                '\n'.join(
                    [
                        'from maa.agent.agent_server import AgentServer',
                        'from maa.resource import ResourceEventSink',
                        'from maa.controller import ControllerEventSink',
                        'from maa.tasker import TaskerEventSink',
                        'from maa.context import ContextEventSink',
                        '',
                        '@AgentServer.resource_sink()',
                        'class ResourceSink(ResourceEventSink):',
                        '    pass',
                        '',
                        '@AgentServer.controller_sink()',
                        'class ControllerSink(ControllerEventSink):',
                        '    pass',
                        '',
                        '@AgentServer.tasker_sink()',
                        'class TaskerSink(TaskerEventSink):',
                        '    pass',
                        '',
                        '@AgentServer.context_sink()',
                        'class ContextSink(ContextEventSink):',
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
            self.assertEqual(1, len(maafw._embedded_resource_sinks))
            self.assertEqual(1, len(maafw._embedded_controller_sinks))
            self.assertEqual(1, len(maafw._embedded_tasker_sinks))
            self.assertEqual(1, len(maafw._embedded_context_sinks))
            sink_text = sink_file.read_text(encoding="utf-8")
            self.assertNotIn("AgentServer.resource_sink", sink_text)
            self.assertNotIn("AgentServer.controller_sink", sink_text)
            self.assertNotIn("AgentServer.tasker_sink", sink_text)
            self.assertNotIn("AgentServer.context_sink", sink_text)

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

    def test_two_embedded_agents_with_colliding_action_package(self):
        def _write_bundle(root: Path, register_name: str) -> None:
            agent_dir = root / "agent"
            action_dir = agent_dir / "action"
            action_dir.mkdir(parents=True, exist_ok=True)
            (action_dir / "__init__.py").write_text("", encoding="utf-8")
            (action_dir / "Fishing.py").write_text(
                '\n'.join(
                    [
                        "class Fishing:",
                        "    pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (agent_dir / "Agent_file.py").write_text(
                '\n'.join(
                    [
                        "from action.Fishing import Fishing",
                        "from maa.custom_action import CustomAction",
                        "from maa.resource import resource",
                        "",
                        f'@resource.custom_action("{register_name}")',
                        "class AgentAction(CustomAction):",
                        "    def run(self, context, argv):",
                        "        return True",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

        with tempfile.TemporaryDirectory() as temp_a, tempfile.TemporaryDirectory() as temp_b:
            root_a = Path(temp_a)
            root_b = Path(temp_b)
            _write_bundle(root_a, "alpha")
            _write_bundle(root_b, "beta")

            maafw_a = MaaFW()
            maafw_b = MaaFW()
            self.assertTrue(
                maafw_a.load_embedded_agent_custom(
                    agent_root=root_a / "agent",
                    agent_entry=root_a / "agent" / "Agent_file.py",
                )
            )
            self.assertTrue(
                maafw_b.load_embedded_agent_custom(
                    agent_root=root_b / "agent",
                    agent_entry=root_b / "agent" / "Agent_file.py",
                )
            )
            self.assertIn("alpha", maafw_a.resource.custom_action_list)
            self.assertIn("beta", maafw_b.resource.custom_action_list)


if __name__ == "__main__":
    unittest.main()
