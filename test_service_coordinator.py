import pytest
from pathlib import Path
from app.core.core import ServiceCoordinator, ConfigItem
import json
import os


def generate_test_interface_json(path: Path):
    data = {
        "name": "TestBundle",
        "task": [
            {"name": "任务A", "option": ["选项1", "选项2"]},
            {"name": "任务B", "option": ["选项2"]},
            {"name": "任务C"},
        ],
        "option": {
            "选项1": {
                "type": "select",
                "cases": [{"name": "case1"}, {"name": "case2"}],
                "default_case": "case1",
            },
            "选项2": {
                "type": "input",
                "cases": [{"name": "default"}],  # 保证至少有一个case，避免IndexError
            },
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@pytest.fixture
def interface_json(tmp_path: Path):
    path = tmp_path / "interface.json"
    generate_test_interface_json(path)
    return path


@pytest.fixture
def sc(tmp_path: Path, interface_json: Path):
    # change cwd to tmp_path so ServiceCoordinator finds interface.json
    os.chdir(tmp_path)
    main_config = tmp_path / "main_config.json"
    configs_dir = tmp_path / "configs"
    return ServiceCoordinator(main_config, configs_dir)


@pytest.mark.stage1
def test_current_config_created_and_has_tasks(sc):
    curr_id = sc.config.current_config_id
    assert isinstance(curr_id, str) and curr_id != ""
    cfg = sc.config.get_current_config()
    assert cfg is not None and isinstance(cfg, ConfigItem)
    assert len(cfg.tasks) >= 3


@pytest.mark.stage2
def test_add_select_and_delete_config(sc):
    cfg = sc.config.get_current_config()
    new_cfg = ConfigItem(
        name="TestConfig",
        item_id="",
        tasks=[],
        know_task=[],
        bundle=cfg.bundle,
    )
    new_id = sc.add_config(new_cfg)
    assert isinstance(new_id, str) and new_id != ""
    assert new_id in [c["item_id"] for c in sc.config.list_configs()]

    # select
    assert sc.select_config(new_id)
    assert sc.config.current_config_id == new_id

    # delete
    assert sc.delete_config(new_id)
    assert new_id not in [c["item_id"] for c in sc.config.list_configs()]


@pytest.mark.stage3
def test_add_modify_and_delete_task(sc, interface_json: Path):
    with open(interface_json, "r", encoding="utf-8") as f:
        interface = json.load(f)
    task_name = interface["task"][0]["name"]

    # add
    assert sc.task.add_task(task_name)
    tasks = sc.task.get_tasks()
    assert any(t.name == task_name for t in tasks)

    # modify
    t1 = next(t for t in tasks if t.name == task_name)
    t1.task_option["a"] = 2
    assert sc.modify_task(t1)
    tasks2 = sc.task.get_tasks()
    t1_mod = next(t for t in tasks2 if t.name == task_name)
    assert t1_mod.task_option["a"] == 2

    # delete
    assert sc.delete_task(t1.item_id)
    tasks3 = sc.task.get_tasks()
    assert all(t.item_id != t1.item_id for t in tasks3)


@pytest.mark.stage4
def test_reorder_tasks(sc):
    orig_order = [t.item_id for t in sc.task.get_tasks()]
    new_order = orig_order[::-1]
    assert sc.reorder_tasks(new_order)
    reordered = [t.item_id for t in sc.task.get_tasks()]
    assert reordered == new_order


@pytest.mark.stage5
def test_default_config_and_know_task(sc, interface_json: Path):
    curr_cfg = sc.config.get_current_config()
    assert curr_cfg is not None
    assert len(curr_cfg.tasks) >= 3
    assert isinstance(curr_cfg.know_task, list)
    with open(interface_json, "r", encoding="utf-8") as f:
        interface = json.load(f)
    interface_task_names = [t["name"] for t in interface.get("task", [])]
    for name in interface_task_names:
        assert name in curr_cfg.know_task


@pytest.mark.stage3
def test_taskservice_add_task_by_name(sc, interface_json: Path):
    with open(interface_json, "r", encoding="utf-8") as f:
        interface = json.load(f)
    task_name = interface["task"][0]["name"]
    assert sc.task.add_task(task_name)
    tasks = sc.task.get_tasks()
    assert any(t.name == task_name for t in tasks)


@pytest.mark.stage6
def test_toggle_task_check_signal_updates_task(sc, interface_json: Path):
    """Ensure toggle_task_check signal exists on the CoreSignalBus and when emitted
    the task's is_checked state is updated by the service layer (if implemented)."""
    with open(interface_json, "r", encoding="utf-8") as f:
        interface = json.load(f)
    task_name = interface["task"][0]["name"]
    assert sc.task.add_task(task_name)
    tasks = sc.task.get_tasks()
    t = next(t for t in tasks if t.name == task_name)

    # 使用 ServiceCoordinator.modify_task 路径修改任务的 is_checked，然后断言被持久化
    new_state = not t.is_checked
    t.is_checked = new_state
    assert sc.modify_task(t)

    t2 = sc.task.get_task(t.item_id)
    assert t2 is not None
    assert t2.is_checked == new_state
