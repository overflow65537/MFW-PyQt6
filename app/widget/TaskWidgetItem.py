from PySide6.QtWidgets import QWidget, QListWidgetItem, QHBoxLayout
from PySide6.QtCore import Signal, Qt, QMimeData
from PySide6.QtGui import QWheelEvent, QMouseEvent, QDrag, QPixmap
from qfluentwidgets import (
    CheckBox,
    TransparentToolButton,
    BodyLabel,
    SimpleCardWidget,
    ToolTipFilter,
    ToolTipPosition,
    FluentIcon as FIF,
)


class TaskWidgetItem(SimpleCardWidget):

    setting_signal = Signal(dict)

    def __init__(self, text: str, config: dict):
        super().__init__()
        self.text = text
        self.config = config
        self._init_ui()

        self.setting_button.clicked.connect(self.on_setting_click)

        # 设置高度
        self.setFixedHeight(40)

    def _init_ui(self):
        # 拖动按钮
        self.drag_button = TransparentToolButton(FIF.SCROLL)
        self.drag_button.setFixedWidth(20)
        self.drag_button.mousePressEvent = self.start_drag
        self.drag_button.installEventFilter(
            ToolTipFilter(self.drag_button, 0, ToolTipPosition.TOP)
        )
        self.drag_button.setToolTip("Press to drag")

        self.checkBox = CheckBox()
        self.checkBox.setFixedWidth(20)

        self.text_label = BodyLabel(self.text)
        self.setting_button = TransparentToolButton(FIF.SETTING)
        self.setting_button.setFixedWidth(20)
        self.setting_button.installEventFilter(
            ToolTipFilter(self.setting_button, 0, ToolTipPosition.TOP)
        )
        self.setting_button.setToolTip("Press to setting")

        self.main_layout = QHBoxLayout(self)
        self.main_layout.addWidget(self.drag_button)
        self.main_layout.addWidget(self.checkBox)
        self.main_layout.addWidget(self.text_label)
        self.main_layout.addWidget(self.setting_button)

    def on_setting_click(self):
        self.setting_signal.emit(self.config)
        print(self.text)

    def start_drag(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            # 创建拖放对象
            drag = QDrag(self)
            mime_data = QMimeData()
            # 存储当前项的唯一标识
            mime_data.setText(str(id(self)))
            drag.setMimeData(mime_data)

            # 创建拖动时的预览图像
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(e.pos())

            # 执行拖放操作，只允许移动动作
            drag.exec(Qt.DropAction.MoveAction)
