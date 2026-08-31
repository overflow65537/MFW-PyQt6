#   This file is part of MFW-ChainFlow Assistant.
#
#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.
#
#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/agpl-3.0.html>.
#
#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""将 ``app.qrc``（i18n + icons）编译为内嵌 Qt 资源 ``app/resources/app_rc.py``。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_pyside6_tool(tool_name: str) -> str | None:
    tool_path = shutil.which(tool_name)
    if tool_path:
        return tool_path
    try:
        import PySide6

        pyside6_path = Path(PySide6.__file__).parent
        if os.name == "nt":
            tool_exe = pyside6_path / f"{tool_name}.exe"
            if tool_exe.exists():
                return str(tool_exe)
        else:
            candidate = pyside6_path / tool_name
            if candidate.exists():
                return str(candidate)
    except ImportError:
        pass
    return None


def resolve_rcc_command() -> list[str]:
    """优先 ``pyside6-rcc``；若仅有 Qt ``rcc``，强制 ``-g python``。

    裸 ``rcc`` 默认输出 C++，写入 ``.py`` 会导致 SyntaxError（如 QT_RCC_MANGLE_*）。
    使用 zlib，避免默认 zstd 压缩在跨平台打包后无法解压。
    """
    pyside_rcc = find_pyside6_tool("pyside6-rcc")
    if pyside_rcc:
        return [pyside_rcc, "--compress-algo", "zlib"]

    rcc = find_pyside6_tool("rcc")
    if rcc:
        return [rcc, "-g", "python", "--compress-algo", "zlib"]

    return ["pyside6-rcc", "--compress-algo", "zlib"]


script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
if not (project_root / "main.py").exists():
    if (Path.cwd() / "main.py").exists():
        project_root = Path.cwd()
    else:
        print("[ERROR] can't find project root (can't find main.py)", file=sys.stderr)
        sys.exit(1)

os.chdir(project_root)

i18n_json_path = script_dir / "i18n.json"
rcc_cmd = resolve_rcc_command()

if i18n_json_path.is_file():
    try:
        with open(i18n_json_path, encoding="utf-8") as handle:
            data = json.load(handle)
        configured = data.get("rcc")
        if configured:
            tool = configured
            if os.path.isdir(tool):
                tool = os.path.join(
                    tool,
                    "pyside6-rcc.exe" if os.name == "nt" else "pyside6-rcc",
                )
            name = Path(tool).name.lower()
            if "pyside" in name:
                rcc_cmd = [tool, "--compress-algo", "zlib"]
            else:
                rcc_cmd = [tool, "-g", "python", "--compress-algo", "zlib"]
    except Exception as exc:
        print(f"Error reading i18n.json file: {exc}", file=sys.stderr)

qrc_path = project_root / "app" / "resources" / "app.qrc"
output_path = project_root / "app" / "resources" / "app_rc.py"
qm_dir = project_root / "app" / "i18n"
logo_path = project_root / "app" / "assets" / "icons" / "logo.png"

if not qrc_path.is_file():
    print(f"Error: qrc not found: {qrc_path}", file=sys.stderr)
    sys.exit(1)

missing_qm = sorted(
    name
    for name in ("i18n.zh_CN.qm", "i18n.zh_TW.qm", "i18n.ja_JP.qm")
    if not (qm_dir / name).is_file()
)
if missing_qm:
    print(
        f"Error: missing .qm files in {qm_dir}: {', '.join(missing_qm)}",
        file=sys.stderr,
    )
    print("Run python tools/lrelease.py first.", file=sys.stderr)
    sys.exit(1)

if not logo_path.is_file():
    print(f"Error: missing logo: {logo_path}", file=sys.stderr)
    sys.exit(1)

print(f"Using tool: {' '.join(rcc_cmd)}")
try:
    subprocess.run(
        [*rcc_cmd, str(qrc_path), "-o", str(output_path)],
        check=True,
    )
except subprocess.CalledProcessError as exc:
    print(f"[Failed] rcc: {exc}", file=sys.stderr)
    sys.exit(1)
except FileNotFoundError:
    print(f"[Failed] Tool not found: {rcc_cmd[0]}", file=sys.stderr)
    sys.exit(1)

if not output_path.is_file():
    print(f"[Failed] output missing: {output_path}", file=sys.stderr)
    sys.exit(1)

# 防止再次把 C++ rcc 产物当成 Python 模块打进包
head = output_path.read_text(encoding="utf-8", errors="replace")[:4000]
if "QT_RCC_MANGLE" in head or "#include" in head:
    print(
        "[Failed] rcc produced C++ output; use pyside6-rcc or rcc -g python",
        file=sys.stderr,
    )
    sys.exit(1)
if "PySide6" not in head and "qt_resource_data" not in head:
    print("[Failed] rcc output does not look like a Python Qt resource module", file=sys.stderr)
    sys.exit(1)

print(f"[Success] {qrc_path.name} -> {output_path.relative_to(project_root)}")
