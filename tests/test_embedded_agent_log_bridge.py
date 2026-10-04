import logging
import tempfile
import unittest
from pathlib import Path

from app.core.runner.embedded_agent_log_bridge import (
    EmbeddedAgentLogBridge,
    collect_agent_loggers,
)


class EmbeddedAgentLogBridgeTests(unittest.TestCase):
    def test_collect_agent_loggers_finds_utils_logger(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_root = Path(temp_dir) / "MPAcustom"
            utils_dir = custom_root / "utils"
            utils_dir.mkdir(parents=True)
            (utils_dir / "__init__.py").write_text(
                "import logging\nlogger = logging.getLogger('agent.test')\n",
                encoding="utf-8",
            )
            import sys

            sys.path.insert(0, str(custom_root))
            try:
                if "utils" in sys.modules:
                    del sys.modules["utils"]
                allowed = (
                    str(custom_root.resolve()).replace("\\", "/").lower() + "/",
                )
                loggers = collect_agent_loggers(custom_root, allowed)
            finally:
                sys.path.remove(str(custom_root))

            self.assertTrue(any(isinstance(x, logging.Logger) for x in loggers))

    def test_attach_forwards_info_to_emit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_root = Path(temp_dir) / "MPAcustom"
            utils_dir = custom_root / "utils"
            utils_dir.mkdir(parents=True)
            (utils_dir / "__init__.py").write_text(
                "\n".join(
                    [
                        "import logging",
                        "logger = logging.getLogger('agent.bridge')",
                        "logger.setLevel(logging.DEBUG)",
                    ]
                ),
                encoding="utf-8",
            )
            import sys

            sys.path.insert(0, str(custom_root))
            emitted: list[tuple[str, str]] = []
            bridge = EmbeddedAgentLogBridge()
            try:
                if "utils" in sys.modules:
                    del sys.modules["utils"]
                count = bridge.attach(
                    lambda level, text: emitted.append((level, text)),
                    custom_root=custom_root,
                )
                self.assertGreaterEqual(count, 1)
                runner = custom_root / "runner.py"
                runner.write_text(
                    "from utils import logger\nlogger.info('hello from agent')\n",
                    encoding="utf-8",
                )
                import runpy

                runpy.run_path(str(runner), run_name="__main__")
            finally:
                bridge.detach()
                sys.path.remove(str(custom_root))

            self.assertIn(("INFO", "hello from agent"), emitted)

    def test_does_not_forward_app_root_logger(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_root = Path(temp_dir) / "MPAcustom"
            utils_dir = custom_root / "utils"
            utils_dir.mkdir(parents=True)
            (utils_dir / "__init__.py").write_text(
                "\n".join(
                    [
                        "import logging",
                        "logger = logging.getLogger('agent.bridge')",
                        "logger.setLevel(logging.DEBUG)",
                    ]
                ),
                encoding="utf-8",
            )
            import sys

            sys.path.insert(0, str(custom_root))
            emitted: list[tuple[str, str]] = []
            bridge = EmbeddedAgentLogBridge()
            try:
                if "utils" in sys.modules:
                    del sys.modules["utils"]
                bridge.attach(
                    lambda level, text: emitted.append((level, text)),
                    custom_root=custom_root,
                )
                logging.getLogger().info("app side message")
            finally:
                bridge.detach()
                sys.path.remove(str(custom_root))

            self.assertEqual(emitted, [])

    def test_does_not_forward_mfw_app_package_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_root = Path(temp_dir) / "MPAcustom"
            utils_dir = custom_root / "utils"
            utils_dir.mkdir(parents=True)
            (utils_dir / "__init__.py").write_text(
                "\n".join(
                    [
                        "import logging",
                        "logger = logging.getLogger('agent.bridge')",
                        "logger.setLevel(logging.DEBUG)",
                    ]
                ),
                encoding="utf-8",
            )

            import app as mfw_app

            mfw_app_file = Path(mfw_app.__file__).resolve()

            import sys

            sys.path.insert(0, str(custom_root))
            emitted: list[tuple[str, str]] = []
            bridge = EmbeddedAgentLogBridge()
            try:
                if "utils" in sys.modules:
                    del sys.modules["utils"]
                bridge.attach(
                    lambda level, text: emitted.append((level, text)),
                    custom_root=custom_root,
                )
                record = logging.LogRecord(
                    name="root",
                    level=logging.INFO,
                    pathname=str(mfw_app_file),
                    lineno=1,
                    msg="ui side",
                    args=(),
                    exc_info=None,
                )
                logging.getLogger().callHandlers(record)
            finally:
                bridge.detach()
                sys.path.remove(str(custom_root))

            self.assertEqual(emitted, [])

    def test_collects_loggers_when_custom_root_under_windows_app_folder(self):
        """D:\\APP\\... 规范化后含 /app/ 子串，不得误判为主程序 app 包。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_root = Path(temp_dir) / "APP" / "MPAcustom" / "agent"
            sink_dir = custom_root / "sink"
            sink_dir.mkdir(parents=True)
            (sink_dir / "resolution_check.py").write_text(
                "\n".join(
                    [
                        "import logging",
                        "logger = logging.getLogger('agent.sink.resolution_check')",
                    ]
                ),
                encoding="utf-8",
            )
            import importlib.util
            import sys

            spec = importlib.util.spec_from_file_location(
                "sink.resolution_check",
                sink_dir / "resolution_check.py",
            )
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            sys.modules["sink.resolution_check"] = module
            spec.loader.exec_module(module)

            allowed = (
                str(custom_root.resolve()).replace("\\", "/").lower() + "/",
            )
            loggers = collect_agent_loggers(custom_root, allowed)
            sys.modules.pop("sink.resolution_check", None)

            self.assertTrue(
                any(
                    isinstance(x, logging.Logger)
                    and x.name == "agent.sink.resolution_check"
                    for x in loggers
                )
            )


if __name__ == "__main__":
    unittest.main()
