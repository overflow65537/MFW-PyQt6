"""资源完整性哈希：对比 MaaResource 接口、interface.json 与 GitHub Release。

三源规则：
- 接口（MaaResourceGetHash）：始终作为实际值参与对比
- interface：仅当 resource.hash 有值时检测，否则视为通过
- GitHub：仅当填写了 github/url，并且成功从当前版本 release body
  解析到关键字后才对比；拉取或解析失败视为通过
- 只有已参与对比的哈希不一致时才判定失败

GitHub release body 在启动检查最新版之后准备：若本次走 GitHub 且
latest 与当前版本相同则复用该次响应；否则再请求当前版本 tag。
结果写入内存与磁盘缓存，任务运行只等待启动预取完成，不再现场查询。
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import quote, urlparse

import requests

from app.utils.logger import logger

DEFAULT_HASH_KEY = "*"
GITHUB_HASH_FETCH_TIMEOUT = 2.0
GITHUB_HASH_PREFETCH_WAIT_TIMEOUT = 5.0
_DISK_CACHE_FILENAME = "github_release_body_cache.json"

_HASH_KEYWORD = r"(?:mfw[-_])?(?:resource[-_.])?(?:hash|哈希)"
_HEX_HASH = re.compile(r"^[0-9a-fA-F]{8,}$")
_HASH_LINE = re.compile(
    rf"^\s*(?:[-*]\s+)?{_HASH_KEYWORD}"
    rf"(?:\[\s*(?P<name>[^\]]+?)\s*\])?"
    rf"\s*[:=]\s*[`'\"]?(?P<value>[^\s`'\",;]+)",
    re.IGNORECASE | re.MULTILINE,
)
_COMMENT_BLOCK = re.compile(
    rf"<!--\s*{_HASH_KEYWORD}\b(?P<body>.*?)-->",
    re.IGNORECASE | re.DOTALL,
)
_FENCE_BLOCK = re.compile(
    r"```(?:jsonc?|ya?ml|hash|text)?\s*(?P<body>.*?)```",
    re.IGNORECASE | re.DOTALL,
)
_JSON_OBJECT = re.compile(r"\{[^{}]*\}", re.DOTALL)
_NAMED_MAPPING_LINE = re.compile(
    r"^\s*(?:[-*]\s+)?(?P<name>[^:\[\]#]+?)\s*[:=]\s*[`'\"]?(?P<value>[^\s`'\",;]+)",
    re.MULTILINE,
)

_RELEASE_BODY_CACHE: dict[tuple[str, str], str] = {}
_CACHE_LOCK = threading.Lock()
_DISK_LOCK = threading.Lock()
_REFRESH_LOCK = threading.Lock()
_PREFETCH_STARTED = False
_PREFETCH_DONE = threading.Event()
_PREFETCH_DONE.set()

GetFunc = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class HashSourceComparison:
    """三源哈希对比结果。"""

    passed: bool
    actual: str = ""
    interface_hash: str = ""
    github_hash: str = ""
    mismatched_sources: tuple[str, ...] = ()


def normalize_hash(value: Any) -> str:
    """去掉空白并统一为小写，便于对比。"""
    return str(value or "").strip().lower()


def compare_resource_hash_sources(
    *,
    actual_hash: str,
    interface_hash: str = "",
    github_hash: str = "",
) -> HashSourceComparison:
    """对比实际哈希与可选的 interface / GitHub 期望值。

    缺省来源不参与检测。任一已参与来源与实际值不一致则失败。
    """
    actual = normalize_hash(actual_hash)
    interface_value = normalize_hash(interface_hash)
    github_value = normalize_hash(github_hash)
    mismatched: list[str] = []

    if interface_value and interface_value != actual:
        mismatched.append("interface")
    if github_value and github_value != actual:
        mismatched.append("github")

    return HashSourceComparison(
        passed=not mismatched,
        actual=actual,
        interface_hash=interface_value,
        github_hash=github_value,
        mismatched_sources=tuple(mismatched),
    )


def parse_release_body_hashes(body: str | None) -> dict[str, str]:
    """从 GitHub release body 中按关键字解析资源哈希表。

    支持：
    - HTML 注释 ``<!-- mfw-resource-hash ... -->``
    - 代码块中的 JSON / ``hash: value`` 行
    - 正文行 ``hash:`` / ``hash[资源名]:`` / ``resource-hash:`` / ``哈希:``
    - JSON ``{"hash": "..."}`` 或 ``{"hash": {"资源名": "..."}}``

    未命名哈希使用 ``*`` 作为键。解析不到关键字时返回空 dict。
    """
    text = str(body or "")
    if not text.strip():
        return {}

    parsed: dict[str, str] = {}
    for match in _COMMENT_BLOCK.finditer(text):
        _merge_hash_map(parsed, _parse_hash_block(match.group("body")))
    for match in _FENCE_BLOCK.finditer(text):
        _merge_hash_map(parsed, _parse_hash_block(match.group("body")))
    _merge_hash_map(parsed, _parse_json_fragments(text))
    _merge_hash_map(parsed, _parse_hash_lines(text))
    return parsed


def pick_github_hash(
    hashes: Mapping[str, str] | None,
    resource_name: str = "",
    resource_label: str = "",
) -> str:
    """按当前资源名/标签选取 GitHub 哈希；没有匹配项时回退到未命名哈希。"""
    if not hashes:
        return ""
    normalized = {
        str(key).strip(): normalize_hash(value)
        for key, value in hashes.items()
        if str(value or "").strip()
    }
    if not normalized:
        return ""

    candidates = [
        str(resource_name or "").strip(),
        _strip_i18n_prefix(resource_label),
        str(resource_label or "").strip(),
    ]
    lowered = {key.lower(): value for key, value in normalized.items()}
    for candidate in candidates:
        if not candidate:
            continue
        if candidate in normalized:
            return normalized[candidate]
        value = lowered.get(candidate.lower())
        if value:
            return value

    return normalized.get(DEFAULT_HASH_KEY, "") or normalized.get("", "")


def fetch_github_resource_hashes(
    github_url: str,
    version: str,
    *,
    request_get: GetFunc | None = None,
) -> dict[str, str]:
    """拉取当前版本 GitHub Release body，并解析其中的资源哈希。

    github 未填写、版本为空、请求失败或未解析到关键字时返回空 dict（视为跳过）。
    """
    body = fetch_github_release_body(
        github_url,
        version,
        request_get=request_get,
    )
    return _hashes_from_release_body(body)


def get_github_resource_hashes_for_run(
    github_url: str,
    version: str,
    *,
    wait_timeout: float = GITHUB_HASH_PREFETCH_WAIT_TIMEOUT,
) -> dict[str, str]:
    """任务运行时读取已预取的 GitHub 哈希，不发起网络请求。

    若启动预取尚未完成则等待；超时或缓存缺失时跳过 GitHub 对比。
    """
    wait_github_hash_prefetch(wait_timeout)
    body = get_cached_github_release_body(github_url, version)
    if body is None:
        return {}
    return _hashes_from_release_body(body)


def fetch_github_release_body(
    github_url: str,
    version: str,
    *,
    request_get: GetFunc | None = None,
    persist: bool = False,
) -> str:
    """获取指定版本 GitHub Release 的 body 原文。失败或超过 2 秒时返回空字符串。"""
    keys = _release_cache_keys(github_url, version)
    if not keys:
        if str(github_url or "").strip() and not str(version or "").strip():
            logger.debug("未提供资源版本，跳过 GitHub 哈希校验")
        return ""

    cached = _lookup_memory_release_body(keys)
    if cached is not None:
        return cached

    getter = request_get or requests.get
    headers = _github_request_headers()
    proxies = _proxy_data()
    verify = not os.path.exists("NO_SSL")
    body = ""
    succeeded = False
    owner, name = keys[0][0].split("/", 1)
    tags = [tag for _, tag in keys]
    deadline = time.monotonic() + GITHUB_HASH_FETCH_TIMEOUT
    for tag in tags:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            logger.debug("GitHub 哈希校验超过 %.1f 秒，跳过", GITHUB_HASH_FETCH_TIMEOUT)
            break
        api_url = (
            f"https://api.github.com/repos/{owner}/{name}/releases/tags/"
            f"{quote(tag, safe='')}"
        )
        try:
            response = getter(
                api_url,
                headers=headers,
                timeout=remaining,
                verify=verify,
                proxies=proxies,
            )
        except Exception as exc:
            logger.warning("获取 GitHub release 失败: %s (%s)", api_url, exc)
            continue
        if not _is_success_status(response):
            status = getattr(response, "status_code", None)
            logger.debug(
                "GitHub release 请求未成功: %s status=%s",
                api_url,
                status,
            )
            continue
        payload = _response_json(response)
        if not isinstance(payload, dict):
            continue
        message = payload.get("message")
        if isinstance(message, str) and message:
            logger.debug("GitHub API 返回消息: %s", message)
            continue
        raw_body = payload.get("body", "")
        body = str(raw_body) if raw_body is not None else ""
        succeeded = True
        break

    store_github_release_body(github_url, version, body, persist=persist and succeeded)
    return body


def github_versions_match(left: str, right: str) -> bool:
    """判断两个版本号是否指向同一 GitHub tag（兼容有无 v 前缀）。"""
    left_tags = set(github_tag_candidates(left))
    right_tags = set(github_tag_candidates(right))
    return bool(left_tags and right_tags and left_tags & right_tags)


def store_github_release_body(
    github_url: str,
    version: str,
    body: str | None,
    *,
    persist: bool = True,
) -> None:
    """将指定版本的 GitHub release body 写入内存，可选持久化到磁盘。"""
    keys = _release_cache_keys(github_url, version)
    if not keys:
        return
    text = str(body) if body is not None else ""
    with _CACHE_LOCK:
        for key in keys:
            _RELEASE_BODY_CACHE[key] = text
    if persist:
        _persist_release_body(keys, text)


def get_cached_github_release_body(github_url: str, version: str) -> str | None:
    """读取当前版本 release body 缓存（内存优先，其次磁盘）。未命中返回 None。"""
    keys = _release_cache_keys(github_url, version)
    if not keys:
        return None
    cached = _lookup_memory_release_body(keys)
    if cached is not None:
        return cached
    loaded = _load_persisted_release_body(keys)
    if loaded is None:
        return None
    with _CACHE_LOCK:
        for key in keys:
            _RELEASE_BODY_CACHE[key] = loaded
    return loaded


def refresh_github_hash_cache_for_current_version(
    github_url: str,
    current_version: str,
    *,
    source: str = "",
    latest_version: str = "",
    latest_body: str | None = None,
    request_get: GetFunc | None = None,
) -> str:
    """在最新版检查之后，准备当前安装版本的 GitHub release body。

    若本次最新版检查走 GitHub 且 latest 与当前版本相同，则直接复用该次 body；
    否则先读缓存，没有再请求 ``releases/tags/{current_version}``。
    """
    with _REFRESH_LOCK:
        return _refresh_github_hash_cache_locked(
            github_url,
            current_version,
            source=source,
            latest_version=latest_version,
            latest_body=latest_body,
            request_get=request_get,
        )


def begin_github_hash_prefetch() -> None:
    """标记启动预取开始；重复调用不会重置已完成状态。"""
    global _PREFETCH_STARTED
    with _CACHE_LOCK:
        if _PREFETCH_STARTED:
            return
        _PREFETCH_STARTED = True
        _PREFETCH_DONE.clear()


def finish_github_hash_prefetch() -> None:
    """标记启动预取结束，唤醒等待中的任务校验。"""
    _PREFETCH_DONE.set()


def wait_github_hash_prefetch(
    timeout: float | None = GITHUB_HASH_PREFETCH_WAIT_TIMEOUT,
) -> bool:
    """等待启动预取完成。尚未开始则立即返回。"""
    if not _PREFETCH_STARTED or _PREFETCH_DONE.is_set():
        return True
    return _PREFETCH_DONE.wait(timeout=timeout)


def parse_github_owner_repo(url: str) -> tuple[str, str] | None:
    """从 GitHub 仓库地址解析 owner/repo。"""
    text = str(url or "").strip()
    if not text:
        return None
    if text.startswith("git@"):
        _, _, rest = text.partition(":")
        parts = [part for part in rest.strip().strip("/").split("/") if part]
        if len(parts) < 2:
            return None
        return parts[0], _strip_git_suffix(parts[1])

    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = (parsed.hostname or "").lower()
    if host not in {"github.com", "www.github.com"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    return parts[0], _strip_git_suffix(parts[1])


def github_tag_candidates(version: str) -> list[str]:
    """生成 GitHub tag 候选（保留原值，并补/去 v 前缀）。"""
    text = str(version or "").strip()
    if not text:
        return []
    candidates = [text]
    if text[:1] in {"v", "V"}:
        stripped = text[1:].strip()
        if stripped:
            candidates.append(stripped)
    else:
        candidates.append(f"v{text}")
    unique: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def clear_github_release_body_cache() -> None:
    """测试辅助：清空内存缓存并重置预取状态。"""
    global _PREFETCH_STARTED
    with _CACHE_LOCK:
        _RELEASE_BODY_CACHE.clear()
        _PREFETCH_STARTED = False
        _PREFETCH_DONE.set()


def _hashes_from_release_body(body: str | None) -> dict[str, str]:
    if not body:
        return {}
    parsed = parse_release_body_hashes(body)
    if parsed:
        logger.debug(
            "从 GitHub release 解析到 %s 个资源哈希: %s",
            len(parsed),
            sorted(parsed.keys()),
        )
    else:
        logger.debug("GitHub release body 未解析到资源哈希关键字，跳过 GitHub 对比")
    return parsed


def _refresh_github_hash_cache_locked(
    github_url: str,
    current_version: str,
    *,
    source: str = "",
    latest_version: str = "",
    latest_body: str | None = None,
    request_get: GetFunc | None = None,
) -> str:
    if not str(github_url or "").strip() or not str(current_version or "").strip():
        return ""

    can_reuse = (
        str(source or "").strip().lower() == "github"
        and github_versions_match(latest_version, current_version)
        and latest_body is not None
    )
    if can_reuse:
        logger.info(
            "GitHub 最新版与当前版本相同，复用已获取的 release body"
        )
        store_github_release_body(github_url, current_version, latest_body, persist=True)
        return str(latest_body)

    cached = get_cached_github_release_body(github_url, current_version)
    if cached is not None:
        logger.debug("当前版本 GitHub release body 已有缓存，跳过请求")
        return cached

    logger.info("拉取当前版本 GitHub release body 用于资源哈希校验")
    return fetch_github_release_body(
        github_url,
        current_version,
        request_get=request_get,
        persist=True,
    )


def _release_cache_keys(github_url: str, version: str) -> list[tuple[str, str]]:
    repo = parse_github_owner_repo(github_url)
    if repo is None:
        return []
    tags = github_tag_candidates(version)
    if not tags:
        return []
    owner, name = repo
    repo_id = f"{owner}/{name}"
    return [(repo_id, tag) for tag in tags]


def _lookup_memory_release_body(keys: list[tuple[str, str]]) -> str | None:
    with _CACHE_LOCK:
        for key in keys:
            if key in _RELEASE_BODY_CACHE:
                return _RELEASE_BODY_CACHE[key]
    return None


def _disk_cache_path() -> Path:
    return Path("config") / _DISK_CACHE_FILENAME


def _persist_release_body(keys: list[tuple[str, str]], body: str) -> None:
    path = _disk_cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with _DISK_LOCK:
            data: dict[str, Any] = {}
            if path.is_file():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    loaded = {}
                if isinstance(loaded, dict):
                    data = loaded
            for owner_repo, tag in keys:
                data[f"{owner_repo}@{tag}"] = body
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(path)
    except Exception as exc:
        logger.debug("写入 GitHub release body 磁盘缓存失败: %s", exc)


def _load_persisted_release_body(keys: list[tuple[str, str]]) -> str | None:
    path = _disk_cache_path()
    if not path.is_file():
        return None
    try:
        with _DISK_LOCK:
            data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    for owner_repo, tag in keys:
        value = data.get(f"{owner_repo}@{tag}")
        if isinstance(value, str):
            return value
    return None


def _parse_hash_block(text: str | None) -> dict[str, str]:
    raw = str(text or "").strip()
    if not raw:
        return {}
    if raw[:1] in {":", "="}:
        raw = raw[1:].strip()
    parsed = _parse_json_value(raw)
    if parsed:
        return parsed
    stripped = raw.strip().strip("`'\"" )
    if _is_hash_value(stripped):
        return {DEFAULT_HASH_KEY: normalize_hash(stripped)}
    parsed_lines = _parse_hash_lines(raw)
    _merge_hash_map(parsed_lines, _parse_named_mapping_lines(raw))
    return parsed_lines


def _parse_hash_lines(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for match in _HASH_LINE.finditer(text):
        name = str(match.group("name") or "").strip() or DEFAULT_HASH_KEY
        value = normalize_hash(match.group("value"))
        if _is_hash_value(value):
            result[name] = value
    return result


def _parse_named_mapping_lines(text: str) -> dict[str, str]:
    """解析哈希块内的 ``资源名: 哈希值`` 行。"""
    result: dict[str, str] = {}
    for match in _NAMED_MAPPING_LINE.finditer(text):
        name = str(match.group("name") or "").strip()
        value = normalize_hash(match.group("value"))
        if not name or _is_hash_keyword(name):
            continue
        if _is_hash_value(value):
            result[name] = value
    return result


def _parse_json_fragments(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for match in _JSON_OBJECT.finditer(text):
        _merge_hash_map(result, _parse_json_value(match.group(0)))
    return result


def _parse_json_value(text: str) -> dict[str, str]:
    try:
        data = json.loads(text)
    except Exception:
        return {}
    return _extract_hash_map(data)


def _extract_hash_map(data: Any) -> dict[str, str]:
    if isinstance(data, str):
        value = normalize_hash(data)
        return {DEFAULT_HASH_KEY: value} if value else {}
    if not isinstance(data, dict):
        return {}

    result: dict[str, str] = {}
    for key, value in data.items():
        key_text = str(key or "").strip()
        if _is_hash_keyword(key_text):
            if isinstance(value, str):
                hashed = normalize_hash(value)
                if _is_hash_value(hashed):
                    result[DEFAULT_HASH_KEY] = hashed
            elif isinstance(value, dict):
                for name, nested in value.items():
                    hashed = normalize_hash(nested)
                    if _is_hash_value(hashed):
                        result[str(name).strip() or DEFAULT_HASH_KEY] = hashed
            continue
        hashed = normalize_hash(value)
        if _is_hash_value(hashed):
            result[key_text or DEFAULT_HASH_KEY] = hashed
    return result


def _is_hash_keyword(text: str) -> bool:
    return re.fullmatch(_HASH_KEYWORD, str(text or "").strip(), re.IGNORECASE) is not None


def _is_hash_value(value: str) -> bool:
    return bool(value) and _HEX_HASH.fullmatch(value) is not None


def _merge_hash_map(target: dict[str, str], incoming: Mapping[str, str]) -> None:
    for key, value in incoming.items():
        hashed = normalize_hash(value)
        if _is_hash_value(hashed):
            target[str(key).strip() or DEFAULT_HASH_KEY] = hashed


def _strip_i18n_prefix(label: str) -> str:
    text = str(label or "").strip()
    if text.startswith("$"):
        return text[1:].strip()
    return text


def _strip_git_suffix(name: str) -> str:
    text = str(name or "").strip()
    if text.lower().endswith(".git"):
        return text[:-4]
    return text


def _github_request_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MFW-PyQt6",
    }
    token = _github_token()
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def _github_token() -> str:
    try:
        from app.common.config import cfg
        from app.utils.crypto import crypto_manager

        stored = cfg.get(cfg.github_api_key) or ""
        if not stored:
            return ""
        return crypto_manager.decrypt_text(
            stored,
            fallback_to_plaintext=True,
        ).strip()
    except ImportError:
        return ""
    except Exception as exc:
        logger.warning("读取 GitHub API Key 失败，将按未配置处理: %s", exc)
        return ""


def _proxy_data() -> dict[str, str] | None:
    try:
        from app.common.config import cfg

        proxy_value = cfg.get(cfg.http_proxy)
        scheme = {0: "http", 1: "socks5"}.get(cfg.get(cfg.proxy))
    except ImportError:
        return None
    except Exception:
        return None
    if not proxy_value or not scheme:
        return None
    return {key: f"{scheme}://{proxy_value}" for key in ("http", "https")}


def _is_success_status(response: Any) -> bool:
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        return 200 <= status < 300
    return True


def _response_json(response: Any) -> Any:
    json_func = getattr(response, "json", None)
    if callable(json_func):
        try:
            return json_func()
        except Exception:
            return None
    return None
