from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy
from PySide6.QtCore import Qt
from qfluentwidgets import (
    MessageBoxBase,
    LineEdit,
    ComboBox,
    SubtitleLabel,
    BodyLabel,
    ToolButton,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
)
import jsonc
from app.core.Item import TaskItem, ConfigItem
from app.common.constants import PRE_CONFIGURATION, POST_ACTION
from app.common.config import cfg
from app.core.core import ServiceCoordinator
from app.common.signal_bus import signalBus


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
        # 仍保留局部弹出的错误 InfoBar，供通用对话框使用
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
        service_coordinator: ServiceCoordinator | None = None,
        parent=None,
    ):
        # 调用基类构造函数，设置标题
        super().__init__(self.tr("Add New Config"), parent)

        self.interface = interface or {}
        self._service_coordinator = service_coordinator
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

        # 组合行：下拉框 + （可选）多资源按钮
        self.resource_row_layout = QHBoxLayout()
        self.resource_row_layout.addWidget(self.resource_combo)

        # 多资源适配开启时，显示“管理/添加资源包”按钮
        self.add_bundle_button: ToolButton | None = None
        try:
            multi_res_enabled = bool(cfg.get(cfg.multi_resource_adaptation))
        except Exception:
            multi_res_enabled = False

        if multi_res_enabled:
            self.add_bundle_button = ToolButton(FIF.FOLDER_ADD, self)
            self.add_bundle_button.setSizePolicy(
                QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
            )
            self.add_bundle_button.setToolTip(self.tr("Add or manage resource bundles"))
            self.add_bundle_button.clicked.connect(self._on_add_bundle_clicked)
            self.resource_row_layout.addWidget(self.add_bundle_button)

        # 加载可用的资源包
        self.resource_bundles = resource_bundles or []
        self.load_resource_bundles(self.resource_bundles, default_resource)

        self.resource_layout.addWidget(self.resource_label)
        self.resource_layout.addLayout(self.resource_row_layout)

        # 将布局添加到对话框
        self.viewLayout.addLayout(self.name_layout)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addLayout(self.resource_layout)

        # 存储数据的变量
        self.config_name = ""
        self.resource_name = ""

    def _on_add_bundle_clicked(self):
        """打开多资源配置对话框，用于新增/选择资源包。"""
        dialog = AddBundleDialog(
            service_coordinator=self._service_coordinator, parent=self.window()
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        bundle_name, bundle_path = dialog.get_bundle_info()
        if not bundle_name or not bundle_path:
            return

        # 这里不直接写 multi_config，只把结果作为可选 bundle 返回给上层，
        # 具体落盘逻辑可以在后续多资源管理中扩展。
        new_info = {"name": bundle_name, "path": bundle_path}

        # 去重后追加
        existing_names = {
            b.get("name") for b in self.resource_bundles if isinstance(b, dict)
        }
        if bundle_name not in existing_names:
            self.resource_bundles.append(new_info)

        # 重新加载下拉框并选中新建的 bundle
        self.load_resource_bundles(self.resource_bundles, default_resource=bundle_name)

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

        # 创建 ConfigItem 对象
        if self.resource_bundles is None:
            raise ValueError("resource_bundles is None")

        # 验证所选资源包在可用列表中存在
        valid_bundle_names = {
            b.get("name") for b in self.resource_bundles if isinstance(b, dict)
        }
        if self.resource_name not in valid_bundle_names:
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

        # bundle 字段现在仅保存 bundle 名称字符串，由 ConfigService 通过主配置解析详情
        self.item = ConfigItem(
            name=self.config_name,
            item_id=ConfigItem.generate_id(),
            tasks=default_tasks,
            know_task=[],
            bundle=self.resource_name,
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


class AddBundleDialog(MessageBoxBase):
    """多资源适配时新增资源包的简单对话框（收集名称与路径，并写入主配置）。"""

    def __init__(
        self, service_coordinator: ServiceCoordinator | None = None, parent=None
    ) -> None:
        super().__init__(parent)
        self._service_coordinator = service_coordinator
        self.setWindowTitle(self.tr("Add Resource Bundle"))
        self.widget.setMinimumWidth(420)
        self.widget.setMinimumHeight(200)

        self.titleLabel = SubtitleLabel(self.tr("Add Resource Bundle"), self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(8)

        # 资源名称
        self.name_layout = QVBoxLayout()
        self.name_label = BodyLabel(self.tr("Bundle Name:"), self)
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText(self.tr("Enter the name of the bundle"))
        self.name_edit.setClearButtonEnabled(True)
        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_edit)

        # 资源路径 + 选择按钮
        self.path_layout = QHBoxLayout()
        self.path_label = BodyLabel(self.tr("Bundle Path:"), self)
        self.path_edit = LineEdit(self)
        self.path_edit.setPlaceholderText(
            self.tr("Select folder containing interface.json and resource/")
        )
        self.path_edit.setClearButtonEnabled(True)
        self.path_button = ToolButton(FIF.FOLDER, self)
        self.path_button.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.path_button.clicked.connect(self._choose_folder)

        self.path_layout.addWidget(self.path_edit)
        self.path_layout.addWidget(self.path_button)

        # 名称行：标签+输入框
        self.viewLayout.addLayout(self.name_layout)
        self.viewLayout.addSpacing(4)
        # 路径行：标签+输入框+按钮
        self.viewLayout.addWidget(self.path_label)
        self.viewLayout.addLayout(self.path_layout)

        self.yesButton.setText(self.tr("Confirm"))
        self.cancelButton.setText(self.tr("Cancel"))
        self.yesButton.clicked.connect(self._on_confirm)

        self._bundle_name: str = ""
        self._bundle_path: str = ""

    def _choose_folder(self) -> None:
        """精准选择 interface.json 文件，并预填路径和名称。"""
        from pathlib import Path as _Path

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Choose interface.json"),
            "./",
            self.tr("Interface (interface.json);;All Files (*)"),
        )
        if not file_path:
            return

        p = _Path(file_path)
        # 仅接受名为 interface.json 的文件，其它选择直接忽略（不弹错误）
        if not p.is_file() or p.name.lower() != "interface.json":
            return

        base_dir = p.parent
        self.path_edit.setText(str(base_dir))

        # 读取 interface.json 的 name 字段以预填 bundle 名称
        interface_name = ""
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = jsonc.load(f)
            iface_name = data.get("name")
            if isinstance(iface_name, str) and iface_name.strip():
                interface_name = iface_name.strip()
        except Exception:
            interface_name = ""

        current_name = self.name_edit.text().strip()
        if not current_name:
            if interface_name:
                self.name_edit.setText(interface_name)
            else:
                self.name_edit.setText("Default Bundle")

    def _on_confirm(self) -> None:
        from pathlib import Path
        import os
        from qfluentwidgets import InfoBar, InfoBarPosition

        name = self.name_edit.text().strip()
        path = self.path_edit.text().strip()

        def _show_error(msg: str) -> None:
            # 通过信号总线发送 InfoBar 通知，由主窗口统一处理
            signalBus.info_bar_requested.emit("error", msg)

        if not path:
            _show_error(self.tr("Bundle path cannot be empty"))
            return

        base = Path(path)
        if not base.exists() or not base.is_dir():
            # 选择错误：静默忽略，不弹出 InfoBar，只记录日志
            from app.utils.logger import logger as _logger

            _logger.warning("Bundle path is not a valid directory: %s", base)
            return

        # 目录：默认视为 bundle 根目录，要求其下存在 interface.json
        interface_path = base / "interface.json"
        if not interface_path.exists():
            # 选择错误：静默忽略，不弹出 InfoBar
            from app.utils.logger import logger as _logger

            _logger.warning(
                "Bundle directory does not contain interface.json: %s", base
            )
            return

        # 读取 interface.json 的 name 字段，如果存在则用于填充 bundle 名称
        interface_name = ""
        try:
            with open(interface_path, "r", encoding="utf-8") as f:
                data = jsonc.load(f)
            iface_name = data.get("name")
            if isinstance(iface_name, str) and iface_name.strip():
                interface_name = iface_name.strip()
        except Exception:
            interface_name = ""

        # 如果当前名称为空，则使用 interface.json 中的 name 或默认值
        if not name:
            if interface_name:
                name = interface_name
            else:
                name = "Default Bundle"
            self.name_edit.setText(name)

        # 统一将路径转换为相对当前工作目录的形式（尽量保持与 multi_config 中一致）
        try:
            rel = base.resolve().relative_to(Path.cwd().resolve())
            normalized = f"./{rel.as_posix()}"
        except Exception:
            normalized = os.path.abspath(str(base))

        # 写入主配置的 bundle 字典
        if not self._service_coordinator:
            _show_error(self.tr("Service is not ready, cannot save bundle"))
            return

        config_service = self._service_coordinator.config
        main_cfg = getattr(config_service, "_main_config", None)
        if main_cfg is None:
            # 尝试加载主配置
            try:
                config_service.load_main_config()
                main_cfg = getattr(config_service, "_main_config", None)
            except Exception:
                main_cfg = None
        if main_cfg is None:
            _show_error(self.tr("Main config is not available"))
            return

        bundle_dict = main_cfg.get("bundle") or {}
        if not isinstance(bundle_dict, dict):
            bundle_dict = {}

        # 不允许重复名称或重复路径
        for exist_name, value in bundle_dict.items():
            exist_path = ""
            if isinstance(value, dict):
                exist_path = str(value.get("path", ""))
            else:
                exist_path = str(value)
            if exist_name == name or (exist_path and exist_path == normalized):
                _show_error(self.tr("Bundle name or path already exists"))
                return

        bundle_dict[name] = {"name": name, "path": normalized}
        main_cfg["bundle"] = bundle_dict

        try:
            # 保存主配置
            if not config_service.save_main_config():
                _show_error(self.tr("Failed to save main config"))
                return
        except Exception as exc:
            _show_error(self.tr("Failed to save main config: ") + str(exc))
            return

        self._bundle_name = name
        self._bundle_path = normalized
        self.accept()

    def get_bundle_info(self) -> tuple[str, str]:
        return self._bundle_name, self._bundle_path
