"""资源完整性哈希：对比 MaaResource 接口、interface.json 与 GitHub Release。

三源规则：
- 接口（MaaResourceGetHash）：始终作为实际值参与对比
- interface：仅当 resource.hash 有值时检测，否则视为通过
- GitHub：仅当填写了 github/url，并且成功从当前版本 release body
  解析到关键字后才对比；拉取或解析失败视为通过
- 只有已参与对比的哈希不一致时才判定失败
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.parse import quote, urlparse

import requests

from app.utils.logger import logger

DEFAULT_HASH_KEY = "*"

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


def fetch_github_release_body(
    github_url: str,
    version: str,
    *,
    request_get: GetFunc | None = None,
) -> str:
    """获取指定版本 GitHub Release 的 body 原文。失败时返回空字符串。"""
    repo = parse_github_owner_repo(github_url)
    if repo is None:
        return ""
    owner, name = repo
    tags = github_tag_candidates(version)
    if not tags:
        logger.debug("未提供资源版本，跳过 GitHub 哈希校验")
        return ""

    cache_key = (f"{owner}/{name}", tags[0])
    with _CACHE_LOCK:
        cached = _RELEASE_BODY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    getter = request_get or requests.get
    headers = _github_request_headers()
    proxies = _proxy_data()
    verify = not os.path.exists("NO_SSL")
    body = ""
    for tag in tags:
        api_url = (
            f"https://api.github.com/repos/{owner}/{name}/releases/tags/"
            f"{quote(tag, safe='')}"
        )
        try:
            response = getter(
                api_url,
                headers=headers,
                timeout=10,
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
        break

    with _CACHE_LOCK:
        _RELEASE_BODY_CACHE[cache_key] = body
    return body


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
    """测试辅助：清空 release body 缓存。"""
    with _CACHE_LOCK:
        _RELEASE_BODY_CACHE.clear()


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
