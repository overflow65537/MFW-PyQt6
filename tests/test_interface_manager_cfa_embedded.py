import json
from pathlib import Path

import jsonc
import pytest

from app.core.service.interface_manager import InterfaceManager
from hotfix_extract import (
    CFA_SETTING_FILENAME,
    apply_cfa_embedded_to_interface,
    sync_interface_after_hotfix,
)


@pytest.fixture
def bundle_dir(tmp_path: Path) -> Path:
    (tmp_path / CFA_SETTING_FILENAME).write_text(
        json.dumps({"update_flag": "1", "embedded": True}),
        encoding="utf-8",
    )
    interface = {
        "name": "TestBundle",
        "version": "1.0.0",
        "agent": {"child_args": ["{PROJECT_DIR}/agent/main.py"]},
    }
    (tmp_path / "interface.json").write_text(
        json.dumps(interface, ensure_ascii=False),
        encoding="utf-8",
    )
    return tmp_path


def test_apply_cfa_embedded_to_interface_updates_agent(bundle_dir: Path):
    interface = {"agent": {"embedded": False}}
    assert apply_cfa_embedded_to_interface(interface, bundle_dir) is True
    assert interface["agent"]["embedded"] is True


def test_apply_cfa_embedded_to_interface_noop_when_missing(bundle_dir: Path):
    interface = {"agent": {"embedded": False}}
    (bundle_dir / CFA_SETTING_FILENAME).unlink()
    assert apply_cfa_embedded_to_interface(interface, bundle_dir) is False
    assert interface["agent"]["embedded"] is False


def test_interface_manager_initialize_syncs_embedded(bundle_dir: Path):
    manager = InterfaceManager()
    manager._reset_state()
    manager.initialize(interface_path=bundle_dir / "interface.json")

    assert manager.get_original_interface()["agent"]["embedded"] is True
    assert manager.get_interface()["agent"]["embedded"] is True

    saved = jsonc.loads((bundle_dir / "interface.json").read_text(encoding="utf-8"))
    assert saved["agent"]["embedded"] is True


def test_interface_manager_finds_cfa_setting_in_parent_dir(tmp_path: Path):
    bundle_root = tmp_path / "bundle"
    nested = bundle_root / "assets"
    nested.mkdir(parents=True)
    (bundle_root / CFA_SETTING_FILENAME).write_text(
        json.dumps({"update_flag": "1", "embedded": True}),
        encoding="utf-8",
    )
    (nested / "interface.json").write_text(
        json.dumps(
            {
                "name": "Nested",
                "agent": {"child_args": ["agent/main.py"], "embedded": False},
            }
        ),
        encoding="utf-8",
    )

    manager = InterfaceManager()
    manager._reset_state()
    manager.initialize(interface_path=nested / "interface.json")

    assert manager.get_original_interface()["agent"]["embedded"] is True


def test_sync_interface_after_hotfix_uses_apply_helper(bundle_dir: Path):
    interface_paths = [bundle_dir / "interface.json"]
    assert sync_interface_after_hotfix(interface_paths, "2.0.0", bundle_dir) is True

    saved = jsonc.loads((bundle_dir / "interface.json").read_text(encoding="utf-8"))
    assert saved["version"] == "2.0.0"
    assert saved["agent"]["embedded"] is True
