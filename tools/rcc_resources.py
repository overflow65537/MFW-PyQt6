#   This file is part of MFW-ChainFlow Assistant.
#
#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.
#
#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.
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
rcc_path = find_pyside6_tool("rcc")
if not rcc_path:
    rcc_path = find_pyside6_tool("pyside6-rcc") or "rcc"

if i18n_json_path.is_file():
    try:
        with open(i18n_json_path, encoding="utf-8") as handle:
            data = json.load(handle)
        configured = data.get("rcc")
        if configured:
            rcc_path = configured
            if os.path.isdir(rcc_path):
                rcc_path = os.path.join(
                    rcc_path, "rcc.exe" if os.name == "nt" else "rcc"
                )
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

print(f"Using tool: {rcc_path}")
try:
    subprocess.run(
        [rcc_path, str(qrc_path), "-o", str(output_path)],
        check=True,
    )
except subprocess.CalledProcessError as exc:
    print(f"[Failed] rcc: {exc}", file=sys.stderr)
    sys.exit(1)
except FileNotFoundError:
    print(f"[Failed] Tool not found: {rcc_path}", file=sys.stderr)
    sys.exit(1)

print(f"[Success] {qrc_path.name} -> {output_path.relative_to(project_root)}")
