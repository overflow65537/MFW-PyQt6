#!/usr/bin/env python3
"""从 MFW-Updater 独立仓库的 GitHub Release 下载预编译 standalone 产物。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


def _request_json(url: str, token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "mfw-packaging-fetch-updater",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def _download_file(url: str, destination: Path, token: str | None) -> None:
    headers = {"User-Agent": "mfw-packaging-fetch-updater"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/octet-stream"
    request = urllib.request.Request(url, headers=headers)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=600) as response, destination.open(
        "wb"
    ) as handle:
        shutil.copyfileobj(response, handle)


def asset_name(platform: str, arch: str) -> str:
    if platform == "win":
        return f"MFWUpdater-{platform}-{arch}.zip"
    return f"MFWUpdater-{platform}-{arch}.tar.gz"


def resolve_release(repo: str, tag: str, token: str | None) -> dict:
    if tag == "latest":
        url = f"https://api.github.com/repos/{repo}/releases/latest"
    else:
        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    payload = _request_json(url, token)
    if not isinstance(payload, dict):
        raise RuntimeError(f"unexpected GitHub API response for {url}")
    return payload


def resolve_asset_download_url(
    repo: str, release: dict, asset_file_name: str, token: str | None
) -> str:
    assets = release.get("assets") or []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        if asset.get("name") == asset_file_name:
            if token:
                return str(asset["url"])
            browser_url = asset.get("browser_download_url")
            if browser_url:
                return str(browser_url)
    raise RuntimeError(
        f"release {release.get('tag_name')} in {repo} has no asset {asset_file_name}"
    )


def extract_archive(archive_path: Path, output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = archive_path.suffix.lower()
    if archive_path.name.endswith(".tar.gz"):
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(output_dir)
        return
    if suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(output_dir)
        return
    raise RuntimeError(f"unsupported updater archive: {archive_path}")


def fetch_mfw_updater(
    *,
    repo: str,
    platform: str,
    arch: str,
    output_dir: Path,
    tag: str = "latest",
    token: str | None = None,
) -> Path:
    release = resolve_release(repo, tag, token)
    name = asset_name(platform, arch)
    download_url = resolve_asset_download_url(repo, release, name, token)
    with tempfile.TemporaryDirectory(prefix="mfw-updater-fetch-") as tmp:
        archive_path = Path(tmp) / name
        _download_file(download_url, archive_path, token)
        extract_archive(archive_path, output_dir)
    executable = (
        output_dir / "MFWUpdater.exe"
        if platform == "win"
        else output_dir / "MFWUpdater"
    )
    if not executable.is_file():
        raise RuntimeError(f"extracted updater missing executable: {executable}")
    return output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=os.environ.get("MFW_UPDATER_REPOSITORY", "overflow65537/MFW-Updater"),
        help="GitHub 仓库 owner/name（默认 overflow65537/MFW-Updater）",
    )
    parser.add_argument(
        "--tag",
        default=os.environ.get("MFW_UPDATER_TAG", "latest"),
        help="Release 标签，默认 latest",
    )
    parser.add_argument("--platform", required=True, choices=["win", "linux", "macos"])
    parser.add_argument("--arch", required=True, choices=["x86_64", "aarch64"])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/updater.dist"),
        help="解压目标目录（Nuitka updater.dist 布局）",
    )
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        fetch_mfw_updater(
            repo=args.repo,
            platform=args.platform,
            arch=args.arch,
            output_dir=args.output.resolve(),
            tag=args.tag,
            token=token,
        )
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(f"[INFO] updater ready at {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
