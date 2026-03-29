import ast
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = PROJECT_ROOT / "app" / "core"
VIEW_ROOT = PROJECT_ROOT / "app" / "view"
ITEM_FILE = CORE_ROOT / "item.py"
EVENTS_FILE = CORE_ROOT / "events.py"

VIEW_SIGNAL_EMIT_PATTERN = re.compile(
    r"(?:^|\W)(?:self\.)?(?:service_coordinator|option_service)\.signal_bus\.\w+\.emit\s*\("
)


def _iter_python_files(root: Path):
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def _parse_python_file(file_path: Path) -> ast.AST:
    return ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))


class ArchitectureGuardTests(unittest.TestCase):
    def test_core_does_not_import_global_signal_bus(self):
        violations: list[str] = []

        for file_path in _iter_python_files(CORE_ROOT):
            tree = _parse_python_file(file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "app.common.signal_bus":
                    violations.append(str(file_path.relative_to(PROJECT_ROOT)))
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "app.common.signal_bus":
                            violations.append(str(file_path.relative_to(PROJECT_ROOT)))

        self.assertEqual(
            [],
            violations,
            msg="app/core 中禁止直接 import app.common.signal_bus",
        )

    def test_view_does_not_emit_core_internal_signal_bus(self):
        violations: list[str] = []

        for file_path in _iter_python_files(VIEW_ROOT):
            source = file_path.read_text(encoding="utf-8")
            if VIEW_SIGNAL_EMIT_PATTERN.search(source):
                violations.append(str(file_path.relative_to(PROJECT_ROOT)))

        self.assertEqual(
            [],
            violations,
            msg="View 层禁止直接 emit service_coordinator.signal_bus 或 option_service.signal_bus",
        )

    def test_item_py_only_contains_models(self):
        source = ITEM_FILE.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(ITEM_FILE))

        class_names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        }

        self.assertNotIn("CoreSignalBus", class_names)
        self.assertNotIn("FromServiceCoordinator", class_names)
        self.assertNotRegex(source, r"from\s+PySide6\.QtCore\s+import\s+.*\bQObject\b")
        self.assertNotRegex(source, r"from\s+PySide6\.QtCore\s+import\s+.*\bSignal\b")

    def test_events_py_contains_core_event_buses(self):
        self.assertTrue(EVENTS_FILE.exists(), msg="app/core/events.py 必须存在")

        tree = _parse_python_file(EVENTS_FILE)
        class_names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        }

        self.assertIn("CoreSignalBus", class_names)
        self.assertIn("FromServiceCoordinator", class_names)


if __name__ == "__main__":
    unittest.main()