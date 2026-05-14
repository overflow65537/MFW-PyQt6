#   This file is part of MFW-ChainFlow Assistant.
#
#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.
#
#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.
#
#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""Windows Nuitka 后处理：仅为发行根生成 file_list.txt（合并由 CI 完成）。"""

import os
import sys
from pathlib import Path

script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
if not (project_root / "main.py").exists():
    if (Path.cwd() / "main.py").exists():
        project_root = Path.cwd()
    else:
        print("[ERROR] can't find project root (can't find main.py)", file=sys.stderr)
        sys.exit(1)

os.chdir(project_root)


def generate_file_list(input_dir: str, output_file: str | None = None) -> bool:
    """在 output_file（默认 <目录名>_file_list.txt）写入发行根内相对路径列表。"""
    input_path = Path(input_dir)
    if not input_path.is_dir():
        print(f"Error: '{input_dir}' is not a directory", file=sys.stderr)
        return False
    if output_file is None:
        output_file = f"{input_path.name}_file_list.txt"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for root, _, files in os.walk(input_path):
                rel_root = os.path.relpath(root, input_path.parent)
                for file in files:
                    if rel_root == input_path.name:
                        file_path = f"./{file}"
                    else:
                        rel_dir = os.path.relpath(root, input_path)
                        file_path = (
                            f"./{file}"
                            if rel_dir == "."
                            else f"./{rel_dir}/{file}"
                        )
                    f.write(file_path + "\n")
            f.write("./file_list.txt\n")
        print(f"[INFO] file list: {output_file}")
        return True
    except OSError as e:
        print(f"Error generating file list: {e}", file=sys.stderr)
        return False


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "--file-list":
        dist_root = os.path.join("build", "main.dist")
        if not os.path.isdir(dist_root):
            print(f"[ERROR] Nuitka output not found: {dist_root}", file=sys.stderr)
            return 1
        out = os.path.join(dist_root, "file_list.txt")
        return 0 if generate_file_list(dist_root, out) else 1
    print(
        "用法: python tools/build_nuitka.py --file-list",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
