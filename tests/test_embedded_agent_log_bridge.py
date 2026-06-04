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

    def test_does_not_forward_app_path_under_project_parent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            custom_root = root / "MPAcustom"
            utils_dir = custom_root / "utils"
            utils_dir.mkdir(parents=True)
            (utils_dir / "__init__.py").write_text(
                "\n".join(
                    [
                        "import logging",
                        "logger = logging.getLogger()",
                        "logger.setLevel(logging.DEBUG)",
                    ]
                ),
                encoding="utf-8",
            )
            app_dir = root / "app"
            app_dir.mkdir()
            fake_widget = app_dir / "logoutput_widget.py"
            fake_widget.write_text("# ui\n", encoding="utf-8")

            import sys

            sys.path.insert(0, str(custom_root))
            sys.path.insert(1, str(root))
            emitted: list[tuple[str, str]] = []
            bridge = EmbeddedAgentLogBridge()
            try:
                for name in ("utils", "utils.logger"):
                    sys.modules.pop(name, None)
                bridge.attach(
                    lambda level, text: emitted.append((level, text)),
                    custom_root=custom_root,
                )
                record = logging.LogRecord(
                    name="root",
                    level=logging.INFO,
                    pathname=str(fake_widget),
                    lineno=1,
                    msg="ui side",
                    args=(),
                    exc_info=None,
                )
                logging.getLogger().callHandlers(record)
            finally:
                bridge.detach()
                sys.path.remove(str(custom_root))
                sys.path.remove(str(root))

            self.assertEqual(emitted, [])


if __name__ == "__main__":
    unittest.main()
