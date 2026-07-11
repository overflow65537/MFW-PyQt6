from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import PrimaryPushButton

from app.utils.logger import logger
from .base import OptionItemBase


class _HotkeyCaptureButton(QWidget):
    """快捷键捕获按钮"""

    CAPTURE_TEXT = "..."

    def __init__(
        self,
        hotkey_name: str,
        default_text: str = "",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._hotkey_name = hotkey_name
        self._capturing = False
        self._current_key = default_text

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._button = PrimaryPushButton(self)
        self._button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._button.setMinimumHeight(36)
        self._update_text()

        layout.addWidget(self._button)

        self._button.clicked.connect(self._on_clicked)

    def _update_text(self):
        if self._capturing:
            self._button.setText(self.CAPTURE_TEXT)
        elif self._current_key:
            self._button.setText(self._current_key)
        else:
            self._button.setText(self.tr("Click to set hotkey"))

    def _on_clicked(self):
        self._start_capture()

    def _start_capture(self):
        self._capturing = True
        self._update_text()
        self.setFocus()
        self.grabKeyboard()

    def _finish_capture(self):
        self._capturing = False
        self._update_text()
        self.releaseKeyboard()

    def keyPressEvent(self, event: QKeyEvent):
        if not self._capturing:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key == Qt.Key.Key_unknown:
            self._finish_capture()
            return

        modifiers = event.modifiers()
        key_code = modifiers.value | key
        key_text = QKeySequence(key_code).toString()
        if not key_text:
            self._finish_capture()
            return

        self._current_key = key_text
        self._finish_capture()

    def key(self) -> str:
        return self._current_key

    def set_key(self, key_text: str):
        self._current_key = key_text
        if not self._capturing:
            self._update_text()


class HotkeyOptionItem(OptionItemBase):
    """快捷键捕获选项项"""

    def __init__(
        self, key: str, config: Dict[str, Any], parent: Optional["OptionItemBase"] = None
    ):
        config["type"] = "hotkey"
        super().__init__(key, config, parent)
        self._capture_buttons: Dict[str, _HotkeyCaptureButton] = {}
        self.init_ui()
        self.init_config()
        self._animation_enabled = True

    def init_ui(self):
        main_label_text = self.config.get("label")
        if main_label_text:
            self.label = self._create_label_with_optional_icon(
                main_label_text,
                self.config.get("icon"),
                self.main_option_layout,
                self.config.get("description"),
            )

        self.control_widget = {}
        hotkeys = self.config.get("hotkeys", [])

        for hotkey_item in hotkeys:
            hotkey_name = hotkey_item.get("name", "")
            hotkey_label = hotkey_item.get("label", hotkey_name)
            hotkey_desc = hotkey_item.get("description")
            default_value = hotkey_item.get("default", "")

            container = QVBoxLayout()
            container.setContentsMargins(10, 5, 10, 5)

            label_widget = self._create_label_with_optional_icon(
                hotkey_label,
                hotkey_item.get("icon"),
                container,
                hotkey_desc,
            )

            capture_btn = _HotkeyCaptureButton(
                hotkey_name, default_value, parent=self
            )
            container.addWidget(capture_btn)
            self.main_option_layout.addLayout(container)

            capture_btn._finish_capture = self._make_capture_finish_handler(
                hotkey_name, capture_btn
            )
            self.control_widget[hotkey_name] = capture_btn
            self._capture_buttons[hotkey_name] = capture_btn

    def _make_capture_finish_handler(self, name: str, btn: _HotkeyCaptureButton):
        original = btn._finish_capture

        def wrapped():
            original()
            if isinstance(self.current_value, dict):
                self.current_value[name] = btn.key()
            self.option_changed.emit(self.key, self.current_value)

        return wrapped

    def init_config(self):
        if isinstance(self.control_widget, dict):
            self.current_value = {
                name: btn.key()
                for name, btn in self.control_widget.items()
            }

    def _unwrap_value(self, value: Any) -> Any:
        if isinstance(value, dict) and "value" in value:
            return value["value"]
        return value

    def set_value(self, value: Any, skip_animation: bool = True):
        hotkey_value = self._unwrap_value(value)

        if isinstance(self.control_widget, dict):
            if isinstance(hotkey_value, dict):
                for name, key_text in hotkey_value.items():
                    if name in self.control_widget:
                        btn = self.control_widget[name]
                        btn.set_key(str(key_text))
                        if isinstance(self.current_value, dict):
                            self.current_value[name] = str(key_text)
            else:
                logger.warning(
                    f"hotkey type expects dict value, got: {type(hotkey_value)}"
                )
        else:
            logger.warning("hotkey controls not initialized, cannot set value")

    def get_option(self) -> Dict[str, Any]:
        return {"value": self.current_value}

    def get_simple_option(self) -> Any:
        return self.current_value


__all__ = ["HotkeyOptionItem"]