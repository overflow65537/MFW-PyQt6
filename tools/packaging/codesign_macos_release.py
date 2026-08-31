#!/usr/bin/env python3
"""对 macOS 发行根下经 install_name_tool 修改过的 Mach-O 做 ad-hoc 重签名。"""

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


def collect_release_macho_files(release_root: Path) -> list[Path]:
    release_root = release_root.resolve()
    targets: list[Path] = []

    maafw_root = release_root / "maafw"
    if maafw_root.is_dir():
        targets.extend(iter_macho_files(maafw_root))

    updater_dir = release_root / "MFWUpdater"
    if updater_dir.is_dir():
        targets.extend(iter_macho_files(updater_dir))

    # 路径越深越先签，降低 @loader_path 依赖链上的验签失败概率。
    return sorted(set(targets), key=lambda path: len(path.parts), reverse=True)


def codesign_file(path: Path, identity: str) -> None:
    result = subprocess.run(
        ["codesign", "--force", "--sign", identity, str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"codesign failed for {path}: {result.stderr.strip() or result.stdout.strip()}"
        )


def verify_codesign(path: Path) -> None:
    result = subprocess.run(
        ["codesign", "--verify", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"codesign verify failed for {path}: {result.stderr.strip() or result.stdout.strip()}"
        )


def codesign_macos_release(release_root: Path, identity: str = "-") -> None:
    release_root = release_root.resolve()
    if not release_root.is_dir():
        raise FileNotFoundError(f"missing release directory: {release_root}")

    targets = collect_release_macho_files(release_root)
    if not targets:
        raise RuntimeError(f"no Mach-O binaries found under {release_root}")

    for path in targets:
        codesign_file(path, identity)
        verify_codesign(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ad-hoc codesign Mach-O files in a macOS release root (maafw/, MFWUpdater/)."
    )
    parser.add_argument(
        "release_root",
        type=Path,
        help="Path to build/mfw-release",
    )
    parser.add_argument(
        "--identity",
        default="-",
        help='codesign identity (default: "-" ad-hoc)',
    )
    args = parser.parse_args(argv)
    codesign_macos_release(args.release_root, identity=args.identity)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
