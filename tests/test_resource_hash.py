import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import jsonc
import pytest

from app.core.utils.resource_hash import (
    apply_resource_hashes_to_interface,
    compute_resource_hash_for_paths,
    resolve_resource_path,
)
from hotfix_extract import sync_interface_after_hotfix


def test_resolve_resource_path_strips_project_dir(tmp_path: Path):
    (tmp_path / "resource").mkdir()
    resolved = resolve_resource_path(tmp_path, "{PROJECT_DIR}/resource")
    assert resolved == (tmp_path / "resource").resolve()


def test_resolve_resource_path_returns_none_for_missing(tmp_path: Path):
    assert resolve_resource_path(tmp_path, "missing") is not None
    assert not resolve_resource_path(tmp_path, "missing").exists()


class _FakeWaitResult:
    def __init__(self, succeeded: bool = True):
        self.succeeded = succeeded


class _FakeResource:
    instances: list["_FakeResource"] = []
    post_calls: list[Path] = []

    def __init__(self):
        self.instances.append(self)
        self._hash = "computed-hash"

    def use_cpu(self) -> None:
        return None

    def post_bundle(self, path: Path | str):
        self.post_calls.append(Path(path))
        return MagicMock(wait=lambda: _FakeWaitResult(True))

    @property
    def hash(self) -> str:
        return self._hash


@pytest.fixture(autouse=True)
def _reset_fake_resource():
    _FakeResource.instances.clear()
    _FakeResource.post_calls.clear()
    yield


def test_compute_resource_hash_for_paths_multi_path(tmp_path: Path):
    first = tmp_path / "res_a"
    second = tmp_path / "res_b"
    first.mkdir()
    second.mkdir()

    with patch(
        "maa.resource.Resource",
        _FakeResource,
    ):
        result = compute_resource_hash_for_paths(
            tmp_path,
            ["res_a", "res_b"],
        )

    assert result == "computed-hash"
    assert _FakeResource.post_calls == [first.resolve(), second.resolve()]


def test_compute_resource_hash_returns_none_when_path_missing(tmp_path: Path):
    with patch(
        "maa.resource.Resource",
        _FakeResource,
    ):
        assert compute_resource_hash_for_paths(tmp_path, ["missing"]) is None
    assert _FakeResource.instances == []


def test_compute_resource_hash_returns_none_when_load_fails(tmp_path: Path):
    resource_dir = tmp_path / "res"
    resource_dir.mkdir()

    class _FailResource(_FakeResource):
        def post_bundle(self, path: Path | str):
            return MagicMock(wait=lambda: _FakeWaitResult(False))

    with patch(
        "maa.resource.Resource",
        _FailResource,
    ):
        assert compute_resource_hash_for_paths(tmp_path, ["res"]) is None


def test_apply_resource_hashes_overwrites_existing(tmp_path: Path):
    resource_dir = tmp_path / "res"
    resource_dir.mkdir()
    interface = {
        "resource": [
            {
                "name": "main",
                "path": ["res"],
                "hash": "old-hash",
            }
        ]
    }

    with patch(
        "maa.resource.Resource",
        _FakeResource,
    ):
        updated = apply_resource_hashes_to_interface(interface, tmp_path)

    assert updated == 1
    assert interface["resource"][0]["hash"] == "computed-hash"


def test_apply_resource_hashes_skips_failed_entry(tmp_path: Path):
    ok_dir = tmp_path / "ok"
    ok_dir.mkdir()
    interface = {
        "resource": [
            {"name": "bad", "path": ["missing"], "hash": "keep-bad"},
            {"name": "good", "path": ["ok"], "hash": "keep-good"},
        ]
    }

    with patch(
        "maa.resource.Resource",
        _FakeResource,
    ):
        updated = apply_resource_hashes_to_interface(interface, tmp_path)

    assert updated == 1
    assert interface["resource"][0]["hash"] == "keep-bad"
    assert interface["resource"][1]["hash"] == "computed-hash"


def test_sync_interface_after_hotfix_writes_hash(tmp_path: Path):
    resource_dir = tmp_path / "res"
    resource_dir.mkdir()
    interface = {
        "name": "TestBundle",
        "version": "1.0.0",
        "agent": {"embedded": False},
        "resource": [{"name": "main", "path": ["res"], "hash": "old-hash"}],
    }
    (tmp_path / "interface.json").write_text(
        json.dumps(interface, ensure_ascii=False),
        encoding="utf-8",
    )
    (tmp_path / "CFA_setting.json").write_text(
        json.dumps({"update_flag": "1", "embedded": True}),
        encoding="utf-8",
    )

    with patch(
        "maa.resource.Resource",
        _FakeResource,
    ):
        assert (
            sync_interface_after_hotfix(
                [tmp_path / "interface.json"],
                "2.0.0",
                tmp_path,
            )
            is True
        )

    saved = jsonc.loads((tmp_path / "interface.json").read_text(encoding="utf-8"))
    assert saved["version"] == "2.0.0"
    assert saved["agent"]["embedded"] is True
    assert saved["resource"][0]["hash"] == "computed-hash"
