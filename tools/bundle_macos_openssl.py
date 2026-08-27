#!/usr/bin/env python3
"""将 OpenSSL dylib 打入 macOS 发行包并修正 cryptography 等模块的绝对路径依赖。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

OPENSSL_DYLIB_NAMES = frozenset(
    {
        "libssl.3.dylib",
        "libcrypto.3.dylib",
        "libssl.dylib",
        "libcrypto.dylib",
    }
)

MACHO_MAGICS = frozenset(
    {
        b"\xcf\xfa\xed\xfe",  # MH_MAGIC_64
        b"\xce\xfa\xed\xfe",  # MH_MAGIC
        b"\xfe\xed\xfa\xcf",  # MH_CIGAM_64
        b"\xfe\xed\xfa\xce",  # MH_CIGAM
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


def otool_linked_libraries(path: Path) -> list[str]:
    result = subprocess.run(
        ["otool", "-L", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    libraries: list[str] = []
    for line in result.stdout.splitlines()[1:]:
        dependency = line.strip().split(" (compatibility", 1)[0].strip()
        if dependency:
            libraries.append(dependency)
    return libraries


def brew_openssl_prefix() -> Path | None:
    result = subprocess.run(
        ["brew", "--prefix", "openssl@3"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    prefix = result.stdout.strip()
    if not prefix:
        return None
    return Path(prefix)


def locate_openssl_dylib(dependency: str) -> Path | None:
    dep_path = Path(dependency)
    if dep_path.is_file():
        return dep_path

    name = dep_path.name
    if name not in OPENSSL_DYLIB_NAMES:
        return None

    prefix = brew_openssl_prefix()
    if prefix is not None:
        candidate = prefix / "lib" / name
        if candidate.is_file():
            return candidate

    for base in (
        "/opt/homebrew/opt/openssl@3/lib",
        "/usr/local/opt/openssl@3/lib",
    ):
        candidate = Path(base) / name
        if candidate.is_file():
            return candidate
    return None


def is_openssl_dependency(dependency: str) -> bool:
    name = Path(dependency).name
    return name in OPENSSL_DYLIB_NAMES or "openssl@3" in dependency


def change_dylib_reference(binary: Path, old_path: str, new_path: str) -> None:
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
    if result.returncode != 0 and "does not exist" not in result.stderr:
        raise RuntimeError(
            f"install_name_tool failed for {binary}: {result.stderr.strip()}"
        )


def bundle_openssl(macos_dir: Path) -> None:
    macos_dir = macos_dir.resolve()
    if not macos_dir.is_dir():
        raise FileNotFoundError(f"missing macOS bundle directory: {macos_dir}")

    macho_files = iter_macho_files(macos_dir)
    if not macho_files:
        raise RuntimeError(f"no Mach-O binaries found under {macos_dir}")

    for _ in range(8):
        macho_files = iter_macho_files(macos_dir)
        pending: set[str] = set()
        for macho in macho_files:
            for dependency in otool_linked_libraries(macho):
                if dependency.startswith("/") and is_openssl_dependency(dependency):
                    pending.add(dependency)

        if not pending:
            break

        for dependency in sorted(pending):
            source = locate_openssl_dylib(dependency)
            if source is None:
                raise FileNotFoundError(
                    f"cannot locate OpenSSL library for dependency: {dependency}"
                )
            destination = macos_dir / source.name
            if not destination.exists():
                shutil.copy2(source, destination)

        for macho in macho_files:
            for dependency in sorted(pending):
                destination_name = Path(dependency).name
                change_dylib_reference(
                    macho,
                    dependency,
                    f"@executable_path/{destination_name}",
                )
    else:
        raise RuntimeError("failed to rewrite all OpenSSL dylib references")

    rust_binding = macos_dir / "cryptography" / "hazmat" / "bindings" / "_rust.so"
    if rust_binding.is_file():
        for dependency in otool_linked_libraries(rust_binding):
            if dependency.startswith("/") and is_openssl_dependency(dependency):
                raise RuntimeError(
                    f"OpenSSL dependency still absolute in {rust_binding}: {dependency}"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bundle OpenSSL dylibs into a macOS app MacOS directory."
    )
    parser.add_argument(
        "macos_dir",
        type=Path,
        help="Path to MFW.app/Contents/MacOS",
    )
    args = parser.parse_args(argv)
    bundle_openssl(args.macos_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
