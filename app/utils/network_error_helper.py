#   This file is part of MFW-ChainFlow Assistant.
#
#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""将外部网络请求异常归一化为用户可理解的提示文案。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Literal, Optional

import requests
from PySide6.QtCore import QCoreApplication

TranslateFn = Callable[[str], str]

# pylupdate 将本模块 tr() 源串收集到 .ts 的空 <name /> context，须用相同 context 查找。
_NETWORK_ERROR_I18N_CONTEXT = ""


def network_error_tr(text: str) -> str:
    """翻译网络/更新/通知类 InfoBar 文案（与 i18n .ts 中空 context 一致）。"""
    return QCoreApplication.translate(_NETWORK_ERROR_I18N_CONTEXT, text)

UpdateSource = Literal["github", "mirror"]
NoticeSource = Literal[
    "dingtalk", "lark", "smtp", "wxpusher", "qywx", "gotify", "webhook"
]


class NetworkErrorCategory(StrEnum):
    RATE_LIMIT = "rate_limit"
    SSL_ERROR = "ssl_error"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    DNS_ERROR = "dns_error"
    HTTP_4XX = "http_4xx"
    HTTP_5XX = "http_5xx"
    RESPONSE_ERROR = "response_error"
    CONFIG_ERROR = "config_error"
    MIRROR_KEY_EXPIRED = "mirror_key_expired"
    MIRROR_KEY_INVALID = "mirror_key_invalid"
    MIRROR_QUOTA_EXHAUSTED = "mirror_quota_exhausted"
    MIRROR_KEY_MISMATCHED = "mirror_key_mismatched"
    MIRROR_RESOURCE_NOT_FOUND = "mirror_resource_not_found"
    MIRROR_INVALID_OS = "mirror_invalid_os"
    MIRROR_INVALID_ARCH = "mirror_invalid_arch"
    MIRROR_INVALID_CHANNEL = "mirror_invalid_channel"
    MIRROR_INVALID_PARAMS = "mirror_invalid_params"
    UNKNOWN = "unknown_network_error"


@dataclass(frozen=True)
class NetworkErrorInfo:
    category: NetworkErrorCategory
    level: Literal["warning", "error", "info"]
    user_message: str
    tech_tag: str
    log_message: str
    status: Literal["failed", "failed_info"] = "failed"


MIRROR_CODE_TO_CATEGORY: dict[int, NetworkErrorCategory] = {
    1001: NetworkErrorCategory.MIRROR_INVALID_PARAMS,
    7001: NetworkErrorCategory.MIRROR_KEY_EXPIRED,
    7002: NetworkErrorCategory.MIRROR_KEY_INVALID,
    7003: NetworkErrorCategory.MIRROR_QUOTA_EXHAUSTED,
    7004: NetworkErrorCategory.MIRROR_KEY_MISMATCHED,
    8001: NetworkErrorCategory.MIRROR_RESOURCE_NOT_FOUND,
    8002: NetworkErrorCategory.MIRROR_INVALID_OS,
    8003: NetworkErrorCategory.MIRROR_INVALID_ARCH,
    8004: NetworkErrorCategory.MIRROR_INVALID_CHANNEL,
}

MIRROR_FALLBACK_CODES = frozenset({7001, 7002, 7003, 7004})

NOTICE_CHANNEL_LABELS: dict[str, str] = {
    "dingtalk": "DingTalk",
    "lark": "Lark",
    "smtp": "SMTP",
    "wxpusher": "WxPusher",
    "qywx": "WeCom",
    "gotify": "Gotify",
    "webhook": "Webhook",
}

SEND_FUNC_TO_CHANNEL: dict[str, str] = {
    "dingtalk_send": "dingtalk",
    "lark_send": "lark",
    "SMTP_send": "smtp",
    "WxPusher_send": "wxpusher",
    "QYWX_send": "qywx",
    "gotify_send": "gotify",
    "webhook_send": "webhook",
}

_notice_error_context: dict[str, NetworkErrorInfo] = {}


