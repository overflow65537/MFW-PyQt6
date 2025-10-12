import pytest
from pathlib import Path
from app.core.core import ServiceCoordinator, TaskItem, ConfigItem
import json
import os

def generate_test_interface_json(path):
    data = {
        "name": "TestBundle",
        "task": [
            {"name": "任务A", "option": ["选项1", "选项2"]},
            {"name": "任务B", "option": ["选项2"]},
            {"name": "任务C"}
        ],
        "option": {
            "选项1": {
                "type": "select",
                "cases": [{"name": "case1"}, {"name": "case2"}],
                "default_case": "case1"
            },
            "选项2": {
                "type": "input",
                "cases": [{"name": "default"}],  # 保证至少有一个case，避免IndexError
                
            }
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def test_service_coordinator_basic(tmp_path):
    generate_test_interface_json(tmp_path / "interface.json")
    import os
    os.chdir(tmp_path)
    main_config = tmp_path / "main_config.json"
    configs_dir = tmp_path / "configs"
    sc = ServiceCoordinator(main_config, configs_dir)

    # 默认配置创建
    curr_id = sc.config.current_config_id
    assert isinstance(curr_id, str) and curr_id != ""
    cfg = sc.config.get_current_config()
    assert cfg is not None and isinstance(cfg, ConfigItem)
    assert len(cfg.tasks) >= 3

    # 添加配置
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

    # 选择配置
    assert sc.select_config(new_id)
    assert sc.config.current_config_id == new_id
    curr_cfg = sc.config.get_current_config()
    assert curr_cfg is not None
    assert curr_cfg.name == "TestConfig"

    # 添加任务（用自动生成的 interface.json 里的任务名）
    with open(tmp_path / "interface.json", "r", encoding="utf-8") as f:
        interface = json.load(f)
    task_name = interface["task"][0]["name"]  # 这里是 '任务A'
    assert sc.task.add_task(task_name)
    tasks = sc.task.get_tasks()
    assert any(t.name == task_name for t in tasks)

    # 修改任务
    t1 = next(t for t in tasks if t.name == task_name)
    t1.task_option["a"] = 2
    assert sc.modify_task(t1)
    tasks2 = sc.task.get_tasks()
    t1_mod = next(t for t in tasks2 if t.name == task_name)
    assert t1_mod.task_option["a"] == 2

    # 删除任务
    assert sc.delete_task(t1.item_id)
    tasks3 = sc.task.get_tasks()
    assert all(t.item_id != t1.item_id for t in tasks3)

    # 删除配置
    assert sc.delete_config(new_id)
    assert new_id not in [c["item_id"] for c in sc.config.list_configs()]

    # 重新排序任务（只对当前配置有效）
    orig_order = [t.item_id for t in sc.task.get_tasks()]
    new_order = orig_order[::-1]
    assert sc.reorder_tasks(new_order)
    reordered = [t.item_id for t in sc.task.get_tasks()]
    assert reordered == new_order

def test_default_config_and_know_task(tmp_path):
    generate_test_interface_json(tmp_path / "interface.json")
    os.chdir(tmp_path)
    main_config = tmp_path / "main_config.json"
    configs_dir = tmp_path / "configs"
    sc = ServiceCoordinator(main_config, configs_dir)

    # 检查主配置自动生成默认配置
    curr_cfg = sc.config.get_current_config()
    assert curr_cfg is not None
    # 默认任务数量 >= 3
    assert len(curr_cfg.tasks) >= 3
    # know_task 自动识别
    assert isinstance(curr_cfg.know_task, list)
    # interface.json 中所有任务都在 know_task
    with open(tmp_path / "interface.json", "r", encoding="utf-8") as f:
        interface = json.load(f)
    interface_task_names = [t["name"] for t in interface.get("task", [])]
    for name in interface_task_names:
        assert name in curr_cfg.know_task

def test_taskservice_add_task_by_name(tmp_path):
    generate_test_interface_json(tmp_path / "interface.json")
    os.chdir(tmp_path)
    main_config = tmp_path / "main_config.json"
    configs_dir = tmp_path / "configs"
    sc = ServiceCoordinator(main_config, configs_dir)
    # 选择当前配置
    curr_cfg = sc.config.get_current_config()
    assert curr_cfg is not None

    # 用任务名添加任务（新接口）
    with open(tmp_path / "interface.json", "r", encoding="utf-8") as f:
        interface = json.load(f)
    task_name = interface["task"][0]["name"]
    assert sc.task.add_task(task_name)
    # 检查任务已添加
    tasks = sc.task.get_tasks()
    assert any(t.name == task_name for t in tasks)