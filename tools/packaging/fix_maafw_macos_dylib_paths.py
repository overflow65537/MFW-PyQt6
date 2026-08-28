#!/usr/bin/env python3
"""修正外置 maafw/ 内 macOS dylib 的 @executable_path/maa/bin 引用为 @loader_path。"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

MACHO_MAGICS = frozenset(
    {
        b"\xcf\xfa\xed\xfe",
        b"\xce\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xfe\xed\xfa\xce",
    }
)

EXECUTABLE_PATH_MAA_BIN = "@executable_path/maa/bin/"


def is_macho_file(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(4) in MACHO_MAGICS
    except OSError:
        return False


def iter_macho_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and is_macho_file(path):
            files.append(path)
    return files


def parse_otool_libraries(path: Path) -> tuple[str | None, list[str]]:
    result = subprocess.run(
        ["otool", "-L", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) <= 1:
        return None, []

    linked: list[str] = []
    for line in lines[1:]:
        dependency = line.strip().split(" (compatibility", 1)[0].strip()
        if dependency:
            linked.append(dependency)

    install_name: str | None = None
    dependencies = linked
    if path.suffix == ".dylib" and linked:
        install_name = linked[0]
        dependencies = linked[1:]
    elif linked and Path(linked[0]).name == path.name:
        dependencies = linked[1:]

    return install_name, dependencies


def rewrite_maafw_dependency(old_path: str) -> str | None:
    if old_path.startswith(EXECUTABLE_PATH_MAA_BIN):
        return "@loader_path/" + old_path[len(EXECUTABLE_PATH_MAA_BIN):]
    if "/maa/bin/" in old_path and old_path.startswith("/"):
        suffix = old_path.split("/maa/bin/", 1)[1]
        if suffix:
            return "@loader_path/" + suffix
    return None


def change_dylib_reference(binary: Path, old_path: str, new_path: str) -> bool:
    result = subprocess.run(
        [
            "install_name_tool",
            "-change",
            old_path,
            new_path,
            str(binary),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True
    stderr = result.stderr.strip()
    if "does not exist" in stderr or "would duplicate path" in stderr:
        return False
    raise RuntimeError(f"install_name_tool failed for {binary}: {stderr}")


def set_dylib_id(dylib: Path, install_name: str) -> None:
    result = subprocess.run(
        ["install_name_tool", "-id", install_name, str(dylib)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"install_name_tool -id failed for {dylib}: {result.stderr.strip()}"
        )


def collect_maafw_path_refs(macho_files: list[Path]) -> dict[str, set[Path]]:
    refs: dict[str, set[Path]] = {}
    for macho in macho_files:
        install_name, dependencies = parse_otool_libraries(macho)
        candidates: list[str] = []
        if install_name:
            candidates.append(install_name)
        candidates.extend(dependencies)
        for dependency in candidates:
            if rewrite_maafw_dependency(dependency) is not None:
                refs.setdefault(dependency, set()).add(macho)
    return refs


def fix_maafw_macos_dylib_paths(maafw_root: Path) -> None:
    maafw_root = maafw_root.resolve()
    if not maafw_root.is_dir():
        raise FileNotFoundError(f"missing maafw directory: {maafw_root}")

    for _ in range(8):
        macho_files = iter_macho_files(maafw_root)
        refs = collect_maafw_path_refs(macho_files)
        if not refs:
            break

        for old_path, binaries in sorted(refs.items()):
            new_path = rewrite_maafw_dependency(old_path)
            if new_path is None:
                continue
            for binary in binaries:
                if binary.suffix == ".dylib" and Path(old_path).name == binary.name:
                    install_name, _ = parse_otool_libraries(binary)
                    if install_name == old_path:
                        set_dylib_id(binary, new_path)
                change_dylib_reference(binary, old_path, new_path)
    else:
        macho_files = iter_macho_files(maafw_root)
        remaining = collect_maafw_path_refs(macho_files)
        details = "\n".join(
            f"  {path}: {', '.join(str(b) for b in sorted(binaries))}"
            for path, binaries in sorted(remaining.items())
        )
        raise RuntimeError(
            "failed to rewrite maafw dylib references:\n" + details
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fix maafw macOS dylib paths for external maafw layout."
    )
    parser.add_argument(
        "maafw_root",
        type=Path,
        help="Path to maafw directory in the release root",
    )
    args = parser.parse_args(argv)
    fix_maafw_macos_dylib_paths(args.maafw_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
