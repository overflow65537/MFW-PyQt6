"""MaaFramework 版本解析与能力判断测试。"""

from __future__ import annotations

import pytest

from app.utils import maafw_version
from app.utils.maafw_version import maafw_manages_debug_images, parse_maafw_version


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("v5.16.1", (5, 16, 1)),
        ("5.16.1", (5, 16, 1)),
        ("v6.0.0", (6, 0, 0)),
        ("v6.0.0-beta.3", (6, 0, 0)),
        ("v6.0.0a1", (6, 0, 0)),
        ("v10.2", (10, 2, 0)),
    ],
)
def test_parse_maafw_version(text: str, expected: tuple[int, int, int]):
    assert parse_maafw_version(text) == expected


@pytest.mark.parametrize("text", [None, "", "unknown", "v"])
def test_parse_maafw_version_rejects_unparsable_text(text):
    assert parse_maafw_version(text) is None


def test_debug_image_ownership_follows_major_version(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(maafw_version, "current_maafw_version", lambda: (5, 16, 1))
    assert maafw_manages_debug_images() is False

    monkeypatch.setattr(maafw_version, "current_maafw_version", lambda: (6, 0, 0))
    assert maafw_manages_debug_images() is True

    monkeypatch.setattr(maafw_version, "current_maafw_version", lambda: (7, 0, 0))
    assert maafw_manages_debug_images() is True


def test_debug_image_ownership_falls_back_when_version_unknown(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(maafw_version, "current_maafw_version", lambda: None)
    assert maafw_manages_debug_images() is False
