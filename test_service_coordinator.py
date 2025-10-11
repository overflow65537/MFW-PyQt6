import pytest
from pathlib import Path
from app.core.core import ServiceCoordinator, TaskItem, ConfigItem

def test_service_coordinator_basic(tmp_path):
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
        is_checked=True,
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

    # 添加任务
    task = TaskItem(name="T1", item_id="", is_checked=True, task_option={"a": 1})
    assert sc.task.add_task(task)
    tasks = sc.task.get_tasks()
    assert any(t.name == "T1" for t in tasks)

    # 修改任务
    t1 = next(t for t in tasks if t.name == "T1")
    t1.task_option["a"] = 2
    assert sc.modify_task(t1)
    tasks2 = sc.task.get_tasks()
    t1_mod = next(t for t in tasks2 if t.name == "T1")
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