def _default_tr(text: str) -> str:
    return network_error_tr(text)


def classify_request_exception(
    exc: BaseException,
    *,
    response: Optional[requests.Response] = None,
) -> NetworkErrorCategory:
    if isinstance(exc, requests.exceptions.SSLError):
        return NetworkErrorCategory.SSL_ERROR
    if isinstance(exc, requests.exceptions.Timeout):
        return NetworkErrorCategory.TIMEOUT
    if isinstance(exc, requests.exceptions.ConnectionError):
        exc_text = str(exc).lower()
        if "name or service not known" in exc_text or "getaddrinfo" in exc_text:
            return NetworkErrorCategory.DNS_ERROR
        return NetworkErrorCategory.CONNECTION_ERROR
    if isinstance(exc, requests.exceptions.HTTPError):
        status = exc.response.status_code if exc.response is not None else None
        if status == 403:
            return NetworkErrorCategory.RATE_LIMIT
        if status is not None and 400 <= status < 500:
            return NetworkErrorCategory.HTTP_4XX
        if status is not None and 500 <= status < 600:
            return NetworkErrorCategory.HTTP_5XX
        return NetworkErrorCategory.HTTP_4XX
    if response is not None:
        status = response.status_code
        if status == 403:
            return NetworkErrorCategory.RATE_LIMIT
        if 400 <= status < 500:
            return NetworkErrorCategory.HTTP_4XX
        if 500 <= status < 600:
            return NetworkErrorCategory.HTTP_5XX
    if isinstance(exc, (json.JSONDecodeError, ValueError, KeyError)):
        return NetworkErrorCategory.RESPONSE_ERROR
    return NetworkErrorCategory.UNKNOWN


def _tech_tag_for_category(category: NetworkErrorCategory) -> str:
    mapping = {
        NetworkErrorCategory.RATE_LIMIT: "403",
        NetworkErrorCategory.SSL_ERROR: "SSL",
        NetworkErrorCategory.TIMEOUT: "Timeout",
        NetworkErrorCategory.CONNECTION_ERROR: "Connection",
        NetworkErrorCategory.DNS_ERROR: "DNS",
        NetworkErrorCategory.HTTP_4XX: "HTTP 4xx",
        NetworkErrorCategory.HTTP_5XX: "HTTP 5xx",
        NetworkErrorCategory.RESPONSE_ERROR: "Response",
        NetworkErrorCategory.CONFIG_ERROR: "Config",
        NetworkErrorCategory.MIRROR_KEY_EXPIRED: "KEY_EXPIRED",
        NetworkErrorCategory.MIRROR_KEY_INVALID: "KEY_INVALID",
        NetworkErrorCategory.MIRROR_QUOTA_EXHAUSTED: "QUOTA",
        NetworkErrorCategory.MIRROR_KEY_MISMATCHED: "KEY_MISMATCHED",
        NetworkErrorCategory.MIRROR_RESOURCE_NOT_FOUND: "NOT_FOUND",
        NetworkErrorCategory.MIRROR_INVALID_OS: "INVALID_OS",
        NetworkErrorCategory.MIRROR_INVALID_ARCH: "INVALID_ARCH",
        NetworkErrorCategory.MIRROR_INVALID_CHANNEL: "INVALID_CHANNEL",
        NetworkErrorCategory.MIRROR_INVALID_PARAMS: "INVALID_PARAMS",
        NetworkErrorCategory.UNKNOWN: "Network",
    }
    return mapping.get(category, "Network")


def _append_tag(message: str, tech_tag: str) -> str:
    tag = tech_tag.strip()
    if not tag:
        return message
    return f"{message} ({tag})"


