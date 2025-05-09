from PyQt6.QtCore import Qt, QSize, QMetaObject, QCoreApplication
from PyQt6.QtWidgets import (
    QFormLayout,QSizePolicy,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QAbstractItemView,QWidget
)

from PyQt6.QtWidgets import QFrame
from qfluentwidgets import (
    PushButton,
    BodyLabel,
    ComboBox,
    EditableComboBox,
    ListWidget,ZhDatePicker,
    LineEdit,
    DateTimeEdit,
    TimePicker,RadioButton,CheckBox,
    SpinBox
    
)

from ..common.style_sheet import StyleSheet
from ..components.listwidge_menu_draggable import ListWidge_Menu_Draggable


class Ui_Scheduled_Interface(object):
    def setupUi(self, Scheduled_Interface):
        Scheduled_Interface.setObjectName("Scheduled_Interface")
        Scheduled_Interface.resize(900, 600)
        Scheduled_Interface.setMinimumSize(QSize(0, 0))
        # 主窗口
        self.List_layout = QVBoxLayout()
        self.List_widget = ListWidge_Menu_Draggable(Scheduled_Interface)
        self.List_widget.setDragEnabled(True)
        self.List_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        self.List_layout.addWidget(self.List_widget)
        


        # 速通模式标题布局
        # 主垂直布局
        self.main_layout = QVBoxLayout()
        
        # 第一行：标题
        self.title_label = BodyLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        #第二行 间隔时间
        # 时间选择水平布局
        self.time_selection_layout = QHBoxLayout()
        self.date_label = BodyLabel()
        self.date_picker = ZhDatePicker(Scheduled_Interface)
        self.time_picker = TimePicker(Scheduled_Interface)
        
        self.time_selection_layout.addWidget(self.date_label)
        self.time_selection_layout.addWidget(self.date_picker)
        self.time_selection_layout.addWidget(self.time_picker)
        # 将时间选择布局添加到主布局
        self.main_layout.addLayout(self.time_selection_layout)
        
        # 第三行：复合水平布局
        self.row3_layout = QHBoxLayout()
        
        # 计划任务模式选择容器
        self.schedule_mode_widget = QWidget()  
        self.schedule_mode_layout = QVBoxLayout(self.schedule_mode_widget)
        
        # 计划任务模式单选按钮
        self.schedule_mode_title = BodyLabel()
        self.daily_mode_radio = RadioButton()
        self.weekly_mode_radio = RadioButton() 
        self.monthly_mode_radio = RadioButton()

        
        self.schedule_mode_layout.addWidget(self.schedule_mode_title)
        self.schedule_mode_layout.addWidget(self.daily_mode_radio)
        self.schedule_mode_layout.addWidget(self.weekly_mode_radio)
        self.schedule_mode_layout.addWidget(self.monthly_mode_radio)
        
        # 右侧：时间选择和操作按钮区域
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        
        # 按钮表格布局容器
        widget = QWidget()

        self.layout = QVBoxLayout()

        self.refresh_time_layout = QHBoxLayout()
        self.refresh_time_label = BodyLabel()
        self.weekly_mode_combox = ComboBox()
        
        
        self.refresh_time_spinbox = SpinBox(self)
        self.refresh_time_unit_label = BodyLabel()

        self.refresh_time_layout.addWidget(self.refresh_time_label)
        self.refresh_time_layout.addWidget(self.weekly_mode_combox)
        self.refresh_time_layout.addWidget(self.refresh_time_spinbox)
        self.refresh_time_layout.addWidget(self.refresh_time_unit_label)
        self.weekly_mode_combox.hide()

        self.interval_layout = QHBoxLayout()
        self.interval_label = BodyLabel()
        self.interval_input = SpinBox()
        self.interval_unit = ComboBox()
        self.loop_label = BodyLabel()
        self.loop_input = SpinBox()
        self.loop_unit_label = BodyLabel()

        self.interval_layout.addWidget(self.interval_label)
        self.interval_layout.addWidget(self.interval_input)
        self.interval_layout.addWidget(self.interval_unit)
        self.interval_layout.addWidget(self.loop_label)
        self.interval_layout.addWidget(self.loop_input)
        self.interval_layout.addWidget(self.loop_unit_label)

        self.layout.addLayout(self.refresh_time_layout)
        self.layout.addLayout(self.interval_layout)
        
        widget.setLayout(self.layout)

        self.current_layout = widget
        self.right_layout.addWidget(self.current_layout)
        
        
        # 将左右两部分添加到水平布局
        self.row3_layout.addWidget(self.schedule_mode_widget)
        self.row3_layout.addWidget(self.right_panel)
        self.main_layout.addLayout(self.row3_layout)
        
        # 第三行：五个标签的垂直布局,可能会当教程使用


        self.main_layout.addWidget(self.List_widget)



        Scheduled_Interface.setLayout(self.main_layout)
        self.retranslateUi(Scheduled_Interface)
        QMetaObject.connectSlotsByName(Scheduled_Interface)

    def retranslateUi(self, Scheduled_Interface):
        _translate = QCoreApplication.translate
        Scheduled_Interface.setWindowTitle(_translate("Scheduled_Interface", "Form"))


        