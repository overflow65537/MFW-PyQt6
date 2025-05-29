#   This file is part of MFW-ChainFlow Assistant.

#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.

#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 工具任务界面
作者:overflow65537
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QStackedWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
)
from PySide6.QtGui import QWheelEvent, QFont, QColor

from qfluentwidgets import (
    Pivot,
    ScrollArea,
    BodyLabel,
    ComboBox,
    PushButton,
)

from typing import List, Optional, Dict
import re

from datetime import datetime


from ..common.maa_config_data import (
    maa_config_data,
)
from ..common.typeddict import (
    TaskItem_interface,
    InterfaceData,
)
from ..utils.logger import logger
from ..utils.tool import Get_Task_List

from ..common.signal_bus import signalBus


class HorizontalScrollArea(ScrollArea):
    def wheelEvent(self, event: QWheelEvent):

        delta = event.angleDelta().y()
        h_bar = self.horizontalScrollBar()
        h_bar.setValue(h_bar.value() - delta)
        event.accept()


class AssistToolTaskInterface(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("Assist_Tool_Task_Interface")
        # 新增：魔法变量存储当前页面信息（索引+实例）
        self.current_page_info: Optional[Dict[str, TaskDetailPage]] = None

        self.pivot = Pivot(self)
        self.scroll_area = HorizontalScrollArea(self)
        self.scroll_area.setWidget(self.pivot)
        self.scroll_area.enableTransparentBackground()
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        # 下方水平布局（左边垂直布局包裹堆叠组件+按钮 + 右边滚动区域）
        self.bottom_h_layout = QHBoxLayout()

        # 左边垂直布局（堆叠组件 + 按钮）
        self.stacked_v_layout = QVBoxLayout()
        # 堆叠组件
        self.stacked_widget = QStackedWidget(self)
        self.stacked_v_layout.addWidget(self.stacked_widget, 1)

        self.S2_Button = PushButton(self.tr("start"), self)
        self.S2_Button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.stacked_v_layout.addWidget(self.S2_Button, 0)

        self.bottom_h_layout.addLayout(self.stacked_v_layout, 3)

        self.right_scroll_area = ScrollArea(self)
        self.right_scroll_area.setWidgetResizable(True)
        self.right_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.right_scroll_area.setStyleSheet("background: transparent; border: none;")

        self.content_widget = QWidget()
        self.right_scroll_area.setWidget(self.content_widget)

        self.right_layout = QVBoxLayout(self.content_widget)
        self.bottom_h_layout.addWidget(self.right_scroll_area, 2)

        self.Vlayout = QVBoxLayout(self)
        self.Vlayout.addWidget(self.scroll_area, 0)
        self.Vlayout.addLayout(self.bottom_h_layout, 1)

        self.pivot.currentItemChanged.connect(self._on_segmented_index_changed)
        self.S2_Button.clicked.connect(self._on_add_task_button_clicked)
        signalBus.task_output_sync.connect(self.sync_taskoutput)
        self.script_list: List[TaskDetailPage] = []
        self._load_all_task_pages()

    def reinitialize(self):
        """重新初始化界面"""
        # 清空现有页面
        while self.stacked_widget.count():
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        self.pivot.clear()
        self.script_list = []
        self.current_page_info = None

        # 清空右侧滚动区域
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.right_layout.addStretch()

        # 重新加载所有任务页面
        self._load_all_task_pages()

    def sync_taskoutput(self, data_dict: dict):
        if data_dict.get("type", "") == "task_output_add":
            self.insert_colored_text(
                data_dict.get("msg", {}).get("text"),
                data_dict.get("msg", {}).get("color"),
            )
            self.S2_Button.setEnabled(True)
        elif data_dict.get("type", "") == "task_output_clear":
            self.clear_layout()
        elif data_dict.get("type", "") == "reinit":
            self.reinitialize()
        elif data_dict.get("type", "") == "change_button":
            print(data_dict)
            self.S2_Button.setEnabled(data_dict.get("status", False))
            if data_dict.get("text", "") == "Start":
                self.S2_Button.setText(self.tr("start"))
                self.S2_Button.clicked.disconnect()
                self.S2_Button.clicked.connect(self._on_add_task_button_clicked)
            elif data_dict.get("text", "") in ["Stop", "停止"]:
                self.S2_Button.setText(self.tr("stop"))
                self.S2_Button.clicked.disconnect()
                self.S2_Button.clicked.connect(self.stop_task)

    def insert_colored_text(self, text, color_name="black"):
        """
        插入带颜色的文本
        """

        message = BodyLabel(self)
        # 初始化 HTML 文本
        html_text = text

        # 解析颜色
        if "[color:" in html_text:
            html_text = re.sub(
                r"\[color:(.*?)\]", r'<span style="color:\1">', html_text
            )
            html_text = re.sub(r"\[/color\]", "</span>", html_text)
        else:
            color = QColor(color_name)
            if not color.isValid():
                color_name = "black"
            message.setTextColor(QColor(color_name))

        # 解析字号
        html_text = re.sub(
            r"\[size:(.*?)\]", r'<span style="font-size:\1px">', html_text
        )
        html_text = re.sub(r"\[/size\]", "</span>", html_text)

        # 解析粗体
        html_text = html_text.replace("[b]", "<b>").replace("[/b]", "</b>")

        # 解析斜体
        html_text = html_text.replace("[i]", "<i>").replace("[/i]", "</i>")

        # 解析下划线
        html_text = html_text.replace("[u]", "<u>").replace("[/u]", "</u>")

        # 解析删除线
        html_text = html_text.replace("[s]", "<s>").replace("[/s]", "</s>")

        html_text = re.sub(
            r"\[align:left\]", '<div style="text-align: left;">', html_text
        )
        html_text = re.sub(
            r"\[align:center\]", '<div style="text-align: center;">', html_text
        )
        html_text = re.sub(
            r"\[align:right\]", '<div style="text-align: right;">', html_text
        )
        html_text = re.sub(r"\[/align\]", "</div>", html_text)

        # 将换行符替换为 <br>
        html_text = html_text.replace("\n", "<br>")

        now = datetime.now().strftime("%H:%M")

        html_text = f'<span style="color:gray">{now}</span> {html_text}'

        message.setWordWrap(True)
        message.setText(html_text)
        message.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )  # 水平扩展，垂直自适应

        # 插入到布局
        count = self.right_layout.count()
        if count >= 2:
            # 插入到倒数第二个位置（避开最后的stretch）
            self.right_layout.insertWidget(count - 1, message)
        else:
            # 插入到第一个位置
            self.right_layout.insertWidget(0, message)

        QTimer.singleShot(
            10,
            lambda: self.right_scroll_area.verticalScrollBar().setValue(
                self.right_scroll_area.verticalScrollBar().maximum()
            ),
        )

    def clear_layout(self):
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.right_layout.addStretch()

    def _on_add_task_button_clicked(self):
        """添加任务按钮点击事件"""
        if not self.current_page_info:
            logger.warning("当前无选中页面")
            return

        # 通过魔法变量获取当前页面实例和索引
        current_page = self.current_page_info["page"]

        # 使用当前页面实例调用方法（如获取选中选项）
        send_dict = {}
        send_dict["entry"] = current_page.get_entry()
        send_dict["pipeline_override"] = current_page.get_pipeline_override()

        signalBus.run_sp_task.emit(send_dict)
        self.S2_Button.setEnabled(False)
        self.S2_Button.setText(self.tr("stop"))
        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.stop_task)

    def stop_task(self):
        signalBus.task_output_sync.emit({"type": "stoptask"})
        self.S2_Button.setEnabled(True)
        self.S2_Button.setText(self.tr("start"))
        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self._on_add_task_button_clicked)

    def _on_segmented_index_changed(self, index: str):
        """导航栏索引变化时"""
        try:
            task_index = int(index.split("_")[-1])
            self.switch_to_task_page(task_index)
        except (ValueError, IndexError):
            logger.warning(f"无效的routeKey: {index}，无法提取索引")

    def _load_all_task_pages(self) -> None:
        """加载所有任务页面"""
        tasks = maa_config_data.interface_config.get("task", [])
        if not tasks:
            logger.warning("未找到任何任务数据")
            return

        filtered_idx = 0
        for task in tasks:
            if task.get("spt"):
                self._create_task_page(task, filtered_idx)
                filtered_idx += 1
        if filtered_idx == 0:
            logger.warning("没有可用的SPT任务")
            QTimer.singleShot(500, lambda: signalBus.show_AssistTool_task.emit(False))
        else:
            signalBus.show_AssistTool_task.emit(True)

        # 初始显示第一个任务页面
        if self.script_list:
            self.switch_to_task_page(0)

    def _create_task_page(self, task: TaskItem_interface, task_index: int) -> None:
        """创建单个任务页面并关联导航项"""
        self.task_page = TaskDetailPage(task, self)
        self.task_page.setObjectName(f"task_{task_index}")
        self.script_list.append(self.task_page)
        self.stacked_widget.addWidget(self.task_page)

        task_name = task.get("name", f"任务{task_index+1}")

        self.pivot.addItem(
            routeKey=f"task_{task_index}",
            text=task_name,
        )

    def switch_to_task_page(self, task_index: int) -> None:
        """切换到指定索引的任务页面"""
        if (
            not self.script_list
            or task_index < 0
            or task_index >= len(self.script_list)
        ):
            logger.warning(f"无效的任务索引: {task_index}")
            return

        # 切换导航栏选中状态
        target_route_key = self.script_list[task_index].objectName()
        self.pivot.setCurrentItem(target_route_key)

        # 切换页面显示
        self.stacked_widget.setCurrentWidget(self.script_list[task_index])

        # 新增：更新当前页面信息（存储索引和页面实例）
        self.current_page_info = {
            "page": self.script_list[task_index]  # TaskDetailPage 实例
        }