def _github_message(
    category: NetworkErrorCategory,
    tr: TranslateFn,
    *,
    action: str = "update check",
) -> str:
    if category == NetworkErrorCategory.RATE_LIMIT:
        return tr(
            "GitHub API rate limit exceeded. Please try again later or configure a GitHub Token."
        )
    if category == NetworkErrorCategory.SSL_ERROR:
        return tr(
            "GitHub SSL connection failed. Check system time, proxy, or certificate settings."
        )
    if category == NetworkErrorCategory.TIMEOUT:
        return tr(
            "GitHub request timed out. Check your network or proxy and try again."
        )
    if category == NetworkErrorCategory.DNS_ERROR:
        return tr(
            "GitHub domain could not be resolved. Check DNS or network settings."
        )
    if category == NetworkErrorCategory.CONNECTION_ERROR:
        return tr(
            "GitHub connection failed. Check your network and try again."
        )
    if category == NetworkErrorCategory.HTTP_4XX:
        return tr("GitHub request was rejected. Check the project URL or permissions.")
    if category == NetworkErrorCategory.HTTP_5XX:
        return tr("GitHub service is temporarily unavailable. Please try again later.")
    if category == NetworkErrorCategory.RESPONSE_ERROR:
        return tr("GitHub returned an invalid response. Please try again later.")
    return tr(f"GitHub {action} failed. Please try again later.")


def _mirror_message(
    category: NetworkErrorCategory,
    tr: TranslateFn,
    *,
    fallback_to_github: bool,
) -> str:
    suffix = (
        tr(" Will try GitHub source for update check.")
        if fallback_to_github
        else ""
    )

    if category == NetworkErrorCategory.SSL_ERROR:
        base = tr(
            "MirrorChyan SSL connection failed. Check system time, proxy, or certificate settings."
        )
        return base + suffix
    if category == NetworkErrorCategory.TIMEOUT:
        base = tr("MirrorChyan request timed out. Check your network or proxy.")
        return base + suffix
    if category == NetworkErrorCategory.DNS_ERROR:
        base = tr("MirrorChyan domain could not be resolved. Check DNS or network settings.")
        return base + suffix
    if category == NetworkErrorCategory.CONNECTION_ERROR:
        base = tr("MirrorChyan connection failed. Check your network and try again.")
        return base + suffix
    if category == NetworkErrorCategory.HTTP_4XX:
        base = tr("MirrorChyan request was rejected. Check CDK or resource settings.")
        return base + suffix
    if category == NetworkErrorCategory.HTTP_5XX:
        base = tr("MirrorChyan service is temporarily unavailable.")
        return base + suffix
    if category == NetworkErrorCategory.MIRROR_KEY_EXPIRED:
        return tr("MirrorChyan CDK has expired.") + suffix
    if category == NetworkErrorCategory.MIRROR_KEY_INVALID:
        return tr("MirrorChyan CDK is invalid. Check your CDK in settings.") + suffix
    if category == NetworkErrorCategory.MIRROR_QUOTA_EXHAUSTED:
        return tr("MirrorChyan resource quota exhausted.") + suffix
    if category == NetworkErrorCategory.MIRROR_KEY_MISMATCHED:
        return tr("MirrorChyan CDK does not match this resource.") + suffix
    if category == NetworkErrorCategory.MIRROR_RESOURCE_NOT_FOUND:
        return tr("MirrorChyan resource was not found. Check the resource ID.") + suffix
    if category == NetworkErrorCategory.MIRROR_INVALID_OS:
        return tr("MirrorChyan OS parameter is invalid for this resource.") + suffix
    if category == NetworkErrorCategory.MIRROR_INVALID_ARCH:
        return tr("MirrorChyan architecture parameter is invalid for this resource.") + suffix
    if category == NetworkErrorCategory.MIRROR_INVALID_CHANNEL:
        return tr("MirrorChyan channel parameter is invalid for this resource.") + suffix
    if category == NetworkErrorCategory.MIRROR_INVALID_PARAMS:
        return tr("MirrorChyan request parameters are invalid.") + suffix
    return tr("MirrorChyan update check failed.") + suffix


