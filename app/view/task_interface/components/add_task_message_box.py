from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, QEasingCurve, QEvent
from qfluentwidgets import (
    MessageBoxBase,
    LineEdit,
    ComboBox,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    StrongBodyLabel,
    InfoBar,
    InfoBarPosition,
    ScrollArea,
    SimpleCardWidget,
    FlowLayout,
    TogglePushButton,
    SwitchButton,
    TextEdit,
)
import jsonc
from app.common.fluent_tooltip import apply_fluent_tooltip
from app.core.item import TaskItem, ConfigItem
from app.common.constants import _RESOURCE_, _CONTROLLER_, _SETTING_, POST_ACTION
from app.common.config import cfg
from app.core.core import ServiceCoordinator
from app.core.builtin_task_loader import BUILTIN_TASK_GROUP_NAME
from app.core.service.i18n_service import I18nService
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
        self.name_edit.setPlaceholderText(
            self.tr("Enter name, or leave empty for auto (preset name + index)")
        )
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

        # 注意：添加 bundle 功能已移至 Bundle 管理界面

        # 加载可用的资源包
        self.resource_bundles = resource_bundles or []
        self.load_resource_bundles(self.resource_bundles, default_resource)
        self.resource_combo.currentIndexChanged.connect(self._on_bundle_changed)

        self.resource_layout.addWidget(self.resource_label)
        self.resource_layout.addLayout(self.resource_row_layout)

        # 预设配置下拉框
        self.preset_layout = QVBoxLayout()
        self.preset_label = BodyLabel(self.tr("Preset:"), self)
        self.preset_combo = ComboBox(self)
        self._presets: list[dict] = []
        self._selected_preset_name: str | None = None
        self._load_presets()

        self.preset_layout.addWidget(self.preset_label)
        self.preset_layout.addWidget(self.preset_combo)

        # 导入分享配置
        self.import_layout = QVBoxLayout()
        import_row = QHBoxLayout()
        self.import_label = BodyLabel(self.tr("Import shared config:"), self)
        self.import_switch = SwitchButton(self)
        self.import_switch.setOffText(self.tr("Off"))
        self.import_switch.setOnText(self.tr("On"))
        import_row.addWidget(self.import_label)
        import_row.addStretch()
        import_row.addWidget(self.import_switch)
        self.import_layout.addLayout(import_row)

        self.import_edit = TextEdit(self)
        self.import_edit.setPlaceholderText(
            self.tr("Paste shared config content here")
        )
        self.import_edit.setMinimumHeight(100)
        self.import_edit.setMaximumHeight(160)
        self.import_edit.hide()
        self.import_layout.addWidget(self.import_edit)
        self.import_switch.checkedChanged.connect(self._on_import_switch_changed)

        # 将布局添加到对话框
        self.viewLayout.addLayout(self.name_layout)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addLayout(self.resource_layout)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addLayout(self.preset_layout)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addLayout(self.import_layout)

        # 存储数据的变量
        self.config_name = ""
        self.resource_name = ""
        self._shared_tasks: list | None = None
        self._share_version_mismatch: tuple[str, str] | None = None


    def _resolve_selected_bundle_version(self) -> str:
        bundle = self._resolve_selected_bundle_info()
        if not bundle:
            return ""
        from app.utils.config_share import load_bundle_interface
        from app.utils.version_policy import resource_version_from_interface

        path = str(bundle.get("path", "./") or "./")
        interface = load_bundle_interface(path)
        return resource_version_from_interface(interface)

    def _on_import_switch_changed(self, checked: bool):
        """切换分享配置导入模式。"""
        self.import_edit.setVisible(checked)
        self.preset_combo.setEnabled(not checked)
        self.preset_label.setEnabled(not checked)
        if checked:
            self.widget.setMinimumHeight(380)
        else:
            self.widget.setMinimumHeight(180)
            self.import_edit.clear()

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

    def _load_presets(self):
        """根据当前选中的 bundle 重新加载预设配置到下拉框。"""
        previous_text = self.preset_combo.currentText().strip()
        self.preset_combo.clear()
        self._presets = []
        self._selected_preset_name = None

        # 默认选项：不使用预设
        default_label = self.tr("Default (all tasks)")
        self.preset_combo.addItem(default_label)

        presets = self._load_presets_for_selected_bundle()
        if isinstance(presets, list):
            self._presets = presets
            for preset in presets:
                if not isinstance(preset, dict):
                    continue
                display_name = preset.get("label") or preset.get("name", "")
                if display_name:
                    self.preset_combo.addItem(display_name)
        if previous_text:
            idx = self.preset_combo.findText(previous_text)
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)

    def _on_bundle_changed(self, _index: int) -> None:
        self._load_presets()

    def _resolve_selected_bundle_info(self) -> dict | None:
        selected_bundle_name = self.resource_combo.currentText().strip()
        if not selected_bundle_name:
            return None
        for bundle in self.resource_bundles or []:
            if isinstance(bundle, dict) and str(bundle.get("name", "")).strip() == selected_bundle_name:
                return bundle
        return None

    def _load_presets_for_selected_bundle(self) -> list[dict]:
        bundle = self._resolve_selected_bundle_info()
        if not bundle:
            return []

        bundle_path = str(bundle.get("path", "./") or "./")
        interface_dir = Path(bundle_path) if Path(bundle_path).is_absolute() else Path.cwd() / bundle_path
        interface_path = None
        for candidate in [interface_dir / "interface.jsonc", interface_dir / "interface.json"]:
            if candidate.exists():
                interface_path = candidate
                break
        if interface_path is None:
            return []

        try:
            with open(interface_path, "r", encoding="utf-8") as f:
                bundle_interface = jsonc.load(f)
        except Exception:
            return []

        language = "zh_cn"
        if self._service_coordinator:
            try:
                language = self._service_coordinator.interface_obj.get_current_language()
            except Exception:
                pass

        i18n_service = I18nService(language=language)
        i18n_service.load_translations_from_interface(bundle_interface, interface_dir)
        translated_interface = i18n_service.translate_any(bundle_interface)
        presets = translated_interface.get("preset", [])
        return presets if isinstance(presets, list) else []

    def _existing_config_display_names(self) -> set[str]:
        names: set[str] = set()
        if not self._service_coordinator:
            return names
        try:
            for entry in self._service_coordinator.config.list_configs():
                n = entry.get("name")
                if isinstance(n, str) and n.strip():
                    names.add(n.strip())
        except Exception:
            pass
        return names

    def _allocate_config_display_name(self, base: str, used: set[str]) -> str | None:
        """在 base 后接序号，生成不与已有配置重名的显示名（第几份）。"""
        base = (base or "").strip()
        if not base:
            base = self.tr("Config")
        if base.lower() == "default":
            base = self.tr("Config")
        for i in range(1, 10000):
            candidate = self.tr("{0} {1}").format(base, i)
            if candidate.lower() == "default":
                continue
            if candidate not in used:
                return candidate
        return None

    def on_confirm(self):
        """确认添加配置"""
        self._shared_tasks = None
        self._share_version_mismatch = None
        self.config_name = self.name_edit.text().strip()
        self.resource_name = self.resource_combo.currentText()

        if self.import_switch.isChecked():
            from app.utils.config_share import (
                ConfigShareError,
                ConfigShareResourceError,
                decode_share_payload,
                validate_share_for_import,
            )

            raw = self.import_edit.toPlainText().strip()
            if not raw:
                self.show_error(self.tr("Please paste shared config content"))
                return
            try:
                payload = decode_share_payload(raw)
            except ConfigShareError:
                self.show_error(self.tr("Invalid shared config content"))
                return
            except Exception:
                self.show_error(self.tr("Invalid shared config content"))
                return
            if not payload.tasks:
                self.show_error(self.tr("Shared config contains no tasks"))
                return

            target_bundle = self.resource_name.strip()
            if not target_bundle:
                self.show_error(self.tr("Please select a resource bundle"))
                return

            try:
                self._share_version_mismatch = validate_share_for_import(
                    payload,
                    target_bundle=target_bundle,
                    target_resource_version=self._resolve_selected_bundle_version(),
                )
            except ConfigShareResourceError as exc:
                self.show_error(
                    self.tr(
                        "Resource mismatch: shared config is for \"{0}\", "
                        "but you selected \"{1}\"."
                    ).format(exc.shared_bundle, exc.target_bundle)
                )
                return
            except ConfigShareError:
                self.show_error(self.tr("Invalid shared config content"))
                return

            self._shared_tasks = payload.tasks
            self._selected_preset_name = None
            selected_preset_dict = None
        else:
            preset_index = self.preset_combo.currentIndex()
            selected_preset_dict = None
            if preset_index > 0 and preset_index - 1 < len(self._presets):
                raw = self._presets[preset_index - 1]
                selected_preset_dict = raw if isinstance(raw, dict) else None
                raw_nm = selected_preset_dict.get("name") if selected_preset_dict else None
                self._selected_preset_name = (
                    raw_nm.strip()
                    if isinstance(raw_nm, str) and raw_nm.strip()
                    else None
                )
            else:
                self._selected_preset_name = None

        if not self.config_name:
            used = self._existing_config_display_names()
            if selected_preset_dict:
                base = (
                    selected_preset_dict.get("label")
                    or selected_preset_dict.get("name")
                    or self._selected_preset_name
                )
                base = str(base).strip() if base is not None else ""
                if not base and self._selected_preset_name:
                    base = str(self._selected_preset_name).strip()
                if not base:
                    base = self.tr("Config")
            else:
                base = self.tr("New Config")
            allocated = self._allocate_config_display_name(base, used)
            if not allocated:
                self.show_error(self.tr("Could not allocate a unique config name"))
                return
            self.config_name = allocated
            self.name_edit.setText(self.config_name)

        if self.config_name.lower() == "default":
            self.show_error(self.tr("Cannot use 'default' as config name"))
            return

        # 创建 ConfigItem 对象
        if self.resource_bundles is None:
            raise ValueError("resource_bundles is None")

        # 验证所选资源包在可用列表中存在，并获取 bundle 信息
        selected_bundle = None
        for bundle in self.resource_bundles:
            if isinstance(bundle, dict) and bundle.get("name") == self.resource_name:
                selected_bundle = bundle
                break
        
        if not selected_bundle:
            self.show_error(self.tr("Resource bundle not found"))
            return
        
        # 根据选中的 bundle 路径加载对应的 interface
        bundle_path = selected_bundle.get("path", "./")
        if not bundle_path:
            bundle_path = "./"
        
        # 解析 bundle 路径（可能是相对路径或绝对路径）
        from pathlib import Path
        from app.utils.logger import logger
        
        if Path(bundle_path).is_absolute():
            interface_dir = Path(bundle_path)
        else:
            interface_dir = Path.cwd() / bundle_path
        
        # 查找 interface.json 或 interface.jsonc
        interface_path = None
        for candidate in [interface_dir / "interface.jsonc", interface_dir / "interface.json"]:
            if candidate.exists():
                interface_path = candidate
                break
        
        if not interface_path:
            self.show_error(
                self.tr("Interface file not found in bundle: {}").format(bundle_path)
            )
            return
        
        # 加载 interface 配置
        try:
            with open(interface_path, "r", encoding="utf-8") as f:
                bundle_interface = jsonc.load(f)
        except Exception as e:
            logger.error(f"加载 bundle interface 失败: {e}")
            self.show_error(
                self.tr("Failed to load interface from bundle: {}").format(str(e))
            )
            return
        
        # 从 bundle interface 中获取 controller 和 resource
        if "controller" not in bundle_interface or not bundle_interface["controller"]:
            self.show_error(self.tr("Controller not found in bundle interface"))
            return
        if "resource" not in bundle_interface or not bundle_interface["resource"]:
            self.show_error(self.tr("Resource not found in bundle interface"))
            return
        
        init_controller = bundle_interface["controller"][0]["name"]
        init_resource = bundle_interface["resource"][0]["name"]
        default_tasks = [
            TaskItem(
                name="Controller",
                item_id=_CONTROLLER_,
                is_checked=True,
                task_option={
                    "controller_type": init_controller,
                },
            ),
            TaskItem(
                name="Setting",
                item_id=_SETTING_,
                is_checked=True,
                task_option={},
            ),
            TaskItem(
                name="Resource",
                item_id=_RESOURCE_,
                is_checked=True,
                task_option={
                    "resource": init_resource,
                },
            ),
            TaskItem(
                name="Post-Action",
                item_id=POST_ACTION,
                is_checked=True,
                task_option={},
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

    def get_selected_preset_name(self) -> str | None:
        """获取选中的预设名称，如果未选择预设则返回 None"""
        return self._selected_preset_name

    def get_shared_tasks(self) -> list | None:
        """获取从分享编码解析出的任务列表，未启用导入时返回 None"""
        return self._shared_tasks

    def get_share_version_mismatch(self) -> tuple[str, str] | None:
        """获取跨版本导入警告信息 (shared_version, target_version)，无警告时返回 None"""
        return self._share_version_mismatch


class AddTaskDialog(BaseAddDialog):
    _DEFAULT_GROUP_KEY = "__default_group__"

    def __init__(
        self,
        task_map: dict[str, dict[str, dict]],
        interface: dict | None = None,
        interface_path: Path | str | None = None,
        parent=None,
    ):
        # 调用基类构造函数，设置标题
        super().__init__(self.tr("Add New Task"), parent)
        self.widget.setMinimumWidth(620)
        self.widget.setMinimumHeight(500)
        self.cancelButton.setText(self.tr("Close"))
        self.yesButton.setText(self.tr("Add"))

        self.task_layout = QVBoxLayout()
        self.task_layout.setContentsMargins(0, 0, 0, 0)
        self.task_layout.setSpacing(12)

        self.task_label = CaptionLabel(self.tr("Task List"), self)
        self.task_hint = BodyLabel(
            self.tr(
                "Click to add a task. Right-click to remove one. "
                "The same task can be added multiple times."
            ),
            self,
        )
        self.task_hint.setWordWrap(True)

        self.task_scroll_area = ScrollArea(self)
        self.task_scroll_area.setWidgetResizable(True)
        self.task_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.task_scroll_area.enableTransparentBackground()
        self.task_scroll_area.setStyleSheet("background: transparent; border: none;")
        self.task_scroll_area.viewport().setStyleSheet("background: transparent;")

        self.task_scroll_content = QWidget(self.task_scroll_area)
        self.task_scroll_content.setObjectName("taskScrollContent")
        self.task_scroll_content.setStyleSheet(
            "QWidget#taskScrollContent { background: transparent; }"
        )
        self.task_group_layout = QVBoxLayout(self.task_scroll_content)
        self.task_group_layout.setContentsMargins(8, 8, 8, 8)
        self.task_group_layout.setSpacing(12)

        self._task_button_group = QButtonGroup(self)
        self._task_button_group.setExclusive(False)

        self.task_map = task_map
        self.interface = interface or {}
        self._interface_dir = self._normalize_interface_dir(interface_path)
        self._task_meta = self._build_task_meta()
        self._group_meta = self._build_group_meta()
        self._populate_task_groups()

        self.task_scroll_area.setWidget(self.task_scroll_content)

        self.task_layout.addWidget(self.task_label)
        self.task_layout.addWidget(self.task_hint)
        self.task_layout.addWidget(self.task_scroll_area)

        # 将布局添加到对话框
        self.viewLayout.addLayout(self.task_layout)

        # 存储数据的变量
        self.task_name = ""
        self.task_type = "task"
        self.items: list[TaskItem] = []
        self._selected_tasks: list[str] = []

    def _normalize_interface_dir(self, interface_path: Path | str | None) -> Path:
        """解析当前 interface 目录，作为相对图标路径基准。"""
        if not interface_path:
            return Path.cwd()

        candidate = Path(interface_path)
        if candidate.suffix.lower() in {".json", ".jsonc"}:
            return candidate.parent.resolve()
        return candidate.resolve()

    def _build_task_meta(self) -> dict[str, dict]:
        """构建任务元数据，保留 interface 中的展示顺序。"""
        task_meta: dict[str, dict] = {}
        interface_tasks = self.interface.get("task", []) if self.interface else []

        for task in interface_tasks:
            task_name = task.get("name")
            if not isinstance(task_name, str) or task_name not in self.task_map:
                continue
            task_meta[task_name] = task

        # 兼容 task_map 中存在但 interface 未声明的任务
        for task_name in self.task_map.keys():
            task_meta.setdefault(task_name, {"name": task_name})

        return task_meta

    def _build_group_meta(self) -> dict[str, dict]:
        """根据 interface.group 和 task.group 构建分组元数据。"""
        group_meta: dict[str, dict] = {}
        for group_def in self.interface.get("group", []) if self.interface else []:
            group_name = group_def.get("name")
            if not isinstance(group_name, str) or not group_name:
                continue
            group_meta[group_name] = group_def

        for task_name, task_def in self._task_meta.items():
            groups = task_def.get("group")
            if isinstance(groups, str):
                groups = [groups]
            if not isinstance(groups, list):
                continue
            for group_name in groups:
                if not isinstance(group_name, str) or not group_name:
                    continue
                group_meta.setdefault(group_name, {"name": group_name})

        group_meta.setdefault(
            self._DEFAULT_GROUP_KEY,
            {
                "name": self._DEFAULT_GROUP_KEY,
                "label": self.tr("Default Group"),
                "description": self.tr("Tasks without an explicit group"),
                "default_expand": True,
            },
        )
        return group_meta

    def _task_groups(self, task_def: dict) -> list[str]:
        """获取任务所属分组；未声明时归入默认分组。"""
        groups = task_def.get("group")
        if isinstance(groups, str):
            groups = [groups]
        if isinstance(groups, list):
            normalized = []
            for group_name in groups:
                if not isinstance(group_name, str):
                    continue
                group_name = group_name.strip()
                if not group_name:
                    continue
                normalized.append(group_name)
            if normalized:
                return normalized
        return [self._DEFAULT_GROUP_KEY]

    def _group_sort_key(self, group_name: str) -> tuple[int, int, str]:
        """按 interface.group 顺序排序，默认分组和内置分组放末尾。"""
        interface_groups = self.interface.get("group", []) if self.interface else []
        if group_name == BUILTIN_TASK_GROUP_NAME:
            return (3, 0, group_name)
        if group_name == self._DEFAULT_GROUP_KEY:
            return (2, 0, group_name)
        for idx, group_def in enumerate(interface_groups):
            if group_def.get("name") == group_name:
                return (0, idx, group_name)
        return (1, 0, group_name)

    def _resolve_icon(self, icon_value: str | None) -> QIcon | None:
        """解析相对路径图标，失败时返回 None。"""
        if not icon_value or not isinstance(icon_value, str):
            return None
        icon_path = Path(icon_value)
        if not icon_path.is_absolute():
            icon_path = self._interface_dir / icon_path
        if not icon_path.exists():
            return None
        icon = QIcon(str(icon_path))
        return icon if not icon.isNull() else None

    def _grouped_task_names(self) -> dict[str, list[str]]:
        """按分组收集任务名。"""
        grouped_tasks: dict[str, list[str]] = {}
        for task_name, task_def in self._task_meta.items():
            for group_name in self._task_groups(task_def):
                grouped_tasks.setdefault(group_name, []).append(task_name)
        return grouped_tasks

    def _create_group_widget(
        self, group_name: str, task_names: list[str]
    ) -> SimpleCardWidget:
        """创建单个分组卡片和动画流式布局。"""
        group_widget = SimpleCardWidget(self.task_scroll_content)
        group_layout = QVBoxLayout(group_widget)
        group_layout.setContentsMargins(16, 14, 16, 14)
        group_layout.setSpacing(8)

        group_def = self._group_meta.get(group_name, {"name": group_name})
        group_label = group_def.get("label") or group_def.get("name") or group_name
        group_title = StrongBodyLabel(str(group_label), group_widget)
        description = group_def.get("description")
        apply_fluent_tooltip(
            group_title, str(description) if description else None,
        )

        group_hint = CaptionLabel(
            self.tr("{} tasks").format(len(task_names)), group_widget
        )
        group_hint.setStyleSheet("color: rgba(128, 128, 128, 0.9);")

        flow_container = QWidget(group_widget)
        flow_container.setObjectName("taskFlowContainer")
        flow_container.setStyleSheet(
            "QWidget#taskFlowContainer { background: transparent; }"
        )
        flow_layout = FlowLayout(flow_container, needAni=True)
        flow_layout.setAnimation(250, QEasingCurve.Type.OutQuad)
        flow_layout.setContentsMargins(0, 2, 0, 0)
        flow_layout.setHorizontalSpacing(10)
        flow_layout.setVerticalSpacing(10)

        for task_name in task_names:
            task_button = self._create_task_button(task_name)
            flow_layout.addWidget(task_button)

        group_layout.addWidget(group_title)
        group_layout.addWidget(group_hint)
        group_layout.addWidget(flow_container)
        return group_widget

    def _create_task_button(self, task_name: str) -> TogglePushButton:
        """创建任务切换按钮。"""
        task_def = self._task_meta.get(task_name, {"name": task_name})
        task_label = task_def.get("label") or task_name
        task_button = TogglePushButton(self.task_scroll_content)
        task_button.setCheckable(True)
        task_button.setText(str(task_label))
        task_button.setMinimumHeight(38)
        task_button.setMinimumWidth(116)
        task_button.setProperty("taskName", task_name)
        task_button.setProperty("taskLabel", str(task_label))

        task_icon = self._resolve_icon(task_def.get("icon"))
        if task_icon:
            task_button.setIcon(task_icon)

        description = task_def.get("description")
        apply_fluent_tooltip(
            task_button, str(description) if description else None,
        )
        self._task_button_group.addButton(task_button)
        task_button.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        task_button.installEventFilter(self)
        return task_button

    def eventFilter(self, watched, event) -> bool:
        """拦截任务按钮点击：左键增加，右键减少；每次点击都计数。"""
        if not isinstance(watched, TogglePushButton):
            return super().eventFilter(watched, event)

        task_name = str(watched.property("taskName") or "").strip()

        if event.type() == QEvent.Type.MouseButtonDblClick:
            if task_name:
                if event.button() == Qt.MouseButton.LeftButton:
                    self._add_task_selection(task_name)
                elif event.button() == Qt.MouseButton.RightButton:
                    self._remove_task_selection(task_name)
            return True

        if event.type() in (
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
        ):
            if event.button() not in (
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.RightButton,
            ):
                return super().eventFilter(watched, event)

            if event.type() == QEvent.Type.MouseButtonPress and task_name:
                if event.button() == Qt.MouseButton.LeftButton:
                    self._add_task_selection(task_name)
                elif event.button() == Qt.MouseButton.RightButton:
                    self._remove_task_selection(task_name)
            return True

        return super().eventFilter(watched, event)

    def _add_task_selection(self, task_name: str) -> None:
        self._selected_tasks.append(task_name)
        self._update_task_button_display(task_name)

    def _remove_task_selection(self, task_name: str) -> None:
        for i in range(len(self._selected_tasks) - 1, -1, -1):
            if self._selected_tasks[i] == task_name:
                del self._selected_tasks[i]
                break
        self._update_task_button_display(task_name)

    def _task_selection_count(self, task_name: str) -> int:
        return self._selected_tasks.count(task_name)

    def _update_task_button_display(self, task_name: str) -> None:
        for button in self._task_button_group.buttons():
            if str(button.property("taskName") or "") != task_name:
                continue
            base_label = str(button.property("taskLabel") or "")
            count = self._task_selection_count(task_name)
            button.blockSignals(True)
            button.setChecked(count > 0)
            button.setText(f"{base_label} ×{count}" if count > 0 else base_label)
            button.blockSignals(False)
            button.update()
            break

    def _populate_task_groups(self) -> None:
        """按 group -> 动画流式布局 构建滚动内容。"""
        grouped_tasks = self._grouped_task_names()
        for group_name in sorted(grouped_tasks.keys(), key=self._group_sort_key):
            group_widget = self._create_group_widget(group_name, grouped_tasks[group_name])
            self.task_group_layout.addWidget(group_widget)
        self.task_group_layout.addStretch(1)

    def _selected_task_names(self) -> list[str]:
        """获取当前被选中的任务名列表（允许同名，保留选择顺序）。"""
        return list(self._selected_tasks)

    def _create_task_item(self, task_name: str) -> TaskItem:
        """根据任务名创建 TaskItem。"""
        default_check = True
        if self.interface:
            for task_def in self.interface.get("task", []):
                if task_def.get("name") == task_name:
                    default_check = bool(task_def.get("default_check", True))
                    break

        task_option = (
            self.task_map.get(task_name, {})
            if isinstance(self.task_map, dict)
            else {}
        )
        task_def = self._task_meta.get(task_name, {})
        task_source = "builtin" if task_def.get("builtin") else "resource"
        builtin_key = str(task_def.get("builtin_key", "") or "")
        return TaskItem(
            name=task_name,
            item_id=TaskItem.generate_id(),
            is_checked=default_check,
            task_option=task_option,
            task_source=task_source,
            builtin_key=builtin_key,
        )

    def on_confirm(self):
        """确认添加任务"""
        task_names = self._selected_task_names()
        self.task_name = task_names[0] if task_names else ""

        if not task_names:
            self.show_error(self.tr("Please select at least one task"))
            return

        self.items = [self._create_task_item(name) for name in task_names]
        self.item = self.items[0]

        self.accept()

    def get_task_item(self):
        """获取创建的任务项对象（兼容单选）"""
        return self.item

    def get_task_items(self) -> list[TaskItem]:
        """获取创建的任务项列表"""
        if self.items:
            return list(self.items)
        return [self.item] if self.item else []


