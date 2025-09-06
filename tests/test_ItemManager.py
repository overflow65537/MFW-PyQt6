import unittest
import os
import sys
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径，解决导入问题
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

# 直接使用绝对导入
from app.core.ItemManager import (
    CoreSignalBus,
    TaskItem,
    ConfigItem,
    MultiConfig,
    BaseItemManager,
    ConfigManager,
    TaskManager
)


class TestItemManager(unittest.TestCase):
    def setUp(self):
        # 创建临时目录用于测试文件操作
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_file = Path(self.temp_dir) / "test_config.json"
        
        # 创建信号总线
        self.signal_bus = CoreSignalBus()
        
    def tearDown(self):
        # 清理临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('app.core.ItemManager.logger')
    def test_multi_config_initialization_and_save(self, mock_logger):
        """测试多配置元素的初始化和保存(其中包括单配置和单任务)"""
        # 创建一个TaskItem
        task_item = TaskItem(
            name="Test Task",
            item_id="t_test123",
            is_checked=True,
            task_option={"key": "value"},
            task_type="test"
        )
        
        # 创建一个ConfigItem
        config_item = ConfigItem(
            name="Test Config",
            item_id="c_config123",
            is_checked=True,
            task=[task_item],
            gpu=0,
            finish_option=1,
            know_task=[],
            task_type="config"
        )
        
        # 创建一个MultiConfig
        multi_config_dict = {
            "curr_config_id": "c_config123",
            "config_list": [config_item.save()]
        }
        multi_config = MultiConfig(multi_config_dict)
        
        # 验证初始化是否正确
        self.assertEqual(multi_config.curr_config_id, "c_config123")
        self.assertEqual(len(multi_config.config_list), 1)
        self.assertEqual(multi_config.config_list[0].name, "Test Config")
        self.assertEqual(len(multi_config.config_list[0].task), 1)
        self.assertEqual(multi_config.config_list[0].task[0].name, "Test Task")
        
        # 测试保存功能
        save_path = Path(self.temp_dir) / "multi_config.json"
        result = multi_config.save(save_path)
        
        # 验证保存是否成功
        self.assertTrue(result)
        self.assertTrue(save_path.exists())
        
        # 读取保存的文件并验证内容
        with open(save_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["curr_config_id"], "c_config123")
        self.assertEqual(len(saved_data["config_list"]), 1)
        self.assertEqual(saved_data["config_list"][0]["name"], "Test Config")
        self.assertEqual(len(saved_data["config_list"][0]["task"]), 1)
        self.assertEqual(saved_data["config_list"][0]["task"][0]["name"], "Test Task")
    
    @patch('app.core.ItemManager.logger')
    def test_config_manager_initialization_no_config(self, mock_logger):
        """测试配置管理器的初始化 - 无配置启动"""
        # 创建一个不存在的配置文件路径
        non_existent_file = Path(self.temp_dir) / "non_existent.json"
        
        # 初始化ConfigManager
        config_manager = ConfigManager(non_existent_file, self.signal_bus)
        
        # 验证初始化是否正确
        self.assertIsNotNone(config_manager.config)
        self.assertEqual(config_manager.config_list[0].name, "New Config")
        self.assertTrue(len(config_manager.config_list[0].task) > 0)
        
        # 验证是否创建了配置文件
        self.assertTrue(non_existent_file.exists())
    
    @patch('app.core.ItemManager.logger')
    def test_config_manager_initialization_with_config(self, mock_logger):
        """测试配置管理器的初始化 - 有配置启动"""
        # 创建一个有效的配置文件
        valid_config = {
            "curr_config_id": "c_valid123",
            "config_list": [
                {
                    "name": "Valid Config",
                    "item_id": "c_valid123",
                    "is_checked": True,
                    "task": [
                        {
                            "name": "Valid Task",
                            "item_id": "t_valid123",
                            "is_checked": True,
                            "task_option": {},
                            "task_type": "test"
                        }
                    ],
                    "gpu": 0,
                    "finish_option": 0,
                    "know_task": [],
                    "task_type": "config"
                }
            ]
        }
        
        # 写入配置文件
        config_file = Path(self.temp_dir) / "valid_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(valid_config, f, ensure_ascii=False, indent=4)
        
        # 初始化ConfigManager
        config_manager = ConfigManager(config_file, self.signal_bus)
        
        # 验证初始化是否正确
        self.assertEqual(config_manager.curr_config_id, "c_valid123")
        self.assertEqual(config_manager.config.name, "Valid Config")
        self.assertEqual(len(config_manager.config.task), 1)
        self.assertEqual(config_manager.config.task[0].name, "Valid Task")
    
    @patch('app.core.ItemManager.logger')
    def test_config_manager_initialization_invalid_config(self, mock_logger):
        """测试配置管理器的初始化 - 错误配置启动"""
        # 创建一个无效的配置文件
        invalid_config = {
            "some_invalid_key": "value"
        }
        
        # 写入配置文件
        config_file = Path(self.temp_dir) / "invalid_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_config, f, ensure_ascii=False, indent=4)
        
        # 初始化ConfigManager
        config_manager = ConfigManager(config_file, self.signal_bus)
        
        # 验证是否创建了默认配置
        self.assertIsNotNone(config_manager.config)
        self.assertEqual(config_manager.config_list[0].name, "New Config")
    
    @patch('app.core.ItemManager.logger')
    def test_config_manager_properties(self, mock_logger):
        """测试配置管理器中暴露的变量和设置部分"""
        # 初始化ConfigManager
        config_manager = ConfigManager(self.temp_config_file, self.signal_bus)
        
        # 测试curr_config_id属性
        original_id = config_manager.curr_config_id
        # 确保新ID是存在的配置ID，不使用任意字符串
        self.assertIsNotNone(original_id)
        
        # 测试config_list属性
        self.assertIsNotNone(config_manager.config_list)
        self.assertTrue(len(config_manager.config_list) > 0)
        
        # 测试config属性
        self.assertIsNotNone(config_manager.config)
        
        # 测试all_config属性
        original_all_config = config_manager.all_config
        new_config = config_manager.create_empty_config("New Test Config")
        config_manager.all_config = new_config
        self.assertEqual(config_manager.all_config.curr_config_id, new_config.curr_config_id)
    
    @patch('app.core.ItemManager.logger')
    def test_config_manager_add_remove_check(self, mock_logger):
        """测试配置管理器初始化完毕后的添加、删除和更改选中状态"""
        # 初始化ConfigManager
        config_manager = ConfigManager(self.temp_config_file, self.signal_bus)
        
        # 添加新配置
        new_config = ConfigItem(
            name="Added Config",
            item_id=BaseItemManager.generate_id("config"),
            is_checked=True,
            task=[],
            gpu=-1,
            finish_option=0,
            know_task=[],
            task_type="config"
        )
        
        config_manager.add_config(new_config)
        self.assertEqual(len(config_manager.config_list), 2)
        self.assertEqual(config_manager.config_list[1].name, "Added Config")
        
        # 更改选中状态
        config_id = config_manager.config_list[1].item_id
        result = config_manager.config_checkbox_state_changed(config_id, False)
        self.assertTrue(result)
        self.assertFalse(config_manager.config_list[1].is_checked)
        
        # 删除配置
        result = config_manager.remove_config(config_id)
        self.assertTrue(result)
        self.assertEqual(len(config_manager.config_list), 1)
    
    @patch('app.core.ItemManager.logger')
    def test_task_manager_operations(self, mock_logger):
        """测试任务管理器的初始化和添加、删除、更新和更改选中状态"""
        # 初始化ConfigManager
        config_manager = ConfigManager(self.temp_config_file, self.signal_bus)
        
        # 初始化TaskManager
        task_manager = TaskManager(config_manager, self.signal_bus)
        
        # 验证初始化是否正确
        self.assertIsNotNone(task_manager.task_list)
        
        # 添加任务
        new_task = TaskItem(
            name="New Task",
            item_id=BaseItemManager.generate_id("task"),
            is_checked=True,
            task_option={"new": "option"},
            task_type="test"
        )
        
        result = task_manager.add_task(new_task)
        self.assertTrue(result)
        self.assertEqual(len(task_manager.task_list), 3)  # 默认有两个任务
        
        # 更新任务
        task_id = task_manager.task_list[2].item_id
        updated_task = TaskItem(
            name="Updated Task",
            item_id=task_id,
            is_checked=True,
            task_option={"updated": "option"},
            task_type="test"
        )
        
        result = task_manager.update_task(task_id, updated_task)
        self.assertTrue(result)
        self.assertEqual(task_manager.task_list[2].name, "Updated Task")
        self.assertEqual(task_manager.task_list[2].task_option, {"updated": "option"})
        
        # 更改选中状态
        result = task_manager.task_checkbox_state_changed(task_id, False)
        self.assertTrue(result)
        self.assertFalse(task_manager.task_list[2].is_checked)
        
        # 删除任务
        result = task_manager.remove_task(task_id)
        self.assertTrue(result)
        self.assertEqual(len(task_manager.task_list), 2)


if __name__ == '__main__':
    unittest.main()