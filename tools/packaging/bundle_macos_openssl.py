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

OPENSSL_BUNDLE_ORDER = ("libcrypto.3.dylib", "libssl.3.dylib", "libcrypto.dylib", "libssl.dylib")

REQUIRED_CRYPTO_SYMBOL = "_EVP_DigestSqueeze"

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


def resolve_openssl_lib_dir() -> Path:
    prefix = brew_openssl_prefix()
    candidates: list[Path] = []
    if prefix is not None:
        candidates.append(prefix / "lib")
    candidates.extend(
        [
            Path("/opt/homebrew/opt/openssl@3/lib"),
            Path("/usr/local/opt/openssl@3/lib"),
        ]
    )
    for lib_dir in candidates:
        if (lib_dir / "libcrypto.3.dylib").is_file() and (lib_dir / "libssl.3.dylib").is_file():
            return lib_dir
    raise FileNotFoundError("cannot locate a complete openssl@3 lib directory on the build host")


def is_openssl_dependency(dependency: str) -> bool:
    name = Path(dependency).name
    return name in OPENSSL_DYLIB_NAMES or "openssl@3" in dependency


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


def dylib_exports_symbol(dylib: Path, symbol: str) -> bool:
    result = subprocess.run(
        ["nm", "-gU", str(dylib)],
        check=True,
        capture_output=True,
        text=True,
    )
    return symbol in result.stdout


def install_openssl_dylibs(macos_dir: Path, openssl_lib_dir: Path) -> None:
    """始终用构建机 openssl@3 覆盖产物内旧版 dylib（Nuitka 可能先收录更老的 libcrypto）。"""
    for name in OPENSSL_BUNDLE_ORDER:
        source = openssl_lib_dir / name
        if not source.is_file():
            continue
        destination = macos_dir / name
        shutil.copy2(source, destination)
        set_dylib_id(destination, f"@executable_path/{name}")

    libssl = macos_dir / "libssl.3.dylib"
    if libssl.is_file():
        install_name, dependencies = parse_otool_libraries(libssl)
        for dependency in dependencies:
            if Path(dependency).name == "libcrypto.3.dylib":
                change_dylib_reference(
                    libssl,
                    dependency,
                    "@executable_path/libcrypto.3.dylib",
                )
        if install_name and install_name.startswith("/"):
            set_dylib_id(libssl, "@executable_path/libssl.3.dylib")

    libcrypto = macos_dir / "libcrypto.3.dylib"
    if libcrypto.is_file() and not dylib_exports_symbol(libcrypto, REQUIRED_CRYPTO_SYMBOL):
        raise RuntimeError(
            f"{libcrypto} is too old for cryptography (missing {REQUIRED_CRYPTO_SYMBOL}); "
            f"upgrade brew openssl@3 on the CI runner"
        )


def collect_absolute_openssl_refs(macho_files: list[Path]) -> dict[str, set[Path]]:
    refs: dict[str, set[Path]] = {}
    for macho in macho_files:
        install_name, dependencies = parse_otool_libraries(macho)
        if (
            macho.suffix == ".dylib"
            and install_name
            and install_name.startswith("/")
            and is_openssl_dependency(install_name)
        ):
            refs.setdefault(install_name, set()).add(macho)

        for dependency in dependencies:
            if dependency.startswith("/") and is_openssl_dependency(dependency):
                refs.setdefault(dependency, set()).add(macho)
    return refs


def bundle_openssl(macos_dir: Path) -> None:
    macos_dir = macos_dir.resolve()
    if not macos_dir.is_dir():
        raise FileNotFoundError(f"missing macOS bundle directory: {macos_dir}")

    openssl_lib_dir = resolve_openssl_lib_dir()
    install_openssl_dylibs(macos_dir, openssl_lib_dir)

    macho_files = iter_macho_files(macos_dir)
    if not macho_files:
        raise RuntimeError(f"no Mach-O binaries found under {macos_dir}")

    for _ in range(8):
        macho_files = iter_macho_files(macos_dir)
        refs = collect_absolute_openssl_refs(macho_files)
        if not refs:
            break

        for dependency, binaries in sorted(refs.items()):
            destination_name = Path(dependency).name
            target = f"@executable_path/{destination_name}"
            for binary in binaries:
                if binary.suffix == ".dylib" and binary.name == destination_name:
                    install_name, _ = parse_otool_libraries(binary)
                    if install_name and install_name.startswith("/"):
                        set_dylib_id(binary, target)
                change_dylib_reference(binary, dependency, target)

    macho_files = iter_macho_files(macos_dir)
    remaining = collect_absolute_openssl_refs(macho_files)
    if remaining:
        details = "\n".join(
            f"  {dependency}: {', '.join(str(path) for path in sorted(binaries))}"
            for dependency, binaries in sorted(remaining.items())
        )
        raise RuntimeError(
            "failed to rewrite all OpenSSL dylib references:\n" + details
        )

    rust_binding = macos_dir / "cryptography" / "hazmat" / "bindings" / "_rust.so"
    if rust_binding.is_file():
        _, dependencies = parse_otool_libraries(rust_binding)
        for dependency in dependencies:
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
