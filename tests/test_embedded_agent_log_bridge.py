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
            root = Path(temp_dir)
            utils_dir = root / "utils"
            utils_dir.mkdir()
            (utils_dir / "__init__.py").write_text(
                "import logging\nlogger = logging.getLogger('agent.test')\n",
                encoding="utf-8",
            )
            import sys

            sys.path.insert(0, str(root))
            try:
                if "utils" in sys.modules:
                    del sys.modules["utils"]
                loggers = collect_agent_loggers(root)
            finally:
                sys.path.remove(str(root))

            self.assertTrue(any(isinstance(x, logging.Logger) for x in loggers))

    def test_attach_forwards_info_to_emit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            utils_dir = root / "utils"
            utils_dir.mkdir()
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

            sys.path.insert(0, str(root))
            emitted: list[tuple[str, str]] = []
            bridge = EmbeddedAgentLogBridge()
            try:
                if "utils" in sys.modules:
                    del sys.modules["utils"]
                count = bridge.attach(
                    lambda level, text: emitted.append((level, text)),
                    root,
                )
                self.assertGreaterEqual(count, 1)
                import utils

                utils.logger.info("hello from agent")
            finally:
                bridge.detach()
                sys.path.remove(str(root))

            self.assertIn(("INFO", "hello from agent"), emitted)


if __name__ == "__main__":
    unittest.main()
