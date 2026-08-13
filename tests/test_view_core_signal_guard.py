import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VIEW_ROOT = PROJECT_ROOT / "app" / "view"
COORDINATOR_PATH = PROJECT_ROOT / "app" / "core" / "core.py"


def _attribute_path(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _attribute_path(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


class ViewCoreSignalBoundaryTests(unittest.TestCase):
    def test_view_does_not_access_core_signal_bus(self):
        violations: list[str] = []

        for file_path in VIEW_ROOT.rglob("*.py"):
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
            relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == "CoreSignalBus":
                            violations.append(
                                f"{relative_path}:{node.lineno}: CoreSignalBus import"
                            )
                elif isinstance(node, ast.Name) and node.id == "CoreSignalBus":
                    violations.append(
                        f"{relative_path}:{node.lineno}: CoreSignalBus reference"
                    )
                elif isinstance(node, ast.Attribute):
                    path = _attribute_path(node)
                    if path.endswith((".signal_bus", ".fs_signal_bus", ".fs_signals")):
                        violations.append(f"{relative_path}:{node.lineno}: {path}")
                    elif path.endswith(".signals") and "service_coordinator" in path:
                        violations.append(f"{relative_path}:{node.lineno}: {path}")

        self.assertEqual(
            [],
            violations,
            msg="View 只能订阅 ServiceCoordinator.view_signals 或全局 signalBus",
        )

    def test_coordinator_does_not_expose_core_signal_aliases(self):
        source = COORDINATOR_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(COORDINATOR_PATH))
        forbidden_attributes = {
            "signal_bus",
            "fs_signal_bus",
        }
        forbidden_properties = {
            "signals",
            "fs_signals",
        }
        violations: list[str] = []

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
                and node.attr in forbidden_attributes
            ):
                violations.append(f"{node.lineno}: self.{node.attr}")
            elif (
                isinstance(node, ast.FunctionDef)
                and node.name in forbidden_properties
            ):
                violations.append(f"{node.lineno}: property {node.name}")

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