def _notice_message(
    channel: str,
    category: NetworkErrorCategory,
    tr: TranslateFn,
) -> str:
    label = NOTICE_CHANNEL_LABELS.get(channel, channel)
    if category == NetworkErrorCategory.SSL_ERROR:
        return tr(
            "{channel} send failed: SSL error. Check certificate or proxy settings."
        ).format(channel=label)
    if category == NetworkErrorCategory.TIMEOUT:
        return tr("{channel} send failed: request timed out. Check your network.").format(
            channel=label
        )
    if category == NetworkErrorCategory.DNS_ERROR:
        return tr(
            "{channel} send failed: domain could not be resolved. Check DNS settings."
        ).format(channel=label)
    if category == NetworkErrorCategory.CONNECTION_ERROR:
        return tr(
            "{channel} send failed: connection error. Check server address and network."
        ).format(channel=label)
    if category == NetworkErrorCategory.HTTP_4XX:
        return tr(
            "{channel} send failed: request rejected. Check URL, token, or webhook key."
        ).format(channel=label)
    if category == NetworkErrorCategory.HTTP_5XX:
        return tr(
            "{channel} send failed: remote service error. Try again later."
        ).format(channel=label)
    if category == NetworkErrorCategory.RESPONSE_ERROR:
        return tr(
            "{channel} send failed: invalid response from server. Check configuration."
        ).format(channel=label)
    return tr("{channel} send failed due to a network error.").format(channel=label)


def normalize_network_error(
    exc: BaseException,
    *,
    source: UpdateSource | NoticeSource | str,
    tr: TranslateFn | None = None,
    action: str = "update check",
    response: Optional[requests.Response] = None,
    fallback_to_github: bool = False,
    context_label: str = "",
) -> NetworkErrorInfo:
    translate = tr or _default_tr
    category = classify_request_exception(exc, response=response)

    if source == "github":
        user_message = _github_message(category, translate, action=action)
        level: Literal["warning", "error", "info"] = "error"
        status: Literal["failed", "failed_info"] = "failed"
    elif source == "mirror":
        user_message = _mirror_message(
            category, translate, fallback_to_github=fallback_to_github
        )
        level = "warning"
        status = "failed_info"
    else:
        user_message = _notice_message(str(source), category, translate)
        level = "warning"
        status = "failed"

    tech_tag = _tech_tag_for_category(category)
    user_message = _append_tag(user_message, tech_tag)
    label = context_label or str(source)
    log_message = f"[{label}] {category.value}: {type(exc).__name__}: {exc}"

    return NetworkErrorInfo(
        category=category,
        level=level,
        user_message=user_message,
        tech_tag=tech_tag,
        log_message=log_message,
        status=status,
    )


def normalize_mirror_business_error(
    code: int,
    *,
    tr: TranslateFn | None = None,
    fallback_to_github: bool = True,
) -> NetworkErrorInfo:
    translate = tr or _default_tr
    category = MIRROR_CODE_TO_CATEGORY.get(
        code, NetworkErrorCategory.UNKNOWN
    )
    user_message = _mirror_message(
        category, translate, fallback_to_github=fallback_to_github
    )
    tech_tag = _tech_tag_for_category(category)
    user_message = _append_tag(user_message, tech_tag)
    level: Literal["warning", "error", "info"] = "warning"
    status: Literal["failed", "failed_info"] = "failed_info"
    return NetworkErrorInfo(
        category=category,
        level=level,
        user_message=user_message,
        tech_tag=tech_tag,
        log_message=f"[mirror] business code={code} category={category.value}",
        status=status,
    )


def normalize_github_http_error(
    error: requests.exceptions.HTTPError,
    *,
    tr: TranslateFn | None = None,
) -> NetworkErrorInfo:
    translate = tr or _default_tr
    if error.response is not None and error.response.status_code == 403:
        user_message = _append_tag(
            translate(
                "GitHub API rate limit exceeded. Please try again later or configure a GitHub Token."
            ),
            "403",
        )
        return NetworkErrorInfo(
            category=NetworkErrorCategory.RATE_LIMIT,
            level="error",
            user_message=user_message,
            tech_tag="403",
            log_message=f"[github] rate limit: {error}",
            status="failed",
        )

    category = classify_request_exception(error, response=error.response)
    user_message = _append_tag(_github_message(category, translate), _tech_tag_for_category(category))
    return NetworkErrorInfo(
        category=category,
        level="error",
        user_message=user_message,
        tech_tag=_tech_tag_for_category(category),
        log_message=f"[github] HTTP error: {error}",
        status="failed",
    )


