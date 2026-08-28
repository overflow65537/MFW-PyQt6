#!/usr/bin/env python3
"""将 MaaAgentBinary（ADB minicap/minitouch 等）拷贝进 macOS 发行目录。"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
from pathlib import Path


def resolve_maagentbinary_root() -> Path:
    spec = importlib.util.find_spec("MaaAgentBinary")
    if spec is None:
        raise RuntimeError("MaaAgentBinary is not installed")

    search_locations = spec.submodule_search_locations
    if search_locations:
        return Path(next(iter(search_locations))).resolve()

    if spec.origin and spec.origin != "namespace":
        return Path(spec.origin).resolve().parent

    import MaaAgentBinary  # noqa: PLC0415

    package_path = getattr(MaaAgentBinary, "__path__", None)
    if package_path:
        return Path(package_path[0]).resolve()

    module_file = getattr(MaaAgentBinary, "__file__", None)
    if module_file:
        return Path(module_file).resolve().parent

    raise RuntimeError("cannot locate MaaAgentBinary installation root")


def copy_maagentbinary(destination: Path) -> None:
    source = resolve_maagentbinary_root()
    destination = destination.resolve()
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Copy MaaAgentBinary into a distribution directory.")
    parser.add_argument(
        "destination",
        type=Path,
        help="Target directory, e.g. MFW.app/Contents/MacOS/MaaAgentBinary",
    )
    args = parser.parse_args(argv)
    copy_maagentbinary(args.destination)

    minicap = args.destination / "minicap" / "arm64-v8a" / "lib" / "android-21" / "minicap.so"
    if not minicap.is_file():
        raise FileNotFoundError(f"missing expected agent binary: {minicap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
