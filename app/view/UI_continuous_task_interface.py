from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel

from qfluentwidgets import SegmentedWidget


class Ui_ContinuousTaskInterface(QWidget):
    def setupUi(self, Continuous_Task_Interface):
        Continuous_Task_Interface.setObjectName("Continuous_Task_Interface")
        Continuous_Task_Interface.resize(900, 600)
        Continuous_Task_Interface.setMinimumSize(QSize(0, 0))
        # 主窗口

        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        #动态创建页面

        for info in [("歌曲", "song"), ("专辑", "album"), ("艺术家", "artist")]:
            page = SpecialTask()
            label = QLabel(page)
            label.setText(info[0])
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stackedWidget.addWidget(page)
            self.pivot.addItem(
                routeKey=info[1],
                text=info[0],
                onClick=lambda: self.stackedWidget.setCurrentIndex(self.stackedWidget.count()-1) 
            )


        # 将导航栏和 stackedWidget 添加到布局中
        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        #设置边距
        self.vBoxLayout.setContentsMargins(20, 20, 20, 20)
        
class SpecialTask(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)