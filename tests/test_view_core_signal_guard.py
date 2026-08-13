import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "app"
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
    def test_legacy_view_signal_names_are_removed(self):
        forbidden_names = (
            "FromeServiceCoordinator",
            "fs_task_",
            "fs_config_",
            "fs_reinit_requested",
        )
        violations: list[str] = []

        for file_path in APP_ROOT.rglob("*.py"):
            source = file_path.read_text(encoding="utf-8-sig")
            for name in forbidden_names:
                if name in source:
                    relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()
                    violations.append(f"{relative_path}: {name}")

        self.assertEqual([], violations)

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

    def test_view_does_not_mutate_task_or_config_business_fields(self):
        forbidden_attributes = {
            "task_option",
            "current_options",
            "is_checked",
            "is_hidden",
        }
        violations: list[str] = []

        def check_target(target: ast.AST, relative_path: str) -> None:
            if isinstance(target, (ast.Tuple, ast.List)):
                for item in target.elts:
                    check_target(item, relative_path)
                return
            if isinstance(target, ast.Attribute):
                path = _attribute_path(target)
                if target.attr in forbidden_attributes or path.endswith(
                    (".item.name", ".task.name")
                ):
                    violations.append(f"{relative_path}:{target.lineno}: {path}")
                    return
            if isinstance(target, ast.Subscript):
                owner = _attribute_path(target.value)
                if owner.endswith((".task_option", ".current_options")):
                    violations.append(f"{relative_path}:{target.lineno}: {owner}[...]")

        for file_path in VIEW_ROOT.rglob("*.py"):
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
            relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    targets = (
                        node.targets
                        if isinstance(node, ast.Assign)
                        else [node.target]
                    )
                    for target in targets:
                        check_target(target, relative_path)
                elif isinstance(node, ast.Delete):
                    for target in node.targets:
                        check_target(target, relative_path)

        self.assertEqual(
            [],
            violations,
            msg="View 不得直接修改 TaskItem/ConfigItem 业务字段",
        )


if __name__ == "__main__":
    unittest.main()
