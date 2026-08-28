#!/usr/bin/env python3
"""修正 macOS .app 的 Info.plist，使 Qt QLocale::uiLanguages() 能反映系统 UI 语言。

Nuitka 默认生成的 Info.plist 未声明应用支持的语言；macOS 会按「仅英文」过滤
用户语言列表，导致首次启动时 detect_system_language() 误判为英文。
"""

from __future__ import annotations

import argparse
import plistlib
import sys
from pathlib import Path

# 与 app/i18n 及 Language 枚举一致（BCP47 / Apple 常用标识）
SUPPORTED_LOCALIZATIONS = ("en", "zh-Hans", "zh-Hant", "ja")

_ENGLISH_DEVELOPMENT_REGIONS = frozenset(
    {"en", "en_US", "en_GB", "English", "english", "U.S. English"}
)


def patch_info_plist(app_path: Path) -> None:
    plist_path = app_path / "Contents" / "Info.plist"
    if not plist_path.is_file():
        raise FileNotFoundError(f"missing Info.plist: {plist_path}")

    with plist_path.open("rb") as plist_file:
        info = plistlib.load(plist_file)

    info["CFBundleAllowMixedLocalizations"] = True
    info["CFBundleLocalizations"] = list(SUPPORTED_LOCALIZATIONS)

    dev_region = info.get("CFBundleDevelopmentRegion")
    if isinstance(dev_region, str) and dev_region in _ENGLISH_DEVELOPMENT_REGIONS:
        # 避免开发区域固定为英文时覆盖系统首选语言（Qt QTBUG-72491 同类问题）
        del info["CFBundleDevelopmentRegion"]

    with plist_path.open("wb") as plist_file:
        plistlib.dump(info, plist_file, fmt=plistlib.FMT_XML)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Patch MFW.app Info.plist for UI language detection.")
    parser.add_argument("app_path", type=Path, help="path to .app bundle (e.g. build/mfw-release/MFW.app)")
    args = parser.parse_args(argv)

    app_path = args.app_path.resolve()
    if not app_path.is_dir():
        print(f"app bundle not found: {app_path}", file=sys.stderr)
        return 1

    patch_info_plist(app_path)
    print(f"patched Info.plist: {app_path / 'Contents' / 'Info.plist'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
