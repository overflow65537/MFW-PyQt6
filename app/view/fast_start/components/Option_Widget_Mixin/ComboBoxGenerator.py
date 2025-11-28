import copy
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
from qfluentwidgets import ComboBox, BodyLabel, ToolTipFilter
from app.utils.logger import logger


class ComboBoxGenerator:
    """
    下拉框生成器
    负责下拉框的创建、配置和信号处理
    """

    def __init__(self, host):
        """
        初始化下拉框生成器
        :param host: 宿主组件，需要包含widgets、child_layouts、all_child_containers等属性
        """
        self.host = host

    def create_combobox(self, key, config, parent_layout, parent_config):
        """创建下拉框"""
        # 创建控件容器
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        parent_layout.addWidget(container_widget)

        # 创建标签和图标容器
        label_container = QHBoxLayout()
        label_container.setSpacing(5)

        # 检查是否有图标配置
        icon_label = None
        if "icon" in config:
            try:

                icon = self.host._icon_loader.load_icon(config["icon"], size=24)
                if not icon.isNull():
                    icon_label = QLabel()
                    icon_label.setPixmap(icon.pixmap(24, 24))
                    icon_label.setFixedSize(24, 24)

                    # 添加图标到容器
                    label_container.addWidget(icon_label)
            except Exception as e:
                # 尝试直接加载作为备选方案
                try:
                    icon_path = config["icon"]
                    icon_pixmap = QPixmap(icon_path)

                    # 检查图标是否加载成功
                    if not icon_pixmap.isNull():
                        # 缩放图标到合适大小
                        icon_pixmap = icon_pixmap.scaled(
                            24,
                            24,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        icon_label = QLabel()
                        icon_label.setPixmap(icon_pixmap)
                        icon_label.setFixedSize(24, 24)

                        # 添加图标到容器
                        label_container.addWidget(icon_label)
                except Exception as direct_load_e:
                    # 加载图标失败时忽略
                    logger.error(
                        f"加载图标失败: {config['icon']}, 错误: {direct_load_e}"
                    )

        # 创建下拉框 - 使用垂直布局
        label_text = config["label"]
        if label_text.startswith("$"):
            pass
        label = BodyLabel(label_text)
        # 移除固定宽度，让标签自然显示

        # 添加标签到容器
        label_container.addWidget(label)

        # 将整个标签容器添加到主布局
        container_layout.addLayout(label_container)

        # 为选项标题添加tooltip（选项层级）
        if "description" in config:
            filter = ToolTipFilter(label)
            label.installEventFilter(filter)
            label.setToolTip(config["description"])

        combo = ComboBox()

        # 保存选项映射关系 (label -> name 和 name -> label)
        self.host._option_maps = getattr(self.host, "_option_maps", {})
        self.host._option_maps[key] = {}
        self.host._option_reverse_maps = getattr(self.host, "_option_reverse_maps", {})
        self.host._option_reverse_maps[key] = {}

        # 只支持新格式：字典列表，包含name和label
        options = config["options"]
        for option in options:
            label = option["label"]
            name = option["name"]
            combo.addItem(label)
            self.host._option_maps[key][label] = name
            self.host._option_reverse_maps[key][name] = label

        container_layout.addWidget(combo)

        # 检查是否需要隐藏整个下拉框行
        if "visible" in config and not config["visible"]:
            # 隐藏整个容器
            container_widget.setVisible(False)

        # 为下拉框控件添加tooltip（选项内部层级）
        if "description" in config:
            filter = ToolTipFilter(combo)
            combo.installEventFilter(filter)
            combo.setToolTip(config["description"])

        # 创建子控件容器布局
        child_layout = QVBoxLayout()
        container_layout.addLayout(child_layout)

        # 保存引用
        self.host.widgets[key] = combo
        self.host.child_layouts[key] = child_layout

        # 初始化配置
        init_label = combo.currentText()
        init_value = self.host._option_maps[key].get(init_label, init_label)
        parent_config[key] = {"value": init_value, "children": {}}

        # 初始化所有子选项容器字典
        self.host.all_child_containers[key] = {}

        # 预先生成所有子选项并设置为不可见
        if "children" in config:
            for option_value, child_config in config["children"].items():
                # 创建子选项容器
                option_container = QWidget()
                option_container_layout = QVBoxLayout(option_container)
                option_container_layout.setContentsMargins(0, 0, 0, 0)
                option_container_layout.setSpacing(0)
                child_layout.addWidget(option_container)

                # 默认设置为不可见
                option_container.setVisible(False)

                # 保存子选项容器的引用和相关信息
                self.host.all_child_containers[key][option_value] = {
                    "container": option_container,
                    "layout": option_container_layout,
                    "widgets": {},
                    "config": {},
                }

        # 连接信号，默认save_config=True
        combo.currentTextChanged.connect(
            lambda value, current_key=key, current_config=config, current_parent_config=parent_config[
                key
            ]: self._on_combobox_changed(
                current_key,
                value,
                current_config,
                current_parent_config,
                child_layout,
                save_config=True,
            )
        )

        # 触发初始加载，但使用blockSignals和save_config=False确保不会触发不必要的信号和配置覆盖
        try:
            # 临时禁用自动保存
            # 使用getattr获取_disable_auto_save属性，如果不存在则默认为False
            old_disable_auto_save = getattr(self.host, "_disable_auto_save", False)


            self.host._disable_auto_save = old_disable_auto_save
            self.host._disable_auto_save = True

            # 阻断下拉框信号，防止触发不必要的回调
            combo.blockSignals(True)
            try:
                # 触发初始加载，但设置save_config=False避免保存默认值
                self._on_combobox_changed(
                    key,
                    combo.currentText(),
                    config,
                    parent_config[key],
                    child_layout,
                    save_config=False,
                )
            finally:
                # 恢复信号连接
                combo.blockSignals(False)
        finally:
            # 恢复自动保存状态
            self.host._disable_auto_save = old_disable_auto_save   # type: ignore

    def _on_combobox_changed(
        self, key, value, config, parent_config, child_layout, save_config=True
    ):
        """下拉框值改变处理

        :param save_config: 是否保存配置，默认为True。初始化时可以设置为False避免保存默认值
        """
        # 获取下拉框控件
        combo_widget = self.host.widgets.get(key)

        # 临时阻断下拉框信号，防止在设置值时触发循环信号
        if combo_widget and hasattr(combo_widget, "blockSignals"):
            combo_widget.blockSignals(True)

        try:
            # 保存所有子选项配置到缓存（不仅仅是当前显示的选项）
            if key in self.host.all_child_containers:
                for option_value, container_info in self.host.all_child_containers[
                    key
                ].items():
                    # 为每个子选项创建缓存键
                    cache_key = f"{key}_{option_value}"

                    # 仅当容器配置非空且缓存中不存在该配置时才保存
                    # 这避免了在初始化时覆盖已经加载的缓存配置
                    if (
                        container_info["config"]
                        and cache_key not in self.host.option_subconfig_cache
                    ):
                        # 深拷贝子配置以保存完整状态
                        self.host.option_subconfig_cache[cache_key] = copy.deepcopy(
                            container_info["config"]
                        )

            # 更新配置 - 使用映射获取实际值
            actual_value = self.host._option_maps[key].get(value, value)
            parent_config["value"] = actual_value

            # 隐藏所有子选项容器
            if key in self.host.all_child_containers:
                for option_value, container_info in self.host.all_child_containers[
                    key
                ].items():
                    container_info["container"].setVisible(False)

            # 处理当前选择的子选项
            # 检查当前选择的是label还是name
            actual_key = self.host._option_maps[key].get(value, value)

            # 先尝试用实际值（name）查找，再尝试用显示值（label）查找
            has_children = False
            child_config = None
            current_container = None
            container_key = value  # 默认使用value作为container_key

            # 检查是否存在用实际值作为key的子配置
            if "children" in config:
                if actual_key in config["children"]:
                    has_children = True
                    child_config = config["children"][actual_key]
                    container_key = actual_key  # 用实际值作为container_key
                    if container_key in self.host.all_child_containers.get(key, {}):
                        current_container = self.host.all_child_containers[key][
                            container_key
                        ]
                elif value in config["children"]:
                    # 兼容旧格式，直接用label作为key
                    has_children = True
                    child_config = config["children"][value]
                    container_key = value
                    if container_key in self.host.all_child_containers.get(key, {}):
                        current_container = self.host.all_child_containers[key][
                            container_key
                        ]

            if (
                has_children
                and child_config
                and current_container
                and key in self.host.all_child_containers
            ):

                # 如果子容器中还没有创建控件，则创建它们
                if current_container["layout"].count() == 0:
                    # 检查child_config是否是一个包含多个配置项的字典
                    if isinstance(child_config, dict):
                        # 方式1：如果child_config有type键，处理为单个控件
                        if "type" in child_config:
                            # 查找当前子选项的键名，而不是硬编码为f"{key}_child"
                            # 遍历config["children"]找到对应的键名
                            child_key = ""

                            # 直接使用子配置的名称或标签作为child_key
                            if "name" in child_config:
                                child_key = child_config["name"]
                            elif "label" in child_config:
                                child_key = child_config["label"]

                            # 确保不使用$开头的名称
                            if child_key.startswith("$"):
                                child_key = child_key[1:]

                            # 如果还是没有找到，使用默认的键名
                            if not child_key:
                                child_key = f"{key}_child"

                            # 记录child_key的值
                            logger.info(
                                f"Generated child_key: {child_key} for config: {child_config}"
                            )

                            if child_config["type"] == "combobox":
                                self.create_combobox(
                                    child_key,
                                    child_config,
                                    current_container["layout"],
                                    current_container["config"],
                                )
                            elif child_config["type"] == "lineedit":
                                # 需要使用LineEditGenerator来创建输入框
                                from .LineEditGenerator import LineEditGenerator

                                line_edit_generator = LineEditGenerator(self.host)
                                line_edit_generator.create_lineedit(
                                    child_key,
                                    child_config,
                                    current_container["layout"],
                                    current_container["config"],
                                )

                        # 方式2：如果child_config不包含type键，但包含多个配置项，处理为多个控件
                        elif len(child_config) > 0:
                            # 为每个子配置项创建控件
                            for sub_key, sub_config in child_config.items():
                                if sub_config.get("type") == "combobox":
                                    self.create_combobox(
                                        sub_key,
                                        sub_config,
                                        current_container["layout"],
                                        current_container["config"],
                                    )
                                elif sub_config.get("type") == "lineedit":
                                    # 需要使用LineEditGenerator来创建输入框
                                    from .LineEditGenerator import LineEditGenerator

                                    line_edit_generator = LineEditGenerator(self.host)
                                    line_edit_generator.create_lineedit(
                                        sub_key,
                                        sub_config,
                                        current_container["layout"],
                                        current_container["config"],
                                    )

                # 尝试从缓存中恢复之前的子配置
                cache_key = f"{key}_{container_key}"
                if cache_key in self.host.option_subconfig_cache:
                    # 临时禁用自动保存，避免恢复配置时触发保存
                    old_disable_auto_save = getattr(
                        self.host, "_disable_auto_save", False
                    )
                    self.host._disable_auto_save = True
                    try:
                        # 应用缓存的子配置
                        self._apply_subconfigs(
                            child_config,
                            current_container["config"],
                            self.host.option_subconfig_cache[cache_key],
                        )
                    finally:
                        # 恢复自动保存状态
                        self.host._disable_auto_save = old_disable_auto_save

                # 设置当前子容器为可见并隐藏其他容器
                self._set_child_container_visibility(key, container_key)

                # 创建一个包含所有子选项配置的字典
                # 使用实际值（name）而不是显示值（label）作为key
                actual_value = self.host._option_maps[key].get(value, value)
                all_children_config = self._build_all_children_config(
                    key, actual_value, current_container["config"]
                )

                # 更新parent_config中的children，包含所有子选项配置
                parent_config["children"] = all_children_config

            # 自动保存选项，只有当save_config为True且未禁用自动保存时才保存
            if save_config and (
                not hasattr(self.host, "_disable_auto_save")
                or not self.host._disable_auto_save
            ):
                self._auto_save_options()
        finally:
            # 恢复信号连接
            if combo_widget and hasattr(combo_widget, "blockSignals"):
                combo_widget.blockSignals(False)

    def _set_child_container_visibility(self, key, visible_option_value):
        """设置子选项容器的可见性"""
        if key in self.host.all_child_containers:
            for option_value, container_info in self.host.all_child_containers[
                key
            ].items():
                container_info["container"].setVisible(
                    option_value == visible_option_value
                )

    def _build_all_children_config(self, key, current_value, current_config):
        """构建包含所有子选项配置的字典"""
        all_children_config = {current_value: current_config}

        if key in self.host.all_child_containers:
            for option_value, container_info in self.host.all_child_containers[
                key
            ].items():
                if option_value != current_value:  # 已经添加了当前选项，跳过
                    cache_key = f"{key}_{option_value}"
                    if cache_key in self.host.option_subconfig_cache:
                        # 从缓存中获取配置
                        all_children_config[option_value] = copy.deepcopy(
                            self.host.option_subconfig_cache[cache_key]
                        )
                    elif container_info["config"]:  # 如果缓存中没有但容器中有配置
                        all_children_config[option_value] = copy.deepcopy(
                            container_info["config"]
                        )

        return all_children_config

    def _apply_subconfigs(self, child_structure, target_config, cached_config):
        """应用缓存的子配置到目标配置

        :param child_structure: 子控件结构定义
        :param target_config: 目标配置字典
        :param cached_config: 缓存的配置字典
        """
        # 确保cached_config是一个字典
        if not isinstance(cached_config, dict):
            return

        # 深度合并缓存配置到目标配置，保留未在缓存中但存在于目标配置中的键
        # import copy is now at the top of the file

        # 如果子结构是单个控件
        if isinstance(child_structure, dict):
            if "type" in child_structure:
                # 单个控件情况
                # 深度合并缓存配置到目标配置
                for sub_key, sub_value in cached_config.items():
                    # 确保在更新时深度复制，避免引用问题
                    target_config[sub_key] = copy.deepcopy(sub_value)
            else:
                # 多个控件情况
                for sub_key, sub_config in child_structure.items():
                    if sub_key in cached_config:
                        # 如果缓存配置是字典，进行深度合并
                        if isinstance(cached_config[sub_key], dict) and isinstance(
                            target_config.get(sub_key), dict
                        ):
                            # 合并两个字典，保留目标配置中不在缓存中的键
                            for k, v in cached_config[sub_key].items():
                                target_config[sub_key][k] = copy.deepcopy(v)
                        else:
                            # 否则直接复制
                            target_config[sub_key] = copy.deepcopy(
                                cached_config[sub_key]
                            )

        # 应用配置到UI控件
        # 遍历目标配置中的所有键
        for sub_key, sub_value in target_config.items():
            # 检查子键是否在widgets字典中
            if sub_key in self.host.widgets:
                sub_widget = self.host.widgets[sub_key]
                try:
                    # 处理嵌套的widgets字典（如inputs类型）
                    if isinstance(sub_widget, dict):
                        for input_name, input_widget in sub_widget.items():
                            if isinstance(sub_value, dict) and input_name in sub_value:
                                # 临时阻断信号
                                input_widget.blockSignals(True)
                                try:
                                    input_widget.setText(str(sub_value[input_name]))
                                finally:
                                    # 确保恢复信号
                                    input_widget.blockSignals(False)
                    # 处理普通控件
                    else:
                        # 临时阻断信号
                        sub_widget.blockSignals(True)
                        try:
                            if hasattr(sub_widget, "setText"):
                                sub_widget.setText(str(sub_value))
                            elif hasattr(sub_widget, "setCurrentText"):
                                # 查找对应的label（考虑映射关系）
                                display_value = str(sub_value)

                                # 遍历所有反向映射，找到对应的label
                                if hasattr(self.host, "_option_reverse_maps"):
                                    for (
                                        widget_key,
                                        reverse_map,
                                    ) in self.host._option_reverse_maps.items():
                                        if (
                                            self.host.widgets.get(widget_key)
                                            == sub_widget
                                        ):
                                            display_value = reverse_map.get(
                                                str(sub_value), str(sub_value)
                                            )
                                            break

                                index = sub_widget.findText(display_value)
                                if index >= 0:
                                    sub_widget.setCurrentIndex(index)
                            # 处理其他可能的控件类型
                            elif hasattr(sub_widget, "setChecked") and isinstance(
                                sub_value, bool
                            ):
                                sub_widget.setChecked(sub_value)
                        finally:
                            # 确保恢复信号
                            sub_widget.blockSignals(False)
                except Exception as e:
                    # 记录错误但不影响其他控件的更新
                    logger.error(
                        f"应用子配置到控件失败 (key: {sub_key}, value: {sub_value}): {e}"
                    )

    def _auto_save_options(self):
        """自动保存当前选项"""
        # 检查是否禁用了自动保存
        if hasattr(self.host, "_disable_auto_save") and self.host._disable_auto_save:
            return

        # 检查是否有service_coordinator和option_service
        if hasattr(self.host, "service_coordinator") and hasattr(self.host.service_coordinator, "option_service"):  
            try:
                # 获取当前所有配置
                all_config = self.host.get_config()
                # 调用OptionService的update_options方法保存选项
                self.host.service_coordinator.option_service.update_options(all_config)  
            except Exception as e:
                # 如果保存失败，记录错误但不影响用户操作
                logger.error(f"自动保存选项失败: {e}")