def _download_message(
    source: UpdateSource,
    category: NetworkErrorCategory,
    tr: TranslateFn,
) -> str:
    if source == "github":
        if category == NetworkErrorCategory.TIMEOUT:
            return tr("GitHub download timed out. Check your network or proxy.")
        if category == NetworkErrorCategory.SSL_ERROR:
            return tr(
                "GitHub download SSL failed. Check certificate or proxy settings."
            )
        if category == NetworkErrorCategory.CONNECTION_ERROR:
            return tr("GitHub download connection failed. Check your network.")
        return tr("GitHub download failed. Please try again.")
    if category == NetworkErrorCategory.TIMEOUT:
        return tr("MirrorChyan download timed out. Check your network or proxy.")
    if category == NetworkErrorCategory.SSL_ERROR:
        return tr(
            "MirrorChyan download SSL failed. Check certificate or proxy settings."
        )
    if category == NetworkErrorCategory.CONNECTION_ERROR:
        return tr("MirrorChyan download connection failed. Check your network.")
    return tr("MirrorChyan download failed. Please try again.")


def normalize_download_error(
    exc: BaseException,
    *,
    source: UpdateSource,
    tr: TranslateFn | None = None,
) -> NetworkErrorInfo:
    translate = tr or _default_tr
    category = classify_request_exception(exc)
    base = _download_message(source, category, translate)
    tech_tag = _tech_tag_for_category(category)
    return NetworkErrorInfo(
        category=category,
        level="error",
        user_message=_append_tag(base, tech_tag),
        tech_tag=tech_tag,
        log_message=f"[{source}] download error: {type(exc).__name__}: {exc}",
        status="failed",
    )


def set_notice_error_context(channel: str, info: NetworkErrorInfo) -> None:
    _notice_error_context[channel] = info


def pop_notice_error_context(channel: str) -> NetworkErrorInfo | None:
    return _notice_error_context.pop(channel, None)


def channel_from_send_func(send_func_name: str) -> str:
    return SEND_FUNC_TO_CHANNEL.get(send_func_name, send_func_name)


def format_notice_result_message(
    send_func_name: str,
    error_code: int,
    tr: TranslateFn | None = None,
) -> str:
    translate = tr or _default_tr
    channel = channel_from_send_func(send_func_name)
    label = NOTICE_CHANNEL_LABELS.get(channel, channel)

    if error_code == 0:
        return translate("{channel} sent successfully.").format(channel=label)
    if error_code == 1:
        return translate("{channel} notifications are disabled.").format(channel=label)
    if error_code == 2:
        return translate("{channel}: required settings are empty.").format(channel=label)
    if error_code == 3:
        return translate("{channel}: invalid URL or parameter format.").format(channel=label)
    if error_code == 4:
        cached = pop_notice_error_context(channel)
        if cached is not None:
            return cached.user_message
        return translate("{channel} send failed due to a network error. (Network)").format(
            channel=label
        )
    if error_code == 5:
        return translate(
            "{channel} send failed: server returned an error. Check webhook or token."
        ).format(channel=label)
    if error_code == 7:
        return translate("{channel}: SMTP port must be a valid number. (Config)").format(
            channel=label
        )
    if error_code == 8:
        cached = pop_notice_error_context(channel)
        if cached is not None:
            return cached.user_message
        return translate(
            "{channel} SMTP connection failed. Check server address, port, and credentials. (Connection)"
        ).format(channel=label)
    return translate("{channel} send failed with an unknown error. (Unknown)").format(
        channel=label
    )
