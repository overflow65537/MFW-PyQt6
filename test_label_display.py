"""测试任务 label 显示逻辑"""
import json
from pathlib import Path

# 模拟接口数据
interface = {
    "task": [
        {
            "name": "活动：绿湖噩梦 17 艰难（活动已结束）",
            "label": "$活动任务",
            "entry": "ANightmareAtGreenLake"
        },
        {
            "name": "领取奖励",
            "label": "$领取奖励",
            "entry": "Awards"
        }
    ]
}

# 模拟 TaskItem
class MockTask:
    def __init__(self, name):
        self.name = name

# 模拟 _get_display_name 逻辑
def get_display_name(task, interface):
    """获取显示名称（从 interface 获取 label，否则使用 name）"""
    if interface:
        for task_info in interface.get("task", []):
            if task_info["name"] == task.name:
                display_label = task_info.get("label", task_info.get("name", task.name))
                # 移除 $ 前缀（如果存在）
                if display_label.startswith("$"):
                    display_label = display_label[1:]
                print(f"找到匹配: {task.name} -> {display_label}")
                return display_label
    # 如果没有找到对应的 label，返回 name
    print(f"未找到匹配，使用 name: {task.name}")
    return task.name

# 测试
print("=" * 50)
print("测试任务 label 显示逻辑")
print("=" * 50)

task1 = MockTask("活动：绿湖噩梦 17 艰难（活动已结束）")
result1 = get_display_name(task1, interface)
print(f"任务1: {task1.name}")
print(f"显示: {result1}")
print(f"预期: 活动任务")
print(f"✓ 正确" if result1 == "活动任务" else "✗ 错误")
print()

task2 = MockTask("领取奖励")
result2 = get_display_name(task2, interface)
print(f"任务2: {task2.name}")
print(f"显示: {result2}")
print(f"预期: 领取奖励")
print(f"✓ 正确" if result2 == "领取奖励" else "✗ 错误")
print()

# 测试空 interface
task3 = MockTask("测试任务")
result3 = get_display_name(task3, {})
print(f"任务3（无interface）: {task3.name}")
print(f"显示: {result3}")
print(f"预期: 测试任务")
print(f"✓ 正确" if result3 == "测试任务" else "✗ 错误")
