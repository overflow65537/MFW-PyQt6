import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "app"


def _resolve_module(module: str) -> Path | None:
    rel = Path(*module.split("."))
    file_path = PROJECT_ROOT / rel.with_suffix(".py")
    package_init = PROJECT_ROOT / rel / "__init__.py"
    if file_path.exists():
        return file_path
    if package_init.exists():
        return package_init
    return None


class ImportPathCaseGuardTests(unittest.TestCase):
    def test_app_python_module_paths_are_lowercase(self):
        violations: list[str] = []

        for file_path in APP_ROOT.rglob("*.py"):
            relative_path = file_path.relative_to(PROJECT_ROOT)
            for part in relative_path.parts:
                if part == "__init__.py":
                    continue
                if any(ch.isupper() for ch in part):
                    violations.append(relative_path.as_posix())
                    break

        self.assertEqual(
            [],
            violations,
            msg="app 下可导入的 Python 模块与目录必须使用小写 snake_case 命名",
        )

    def test_app_imports_resolve_with_exact_case(self):
        violations: list[str] = []

        for file_path in APP_ROOT.rglob("*.py"):
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
            relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level == 0 and node.module and node.module.startswith("app."):
                        if _resolve_module(node.module) is None:
                            violations.append(
                                f"{relative_path}:{node.lineno}: from {node.module} import ..."
                            )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("app.") and _resolve_module(alias.name) is None:
                            violations.append(
                                f"{relative_path}:{node.lineno}: import {alias.name}"
                            )

        self.assertEqual(
            [],
            violations,
            msg="app.* 导入必须能在磁盘上解析到精确大小写匹配的模块路径",
        )


if __name__ == "__main__":
    unittest.main()