class TaskDetailPage(QWidget):
    """任务详情页面（显示具体任务信息）"""

    def __init__(self, task: TaskItem_interface, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.task = task

        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

        self.scroll_area_content = QWidget()
        self.scroll_area_content.setContentsMargins(0, 0, 10, 0)

        # 选项区域
        self.option_widget = QWidget()
        self.option_layout = QVBoxLayout(self.option_widget)
        self.option_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,  # 水平策略保持不变
            QSizePolicy.Policy.Minimum,  # 垂直策略根据内容自动调整
        )

        # doc区域
        self.doc_widget = QWidget()
        self.doc_layout = QVBoxLayout(self.doc_widget)
        self.doc_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,  # 水平策略保持不变
            QSizePolicy.Policy.Minimum,  # 垂直策略根据内容自动调整
        )

        # 主滚动区域布局
        self.main_scroll_layout = QVBoxLayout(self.scroll_area_content)
        self.main_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_scroll_layout.addWidget(self.option_widget)
        self.main_scroll_layout.addWidget(self.doc_widget)

        self.scroll_area.setWidget(self.scroll_area_content)

        self.Option_area_Label = QVBoxLayout()
        self.Option_area_Label.addWidget(self.scroll_area, 1)

        self.setLayout(self.Option_area_Label)
        # 填充任务区数据和文本

        self.show_task_options(task.get("name", ""), maa_config_data.interface_config)

    def resizeEvent(self, event):
        """
        当窗口大小改变时，重新设置所有 任务选项下拉框和doc 的宽度。
        """
        super().resizeEvent(event)
        scroll_area_width = self.scroll_area.width()
        for i in range(self.option_layout.count()):
            layout = self.option_layout.itemAt(i).layout()
            if layout is not None:
                for j in range(layout.count()):
                    # 检查 item 是否为 None
                    item = layout.itemAt(j)
                    if item is not None:
                        widget = item.widget()
                        if isinstance(widget, ComboBox):
                            widget.setFixedWidth(scroll_area_width - 20)
                        if isinstance(widget, BodyLabel):
                            widget.setFixedWidth(scroll_area_width - 20)

    def show_task_options(self, select_target: str, MAA_Pi_Config: InterfaceData):
        """展示任务选项和文档"""

        option_layout = self.option_layout
        doc_layout = self.doc_layout

        for task in MAA_Pi_Config.get("task", []):
            if task.get("name") == select_target:
                # 处理 option 字段
                options = task.get("option")
                if options:
                    for option in options:
                        v_layout = QVBoxLayout()

                        label = BodyLabel(self)
                        label.setText(option)
                        label.setFont(QFont("Arial", 10))
                        v_layout.addWidget(label)

                        select_box = ComboBox(self)
                        select_box.addItems(
                            list(
                                Get_Task_List(
                                    maa_config_data.interface_config_path, option
                                )
                            )
                        )
                        select_box.setSizePolicy(
                            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                        )
                        scroll_area_width = self.scroll_area.width()
                        select_box.setFixedWidth(scroll_area_width - 20)

                        v_layout.addWidget(select_box)

                        option_layout.addLayout(v_layout)
                # 处理 doc 字段
                doc = task.get("doc")
                if doc:
                    if isinstance(doc, list):
                        doc = "\n".join(doc)
                    doc_label = BodyLabel(self)
                    doc_label.setWordWrap(True)

                    # 初始化 HTML 文本
                    html_text = doc

                    # 解析颜色
                    html_text = re.sub(
                        r"\[color:(.*?)\]", r'<span style="color:\1">', html_text
                    )
                    html_text = re.sub(r"\[/color\]", "</span>", html_text)

                    # 解析字号
                    html_text = re.sub(
                        r"\[size:(.*?)\]", r'<span style="font-size:\1px">', html_text
                    )
                    html_text = re.sub(r"\[/size]", "</span>", html_text)

                    # 解析粗体
                    html_text = html_text.replace("[b]", "<b>").replace("[/b]", "</b>")

                    # 解析斜体
                    html_text = html_text.replace("[i]", "<i>").replace("[/i]", "</i>")

                    # 解析下划线
                    html_text = html_text.replace("[u]", "<u>").replace("[/u]", "</u>")

                    # 解析删除线
                    html_text = html_text.replace("[s]", "<s>").replace("[/s]", "</s>")

                    # 解析对齐方式
                    html_text = re.sub(
                        r"\[align:left\]", '<div style="text-align: left;">', html_text
                    )
                    html_text = re.sub(
                        r"\[align:center\]",
                        '<div style="text-align: center;">',
                        html_text,
                    )
                    html_text = re.sub(
                        r"\[align:right\]",
                        '<div style="text-align: right;">',
                        html_text,
                    )
                    html_text = re.sub(r"\[/align\]", "</div>", html_text)

                    # 将换行符替换为 <br>
                    html_text = html_text.replace("\n", "<br>")

                    doc_label.setText(html_text)
                    doc_layout.addWidget(doc_label)

                spacer = QSpacerItem(
                    0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                self.main_scroll_layout.addItem(spacer)

                break

    def get_selected_options(self):
        """获取所有选中的选项"""
        selected_options = []
        layout = self.option_layout
        name = None
        selected_value = None
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not isinstance(item, QVBoxLayout):
                continue  # 如果item不是QVBoxLayout，跳过本次循环
            for j in range(item.count()):
                widget = item.itemAt(j).widget()
                if isinstance(widget, BodyLabel):
                    name = widget.text()
                elif isinstance(widget, ComboBox):
                    selected_value = widget.currentText()
            if name and selected_value:
                selected_options.append({"name": name, "value": selected_value})

            # 重置变量
            name = None
            selected_value = None

        return selected_options

    def get_task(self):
        """获取当前选中任务的信息"""
        name = self.task.get("name")
        option = self.get_selected_options()
        return {"name": name, "option": option}

    def get_entry(self):
        """获取当前选中任务的入口名称"""
        return self.task.get("entry")

    def get_pipeline_override(self) -> dict:
        """获取任务的pipeline_override配置项"""
        override_options = {}
        task_list = self.get_task()

        # 找到task的entry
        enter_index = 0
        for index, task_enter in enumerate(
            maa_config_data.interface_config.get("task", [])
        ):
            if task_enter.get("name", "M1") == task_list.get("name", "M2"):
                self.entry = task_enter.get("entry")
                enter_index = index
                break
        # 解析task中的pipeline_override
        if maa_config_data.interface_config.get("task", [])[enter_index].get(
            "pipeline_override", False
        ):
            update_dict = maa_config_data.interface_config.get("task", [])[
                enter_index
            ].get("pipeline_override", {})
            override_options.update(update_dict)
        # 解析task中的option
        if task_list["option"] != []:
            for task_option in task_list["option"]:
                for override in maa_config_data.interface_config.get("option", [])[
                    task_option["name"]
                ]["cases"]:
                    if override["name"] == task_option["value"]:

                        override_options.update(override.get("pipeline_override", {}))
        return override_options
