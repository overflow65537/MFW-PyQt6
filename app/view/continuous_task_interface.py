from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel
from qfluentwidgets import SegmentedWidget ,ScrollArea
from typing import List, Dict, Optional

from ..common.maa_config_data import maa_config_data
from ..utils.logger import logger


class ContinuousTaskInterface(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("Continuous_Task_Interface")
        # 初始化滚动区域（关键新增）
        self.scroll_area = ScrollArea(self)
        self.scroll_area.setWidgetResizable(True)  # 允许内容自适应大小
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # 水平滚动条按需显示
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 禁用垂直滚动条
        
        # 导航栏放入滚动区域
        self.pivot = SegmentedWidget(self.scroll_area)
        self.scroll_area.setWidget(self.pivot)  # 设置滚动内容为导航栏
        
        # 初始化组件（关键修改：Pivot → SegmentedWidget）
        self.pivot = SegmentedWidget(self)  # 替换为SegmentedWidget
        self.stacked_widget = QStackedWidget(self)
        self.Vlayout = QVBoxLayout(self)

        # 布局调整（添加滚动区域）
        self.Vlayout.addWidget(self.scroll_area, 0, Qt.AlignmentFlag.AlignHCenter)  # 滚动区域替代原导航栏位置
        self.Vlayout.addWidget(self.stacked_widget)
        self.Vlayout.setContentsMargins(10, 10, 10, 10)
        
        # 任务页面列表（存储所有动态创建的页面）
        self.script_list: List[QWidget] = []

        
        # 信号连接（修正信号名为 currentItemChanged）
        self.pivot.currentItemChanged.connect(self._on_segmented_index_changed)  # 修改信号名
        
        # 初始化所有任务页面
        self._load_all_task_pages()

    def _on_segmented_index_changed(self, index: str):  # 参数类型应为str（routeKey）
        """SegmentedWidget索引变化时的回调（从routeKey中提取数字索引）"""
        try:
            # 从routeKey（如"task_0"）中提取数字部分
            task_index = int(index.split("_")[-1])
            self.switch_to_task_page(task_index)
        except (ValueError, IndexError):
            logger.warning(f"无效的routeKey: {index}，无法提取索引")

    def get_all_tasks(self) -> List[Dict]:
        """直接获取所有任务数据（无需过滤）"""
        return maa_config_data.interface_config.get("task", [])

    def _load_all_task_pages(self) -> None:
        """加载所有任务页面（根据实际任务数量动态创建）"""
        tasks = self.get_all_tasks()
        if not tasks:
            logger.warning("未找到任何任务数据")
            return

        for idx, task in enumerate(tasks):
            self._create_task_page(task, idx)
        
        # 初始显示第一个任务页面
        if self.script_list:
            self.switch_to_task_page(0)

    def _create_task_page(self, task: Dict, task_index: int) -> None:
        """创建单个任务页面并关联导航项（调整导航项添加逻辑）"""
        # 创建任务详情页面（与原逻辑一致）
        task_page = self.TaskDetailPage(task, self)
        task_page.setObjectName(f"task_{task_index}")
        
        # 更新页面列表和容器（与原逻辑一致）
        self.script_list.append(task_page)
        self.stacked_widget.addWidget(task_page)
        
        # 添加导航项时优化样式（可选但推荐）
        task_name = task.get("name", f"任务{task_index+1}")
        self.pivot.addItem(routeKey=f"task_{task_index}", text=task_name)
        # 调整导航项样式（通过 CSS 选择器定位内部按钮）
        self.pivot.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;  /* 缩小左右边距 */
                font-size: 12px;   /* 缩小字体 */
                min-width: 60px;   /* 限制最小宽度避免文字截断 */
            }
        """)

    def switch_to_task_page(self, task_index: int) -> None:
        """切换到指定索引的任务页面（索引从0开始）"""
        if not self.script_list or task_index < 0 or task_index >= len(self.script_list):
            logger.warning(f"无效的任务索引: {task_index}")
            return

        # 切换导航栏选中状态
        target_route_key = self.script_list[task_index].objectName()
        self.pivot.setCurrentItem(target_route_key)
        
        # 切换页面显示
        self.stacked_widget.setCurrentWidget(self.script_list[task_index])

    class TaskDetailPage(QWidget):
        """任务详情页面（显示具体任务信息）"""
        def __init__(self, task: Dict, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self.Vlayout = QVBoxLayout(self)
            self.Vlayout.setContentsMargins(15, 15, 15, 15)
            self.Vlayout.setSpacing(10)
            
            # 动态添加任务信息展示（根据实际字段扩展）
            name_label = QLabel(f"任务名称: {task.get('name', '未命名任务')}", self)
            name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.Vlayout.addWidget(name_label)

            entry_label = QLabel(f"入口: {task.get('entry', '无')}", self)
            self.Vlayout.addWidget(entry_label)

            periodic = task.get("periodic", 0)
            periodic_label = QLabel(f"周期: {periodic}天" if periodic else "无固定周期", self)
            self.Vlayout.addWidget(periodic_label)

            daily_start = task.get("daily_start", 0)
            daily_start_label = QLabel(f"每日开始时间: {daily_start}:00", self)
            self.Vlayout.addWidget(daily_start_label)

            # 可根据需要添加更多字段（如description等）
            # description_label = QLabel(f"描述: {task.get('description', '无')}", self)
            # self.Vlayout.addWidget(description_label)