"""选项面板控件 - 重构简化版示例

这是重构后 OptionWidget 的简化示例,展示如何使用各个模块。
原有的3000+行代码被拆分到多个专门的模块中。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSplitter,
)
from qfluentwidgets import SimpleCardWidget, BodyLabel, ScrollArea

from app.utils.logger import logger
from app.utils.gui_helper import IconLoader
from .....core.Core import TaskItem, ConfigItem, ServiceCoordinator

# 导入各个功能模块
from .option_data_manager import OptionDataManager
from .widget_factory import WidgetFactory
from .nested_option_handler import NestedOptionHandler
from .device_manager import DeviceManager


class OptionWidgetRefactored(QWidget):
    """选项面板控件 - 重构版
    
    职责:
    - 管理 UI 布局
    - 协调各个功能模块
    - 处理信号连接
    
    复杂逻辑已委托给专门的模块:
    - OptionDataManager: 数据管理
    - WidgetFactory: 控件创建
    - NestedOptionHandler: 嵌套选项处理
    - DeviceManager: 设备管理
    """

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self.task = self.service_coordinator.task
        self.config = self.service_coordinator.config
        self.core_signalBus = self.service_coordinator.signal_bus

        # 创建图标加载器
        self.icon_loader = IconLoader(service_coordinator)

        # 初始化 UI
        self._init_ui()
        
        # 初始化功能模块
        self._init_managers()
        
        # 连接信号
        self._connect_signals()
        
        # 初始状态
        self._toggle_description(visible=False)
        self.set_title(self.tr("Options"))
        self.current_task = None

    def _init_ui(self):
        """初始化 UI - 只负责界面布局"""
        self.main_layout = QVBoxLayout(self)
        
        # 标题
        self.title_widget = BodyLabel()
        self.title_widget.setStyleSheet("font-size: 20px;")
        self.title_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 选项区域
        self.option_area_card = SimpleCardWidget()
        self.option_area_card.setClickEnabled(False)
        self.option_area_card.setBorderRadius(8)
        
        self.option_area_widget = ScrollArea()
        self.option_area_widget.setWidgetResizable(True)
        self.option_area_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.option_area_widget.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        
        option_container = QWidget()
        self.option_area_layout = QVBoxLayout(option_container)
        self.option_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.option_area_layout.setContentsMargins(10, 10, 10, 10)
        
        self.option_area_widget.setWidget(option_container)
        
        card_layout = QVBoxLayout()
        card_layout.addWidget(self.option_area_widget)
        card_layout.setContentsMargins(0, 0, 0, 0)
        self.option_area_card.setLayout(card_layout)
        
        # 描述区域
        self.description_title = BodyLabel("功能描述")
        self.description_title.setStyleSheet("font-size: 20px;")
        self.description_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.description_area_card = SimpleCardWidget()
        self.description_area_card.setClickEnabled(False)
        self.description_area_card.setBorderRadius(8)
        
        self.description_area_widget = QWidget()
        self.description_layout = QVBoxLayout(self.description_area_widget)
        self.description_layout.setContentsMargins(10, 10, 10, 10)
        
        self.description_content = BodyLabel()
        self.description_content.setWordWrap(True)
        self.description_layout.addWidget(self.description_content)
        self.description_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.description_scroll_area = ScrollArea()
        self.description_scroll_area.setWidget(self.description_area_widget)
        self.description_scroll_area.setWidgetResizable(True)
        self.description_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.description_scroll_area.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        
        desc_card_layout = QVBoxLayout(self.description_area_card)
        desc_card_layout.setContentsMargins(0, 0, 0, 0)
        desc_card_layout.addWidget(self.description_scroll_area)
        
        # 分割器
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setStyleSheet(
            """
            QSplitter::handle:vertical {
                background: transparent;   
            }
            """
        )
        
        self.option_splitter_widget = QWidget()
        self.option_splitter_layout = QVBoxLayout(self.option_splitter_widget)
        self.option_splitter_layout.addWidget(self.option_area_card)
        self.option_splitter_layout.setContentsMargins(0, 0, 0, 0)
        
        self.description_splitter_widget = QWidget()
        self.description_splitter_layout = QVBoxLayout(self.description_splitter_widget)
        self.description_splitter_layout.addWidget(self.description_title)
        self.description_splitter_layout.addWidget(self.description_area_card)
        self.description_splitter_layout.setStretch(0, 1)
        self.description_splitter_layout.setStretch(1, 99)
        self.description_splitter_layout.setContentsMargins(0, 0, 0, 0)
        
        self.splitter.addWidget(self.option_splitter_widget)
        self.splitter.addWidget(self.description_splitter_widget)
        self.splitter.setSizes([90, 10])
        
        # 主布局
        self.main_layout.addWidget(self.title_widget)
        self.main_layout.addWidget(self.splitter)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

    def _init_managers(self):
        """初始化功能模块 - 各司其职"""
        # 数据管理器
        self.data_manager = OptionDataManager(self.service_coordinator)
        
        # 控件工厂
        self.widget_factory = WidgetFactory(
            self.service_coordinator,
            self.option_area_layout,
            self.icon_loader,
            self._save_current_options
        )
        
        # 嵌套选项处理器
        self.nested_handler = NestedOptionHandler(
            self.service_coordinator,
            self.option_area_layout,
            self.icon_loader,
            self.Get_Task_List,
            self._save_current_options
        )
        
        # 设备管理器
        self.device_manager = DeviceManager(self.service_coordinator)

    def _connect_signals(self):
        """连接信号"""
        self.core_signalBus.task_selected.connect(self.show_option)
        self.core_signalBus.config_changed.connect(self._on_config_changed)

    def _save_current_options(self):
        """保存当前选项 - 委托给数据管理器"""
        if not self.current_task:
            return
        
        is_resource_setting = self.current_task.item_id.startswith("r_")
        self.data_manager.save_options(
            self.current_task,
            self.option_area_layout,
            is_resource_setting
        )

    def show_option(self, item_or_id: TaskItem | ConfigItem | str):
        """显示选项 - 主入口"""
        self.reset()
        
        # 获取任务对象
        item = item_or_id
        if isinstance(item_or_id, str):
            item = self.task.get_task(item_or_id)
        if not item or not isinstance(item, TaskItem):
            return
        
        self.current_task = item
        
        # 根据任务类型显示对应的选项
        if item.item_id.startswith("r_"):
            # 资源设置任务
            # TODO: 实现资源设置选项显示
            logger.info("显示资源设置选项")
        elif item.item_id.startswith("f_"):
            # 完成后操作任务
            # TODO: 实现完成后操作选项显示
            logger.info("显示完成后操作选项")
        else:
            # 普通任务
            self._show_task_option(item)

    def _show_task_option(self, item: TaskItem):
        """显示普通任务选项
        
        使用 widget_factory 创建控件
        使用 nested_handler 处理嵌套
        """
        interface = getattr(self.task, "interface", None)
        if not interface:
            return
        
        # 查找任务模板
        target_task = None
        for task_template in interface["task"]:
            if task_template["name"] == item.name:
                target_task = task_template
                break
        
        if not target_task:
            logger.warning(f"未找到任务模板: {item.name}")
            return
        
        # 显示描述
        self._show_task_description(target_task)
        
        # 添加选项 - 委托给 widget_factory 和 nested_handler
        # TODO: 实现完整的选项添加逻辑
        logger.info(f"显示任务选项: {item.name}")

    def _show_task_description(self, task_template: dict):
        """显示任务描述"""
        descriptions = []
        
        task_description = task_template.get("description")
        if task_description:
            descriptions.append(task_description)
        
        task_doc = task_template.get("doc")
        if task_doc:
            descriptions.append(task_doc)
        
        if descriptions:
            self._toggle_description(True)
            combined_description = "\n\n---\n\n".join(descriptions)
            self.set_description(combined_description)
        else:
            self._toggle_description(False)

    def Get_Task_List(self, interface: dict, target: str):
        """获取任务选项列表"""
        lists = []
        task_config = interface["option"][target]["cases"]
        if not task_config:
            return []
        lens = len(task_config) - 1
        for i in range(lens, -1, -1):
            lists.append(task_config[i]["name"])
        lists.reverse()
        return lists

    # UI 辅助方法
    def _toggle_description(self, visible=None):
        """切换描述区域显示"""
        if visible is None:
            visible = not self.description_splitter_widget.isVisible()
        
        if visible:
            self.description_splitter_widget.show()
            self.splitter.setSizes([90, 10])
        else:
            self.description_splitter_widget.hide()
            self.splitter.setSizes([100, 0])

    def set_description(self, description: str):
        """设置描述内容"""
        import markdown
        import re
        
        self.description_content.setText("")
        html = markdown.markdown(description).replace("\n", "")
        html = re.sub(
            r"<code>(.*?)</code>",
            r"<span style='color: #009faa;'>\1</span>",
            html,
        )
        html = re.sub(
            r'(<a\s+[^>]*href="[^"]+"[^>]*)>', r'\1 style="color: #009faa;">', html
        )
        html = re.sub(r"<li><p>(.*?)</p></li>", r"<p><strong>◆ </strong>\1</p>", html)
        html = re.sub(r"<ul>(.*?)</ul>", r"\1", html)
        self.description_content.setText(html)

    def set_title(self, title: str):
        """设置标题"""
        self.title_widget.setText(title)

    def reset(self):
        """重置选项面板"""
        self._clear_options()
        self._toggle_description(visible=False)
        self.current_task = None

    def _on_config_changed(self, config_id: str):
        """配置切换时重置"""
        self.reset()

    def _clear_options(self):
        """清除所有选项"""
        def recursive_clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.hide()
                    widget.deleteLater()
                elif item.layout():
                    nested_layout = item.layout()
                    recursive_clear_layout(nested_layout)
                    if nested_layout.parent() is None:
                        del nested_layout
                elif item.spacerItem():
                    layout.removeItem(item)
        
        recursive_clear_layout(self.option_area_layout)
