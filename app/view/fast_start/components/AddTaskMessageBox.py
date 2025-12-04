from PySide6.QtWidgets import QVBoxLayout
from qfluentwidgets import (
    MessageBoxBase,
    LineEdit,
    ComboBox,
    SubtitleLabel,
    BodyLabel,
)
from app.core.Item import TaskItem, ConfigItem
from app.common.constants import PRE_CONFIGURATION, POST_ACTION


class BaseAddDialog(MessageBoxBase):
    """添加类对话框的基类"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        # 设置对话框标题和大小
        self.titleLabel = SubtitleLabel(title, self)
        self.widget.setMinimumWidth(400)
        self.widget.setMinimumHeight(180)

        # 存储返回的项
        self.item = None

        # 连接确认按钮信号
        self.yesButton.clicked.connect(self.on_confirm)
        self.cancelButton.clicked.connect(self.on_cancel)

        # 设置按钮文本
        self.yesButton.setText(self.tr("Confirm"))
        self.cancelButton.setText(self.tr("Cancel"))

        # 添加标题到布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(10)

    def on_confirm(self):
        """确认添加"""
        pass

    def on_cancel(self):
        """取消添加"""
        self.item = None
        self.reject()

    def show_error(self, message):
        """显示错误信息"""
        from qfluentwidgets import InfoBar, InfoBarPosition
        from PySide6.QtCore import Qt

        InfoBar.error(
            title=self.tr("Error"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self.parent(),
        )


class AddConfigDialog(BaseAddDialog):
    def __init__(
        self,
        resource_bundles: list | None = None,
        default_resource: str | None = None,
        interface: dict | None = None,
        parent=None,
    ):
        # 调用基类构造函数，设置标题
        super().__init__(self.tr("Add New Config"), parent)

        self.interface = interface or {}
        # 配置名输入框
        self.name_layout = QVBoxLayout()
        self.name_label = BodyLabel(self.tr("Config Name:"), self)
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText(self.tr("Enter the name of the config"))
        self.name_edit.setClearButtonEnabled(True)

        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_edit)

        # 资源包下拉框
        self.resource_layout = QVBoxLayout()
        self.resource_label = BodyLabel(self.tr("Resource Bundle:"), self)
        self.resource_combo = ComboBox(self)

        # 加载可用的资源包
        self.resource_bundles = resource_bundles
        self.load_resource_bundles(resource_bundles, default_resource)

        self.resource_layout.addWidget(self.resource_label)
        self.resource_layout.addWidget(self.resource_combo)

        # 将布局添加到对话框
        self.viewLayout.addLayout(self.name_layout)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addLayout(self.resource_layout)

        # 存储数据的变量
        self.config_name = ""
        self.resource_name = ""

    def load_resource_bundles(self, resource_bundles, default_resource):
        """加载可用的资源包到下拉框"""
        # 使用传入的资源包列表
        if resource_bundles:
            # 清空下拉框
            self.resource_combo.clear()
            resource_bundles_name = [bundle["name"] for bundle in resource_bundles]
            self.resource_combo.addItems(resource_bundles_name)
            # 如果有默认资源包，选中它
            if default_resource and default_resource in resource_bundles_name:
                index = self.resource_combo.findText(default_resource)
                if index >= 0:
                    self.resource_combo.setCurrentIndex(index)

    def on_confirm(self):
        """确认添加配置"""
        self.config_name = self.name_edit.text().strip()
        self.resource_name = self.resource_combo.currentText()

        # 验证输入
        if not self.config_name:
            self.show_error(self.tr("Config name cannot be empty"))
            return

        if self.config_name.lower() == "default":
            self.show_error(self.tr("Cannot use 'default' as config name"))
            return

        # 创建 ConfigItem 对象，使用新的 core.model 数据结构
        if self.resource_bundles is None:
            raise ValueError("resource_bundles is None")
        bundle_path = ""
        for bundle in self.resource_bundles:
            if bundle["name"] == self.resource_name:
                bundle_path = bundle["path"]
                break
        if not bundle_path:
            self.show_error(self.tr("Resource bundle not found"))
            return
        init_controller = self.interface["controller"][0]["name"]
        init_resource = self.interface["resource"][0]["name"]
        # 仅为配置创建所需的基础任务:资源 与 完成后操作
        default_tasks = [
            TaskItem(
                name="Pre-Configuration",
                item_id=PRE_CONFIGURATION,
                is_checked=True,
                task_option={
                    "controller_type": init_controller,
                    "resource": init_resource,
                },
                is_special=False,  # 基础任务，不是特殊任务
            ),
            TaskItem(
                name="Post-Action",
                item_id=POST_ACTION,
                is_checked=True,
                task_option={},
                is_special=False,  # 基础任务，不是特殊任务
            ),
        ]

        # bundle 字段期望为 Dict[str, Dict[str, Any]]，这里使用 resource_name 作为 key
        self.item = ConfigItem(
            name=self.config_name,
            item_id=ConfigItem.generate_id(),
            tasks=default_tasks,
            know_task=[],
            bundle={
                self.resource_name: {"name": self.resource_name, "path": bundle_path}
            },
        )

        # 接受对话框
        self.accept()

    def get_config_item(self):
        """获取创建的配置项对象"""
        return self.item


class AddTaskDialog(BaseAddDialog):
    def __init__(
        self,
        task_map: dict[str, dict[str, dict]],
        interface: dict | None = None,
        parent=None,
    ):
        # 调用基类构造函数，设置标题
        super().__init__(self.tr("Add New Task"), parent)

        # 任务名下拉框
        self.task_layout = QVBoxLayout()
        self.task_label = BodyLabel(self.tr("Task Name:"), self)
        self.task_combo = ComboBox(self)

        # 加载可用的任务名
        self.task_names = list(task_map.keys())
        self.task_map = task_map
        self.interface = interface or {}
        self.load_task_names(self.task_names)

        self.task_layout.addWidget(self.task_label)
        self.task_layout.addWidget(self.task_combo)

        # 将布局添加到对话框
        self.viewLayout.addLayout(self.task_layout)

        # 存储数据的变量
        self.task_name = ""
        self.task_type = "task"

    def load_task_names(self, task_names):
        """加载可用的任务名到下拉框（显示label，存储name）

        注意：保留 $ 前缀，它用于国际化标记
        """
        if task_names:
            # 清空下拉框
            self.task_combo.clear()

            # 构建显示文本（label）到任务名（name）的映射
            self.display_to_name = {}
            display_labels = []

            for task_name in task_names:
                # 在 interface 中查找对应的 label
                display_label = task_name  # 默认使用 name
                if self.interface:
                    for task in self.interface.get("task", []):
                        if task["name"] == task_name:
                            display_label = task.get(
                                "label", task.get("name", task_name)
                            )
                            break

                display_labels.append(display_label)
                self.display_to_name[display_label] = task_name

            self.task_combo.addItems(display_labels)

    def on_confirm(self):
        """确认添加任务"""
        # 获取选中的显示文本
        selected_label = self.task_combo.currentText().strip()

        # 通过映射获取真实的任务名称（name）
        self.task_name = self.display_to_name.get(selected_label, selected_label)

        # 验证输入
        if not self.task_name:
            self.show_error(self.tr("Task name cannot be empty"))
            return

        # 检查任务是否为特殊任务
        is_special = False
        if self.interface:
            for task in self.interface.get("task", []):
                if task["name"] == self.task_name:
                    is_special = task.get("spt", False)
                    break

        # 创建 TaskItem 对象，匹配 core.TaskItem 数据结构
        task_option = (
            self.task_map.get(self.task_name, {})
            if isinstance(self.task_map, dict)
            else {}
        )
        self.item = TaskItem(
            name=self.task_name,
            item_id=TaskItem.generate_id(is_special=is_special),
            is_checked=not is_special,  # 特殊任务默认不选中
            task_option=task_option,
            is_special=is_special,
        )

        # 接受对话框
        self.accept()

    def get_task_item(self):
        """获取创建的任务项对象"""
        return self.item
