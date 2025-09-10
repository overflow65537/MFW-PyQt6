from pathlib import Path
import sys
import os
import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块
from app.core.ItemManager import ConfigManager, TaskManager, ConfigItem, TaskItem, BaseItemManager
from app.core.CoreSignalBus import core_signalBus


class OutputManager:
    """管理输出到控制台和文件"""
    def __init__(self, log_file_path=None):
        # 如果没有指定日志文件路径，则使用当前时间生成一个
        if log_file_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file_path = Path(f"output_log_{timestamp}.txt")
        else:
            self.log_file_path = Path(log_file_path)
        
        # 创建日志文件
        with open(self.log_file_path, "w", encoding="utf-8") as f:
            f.write(f"输出日志 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
        
        print(f"输出将同时保存到文件：{self.log_file_path}")
    
    def print_and_log(self, message):
        """同时打印到控制台和写入到日志文件"""
        print(message)
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")


def print_current_config(log_print, config_manager):
    """打印当前配置信息"""
    log_print("\n==== 当前配置信息 ====")
    if config_manager.config:
        log_print(f"当前配置名称: {config_manager.config.name}")
        log_print(f"当前配置ID: {config_manager.config.item_id}")
        log_print(f"配置总数: {len(config_manager.config_list)}")  # 修改这里，使用config_list而不是all_config
    else:
        log_print("当前没有选择的配置")
        log_print(f"配置总数: {len(config_manager.config_list)}")  # 修改这里，使用config_list而不是all_config
    log_print("=" * 25)


def main():
    # 创建输出管理器，将输出保存到文件
    output_manager = OutputManager()
    
    # 定义一个打印函数，同时输出到控制台和文件
    def log_print(message):
        output_manager.print_and_log(message)
    
    # 1. 创建一个临时的配置文件路径
    temp_config_path = Path("temp_config.json")
    
    try:
        # 2. 创建配置管理器和任务管理器
        log_print("创建配置管理器...")
        config_manager = ConfigManager(temp_config_path, core_signalBus)
        
        log_print("创建任务管理器...")
        task_manager = TaskManager(config_manager, core_signalBus)
        
        # 打印初始配置状态
        print_current_config(log_print, config_manager)
        
        # 3. 添加一个名为"测试配置"的新配置
        log_print("\n添加新配置：测试配置")
        # 生成配置ID
        config_id = BaseItemManager.generate_id("config")
        # 创建默认任务列表
        default_tasks = []
        # 创建新配置项
        new_config = ConfigItem(
            name="测试配置",
            item_id=config_id,
            is_checked=True,
            task=default_tasks,
            gpu=-1,
            finish_option=0,
            know_task=[],
            task_type="config"
        )
        # 添加配置
        config_manager.add_config(new_config)
        log_print(f"成功添加配置：{new_config.name} (ID: {new_config.item_id})")
        
        # 4. 将当前配置变更为新配置
        log_print(f"\n将当前配置变更为：{new_config.name}")
        # 打印配置变更前的状态
        print_current_config(log_print, config_manager)
        config_manager.curr_config_id = new_config.item_id
        log_print(f"当前配置已变更为：{config_manager.config.name}")
        
        # 5. 在新配置中添加一个测试任务
        log_print("\n在测试配置中添加测试任务...")
        # 打印配置状态
        print_current_config(log_print, config_manager)
        # 生成任务ID
        task_id = BaseItemManager.generate_id("task")
        # 创建测试任务
        test_task = TaskItem(
            name="测试任务",
            item_id=task_id,
            is_checked=True,
            task_option={},
            task_type="test"
        )
        # 添加任务
        task_manager.add_task(test_task)
        log_print(f"成功添加任务：{test_task.name} (ID: {test_task.item_id})")
        
        # 6. 调用task_list显示任务列表
        log_print("\n当前任务列表：")
        for task in task_manager.task_list:
            log_print(f"- {task.name} (ID: {task.item_id})")
        
        # 7. 通过get_task获取测试任务
        log_print(f"\n通过get_task获取任务：{test_task.name}")
        retrieved_task = task_manager.get_task(test_task.item_id)
        if retrieved_task:
            log_print(f"成功获取任务：{retrieved_task.name}")
            
            # 8. 修改测试任务的名称为"测试任务2"
            log_print("\n修改任务名称为：测试任务2")
            # 打印配置状态
            print_current_config(log_print, config_manager)
            retrieved_task.name = "测试任务2"
            # 更新任务
            task_manager.update_task(retrieved_task.item_id, retrieved_task)
            log_print(f"任务名称已更新为：{retrieved_task.name}")
        
        # 9. 再次调用task_list显示更新后的任务列表
        log_print("\n更新后的任务列表：")
        for task in task_manager.task_list:
            log_print(f"- {task.name} (ID: {task.item_id})")
            
        # 记录完成信息
        log_print(f"\n{"=" * 50}")
        log_print(f"操作完成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_print(f"输出已保存到：{output_manager.log_file_path}")
            
    finally:
        # 清理临时文件
        if temp_config_path.exists():
            try:
                temp_config_path.unlink()
                log_print(f"\n临时文件已清理：{temp_config_path}")
            except:
                pass


if __name__ == "__main__":
    main()