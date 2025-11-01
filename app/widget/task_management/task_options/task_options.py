"""普通任务选项模块

提供普通任务选项的显示逻辑。
"""

import json
from pathlib import Path
from typing import List
from app.utils.logger import logger
from app.utils.i18n_manager import get_interface_i18n
from ._mixin_base import MixinBase


class TaskOptionsMixin(MixinBase):
    """普通任务选项 Mixin
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    
    提供普通任务选项的显示功能，包括：
    - 从 interface.json 读取任务配置
    - 按智能顺序添加选项
    - 处理嵌套选项
    - 显示任务描述
    
    依赖的宿主类方法/属性：
    - self.task
    - self._get_option_value
    - self.set_description (在选项区域末尾添加描述)
    - self._add_combox_option (在 WidgetCreatorsMixin 中)
    - self._add_multi_input_option (在 WidgetCreatorsMixin 中)
    """
    
    def _show_task_option(self, item):
        """显示任务选项
        
        Args:
            item: TaskItem 对象
        """
        # 获取 interface 配置（使用翻译后的数据）
        interface = getattr(self.task, "interface", None)
        if not interface:
            try:
                i18n = get_interface_i18n()
                interface = i18n.get_translated_interface()
            except Exception as e:
                logger.error(f"获取翻译后的 interface.json 失败: {e}")
                # 降级方案：直接加载原始 interface.json
                interface_path = Path.cwd() / "interface.json"
                if not interface_path.exists():
                    return
                with open(interface_path, "r", encoding="utf-8") as f:
                    interface = json.load(f)
        
        # 查找任务模板
        target_task = None
        for task_template in interface["task"]:
            if task_template["name"] == item.name:
                target_task = task_template
                break
        
        if target_task is None:
            logger.warning(f"未找到任务模板: {item.name}")
            return
        
        # 收集描述内容
        descriptions = []
        task_description = target_task.get("description")
        if task_description:
            descriptions.append(task_description)
        
        task_doc = target_task.get("doc")
        if task_doc:
            descriptions.append(task_doc)
        
        # 先添加选项
        self._add_options_with_order(target_task, interface, item)
        
        # 最后添加描述（如果有）
        if descriptions:
            combined_description = "\n\n---\n\n".join(descriptions)
            self.set_description(combined_description)
    
    def _add_options_with_order(self, target_task, interface, item):
        """按照智能顺序添加选项
        
        主选项按 task.option 顺序添加，嵌套选项紧随其父选项。
        
        Args:
            target_task: 任务模板配置
            interface: 完整的 interface 配置
            item: 当前任务项
        """
        added_options = set()  # 跟踪已添加的选项
        
        def _get_task_info(option):
            """获取选项的显示信息和配置"""
            option_config = interface["option"][option]
            display_name = option_config.get("label", option_config.get("name", option))
            obj_name = option
            options = self.Get_Task_List(interface, option)
            current = self._get_option_value(item.task_option, option, None)
            icon_path = option_config.get("icon", "")
            tooltip = option_config.get("description", "")
            
            # 收集选项提示信息
            option_tooltips = {}
            for case in option_config.get("cases", []):
                option_tooltips[case["name"]] = case.get("description", "")
            
            return (
                display_name,
                obj_name,
                options,
                current,
                icon_path,
                tooltip,
                option_tooltips,
                option_config,
            )
        
        def _get_current_case_config(option_name):
            """获取选项当前选中的 case 配置"""
            option_config = interface["option"].get(option_name)
            if not option_config:
                return None
            
            cases = option_config.get("cases", [])
            if not cases:
                return None
            
            # 尝试获取当前值对应的 case
            current_value = self._get_option_value(item.task_option, option_name, None)
            if current_value:
                for case in cases:
                    if case.get("name") == current_value:
                        return case
            
            # 默认返回第一个 case
            return cases[0]
        
        def _add_option_recursive(option_name, depth=0):
            """递归添加选项及其嵌套选项"""
            # 防止重复添加和无限递归
            if option_name in added_options or depth > 10:
                return
            
            added_options.add(option_name)
            
            # 获取选项配置
            option_config = interface["option"].get(option_name)
            if not option_config:
                logger.warning(f"选项配置不存在: {option_name}")
                return
            
            # 判断选项类型
            option_type = option_config.get("type", "select")
            
            if option_type == "multi_input":
                # 多输入项类型
                self._add_multi_input_option(
                    option_name,
                    option_config,
                    item,
                    parent_option_name=None,
                    insert_index=None,
                )
            else:
                # 下拉框类型（默认）
                (
                    display_name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    tooltip,
                    option_tooltips,
                    _,
                ) = _get_task_info(option_name)
                
                # 添加下拉框选项
                # skip_initial_nested=True 避免在 _add_combox_option 内部自动加载嵌套选项
                # 因为我们会在后面通过 _update_nested_options 统一添加
                widget = self._add_combox_option(
                    name=display_name,
                    obj_name=obj_name,
                    options=options,
                    current=current,
                    icon_path=icon_path,
                    editable=False,
                    tooltip=tooltip,
                    option_tooltips=option_tooltips,
                    option_config=option_config,
                    skip_initial_nested=True,
                    block_signals=False,
                    return_widget=True,
                )
                
                # 手动调用 _update_nested_options 来添加嵌套选项
                # recursive=True 让它递归加载所有层级的嵌套选项
                if widget and option_config:
                    self._update_nested_options(
                        widget,
                        current or widget.currentText(),
                        recursive=True,
                    )
        
        # 按照 task 的 option 数组顺序添加选项
        for option in target_task.get("option", []):
            _add_option_recursive(option)
    
    def Get_Task_List(self, interface, target):
        """根据选项名称获取所有 case 的 name 列表
        
        Args:
            interface: interface 配置字典
            target: 选项名称
            
        Returns:
            list: 包含所有 case 的 name 列表，如果选项没有 cases 则返回空列表
        """
        lists = []
        option_config = interface["option"].get(target)
        if not option_config:
            return lists
        
        # 某些选项类型（如 multi_input）没有 cases
        Task_Config = option_config.get("cases")
        if not Task_Config:
            return lists
        
        Lens = len(Task_Config) - 1
        for i in range(Lens, -1, -1):
            lists.append(Task_Config[i]["name"])
        lists.reverse()
        return lists
