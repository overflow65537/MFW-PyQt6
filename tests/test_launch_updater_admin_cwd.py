"""管理员启动更新器时 cwd 必须是安装根（契约检查，避免拉起完整 UI 依赖）。"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


class LaunchUpdaterAdminCwdContractTests(unittest.TestCase):
    def test_admin_helper_requires_working_dir_kwarg(self) -> None:
        source_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "view"
            / "setting_interface"
            / "setting_interface.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        helper = None
        launch = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                if node.name == "_start_windows_process_with_admin":
                    helper = node
                elif node.name == "launch_updater_process":
                    launch = node

        self.assertIsNotNone(helper)
        assert helper is not None
        arg_names = [arg.arg for arg in helper.args.args]
        kwonly = [arg.arg for arg in helper.args.kwonlyargs]
        self.assertIn("executable", arg_names)
        self.assertIn("working_dir", kwonly)

        # 函数体内不得再把 working_dir 默认为 executable.parent
        helper_src = ast.get_source_segment(
            source_path.read_text(encoding="utf-8"), helper
        )
        self.assertIsNotNone(helper_src)
        assert helper_src is not None
        self.assertNotIn("executable.parent", helper_src)

        self.assertIsNotNone(launch)
        assert launch is not None
        launch_src = ast.get_source_segment(
            source_path.read_text(encoding="utf-8"), launch
        )
        self.assertIsNotNone(launch_src)
        assert launch_src is not None
        self.assertIn("working_dir=install_root", launch_src)


if __name__ == "__main__":
    unittest.main()
