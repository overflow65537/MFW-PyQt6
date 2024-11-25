from PyQt6.QtCore import QSize, QMetaObject, QCoreApplication
from PyQt6.QtWidgets import (
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QFrame,
)
from qfluentwidgets import (
    PushButton,
    BodyLabel,
    ComboBox,
    EditableComboBox,
    ListWidget,
    LineEdit,
    TimeEdit,
)


class Ui_Scheduled_Interface(object):
    def setupUi(self, Scheduled_Interface):
        Scheduled_Interface.setObjectName("Scheduled_Interface")
        Scheduled_Interface.resize(900, 600)
        Scheduled_Interface.setMinimumSize(QSize(0, 0))
        # 主窗口

        # 切换配置布局

        self.cfgCombox_layout = QHBoxLayout()
        self.Cfg_Combox = EditableComboBox(Scheduled_Interface)
        self.Cfg_Combox.setObjectName("Cfg_Combox")
        self.Add_cfg_Button = PushButton(Scheduled_Interface)
        self.Add_cfg_Button.setObjectName("Add_cfg_Button")
        self.Add_cfg_Button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.Delete_cfg_Button = PushButton(Scheduled_Interface)
        self.Delete_cfg_Button.setObjectName("Delete_cfg_Button")
        self.Delete_cfg_Button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )

        self.cfgCombox_layout.addWidget(self.Cfg_Combox)
        self.cfgCombox_layout.addWidget(self.Add_cfg_Button)
        self.cfgCombox_layout.addWidget(self.Delete_cfg_Button)

        # 资源布局
        self.res_combox_layout = QHBoxLayout()
        self.res_combox = ComboBox(Scheduled_Interface)
        self.res_combox.setObjectName("res_combox")
        self.add_res_button = PushButton(Scheduled_Interface)
        self.add_res_button.setObjectName("add_res_button")
        self.add_res_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.delete_res_button = PushButton(Scheduled_Interface)
        self.delete_res_button.setObjectName("delete_res_button")
        self.delete_res_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.res_combox_layout.addWidget(self.res_combox)
        self.res_combox_layout.addWidget(self.add_res_button)
        self.res_combox_layout.addWidget(self.delete_res_button)

        # 配置列表布局

        self.List_layout = QVBoxLayout()
        self.List_widget = ListWidget(Scheduled_Interface)
        self.List_widget.setObjectName("List_widget")
        self.Add_cfg_Button.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        self.List_layout.addLayout(self.res_combox_layout)
        self.List_layout.addLayout(self.cfgCombox_layout)
        self.List_layout.addWidget(self.List_widget)

        # 计划任务布局

        self.Schedule_layout = QFormLayout()
        self.Schedule_name_title = BodyLabel(Scheduled_Interface)
        self.Schedule_name_title.setObjectName("Schedule_name_title")
        self.Schedule_name_edit = EditableComboBox(Scheduled_Interface)
        self.Schedule_name_edit.setObjectName("Schedule_name_edit")
        self.Schedule_layout.addRow(self.Schedule_name_title, self.Schedule_name_edit)

        self.Trigger_Time_layout = QGridLayout()
        self.Trigger_Time_title = BodyLabel(Scheduled_Interface)
        self.Trigger_Time_title.setObjectName("Trigger_Time_title")
        self.Trigger_Time_type = ComboBox(Scheduled_Interface)
        self.Trigger_Time_even_week = ComboBox(Scheduled_Interface)
        self.Trigger_Time_edit = TimeEdit(Scheduled_Interface)
        self.Trigger_Time_edit.setObjectName("Trigger_Time_edit")
        self.Trigger_Time_layout.addWidget(self.Trigger_Time_title, 0, 0)
        self.Trigger_Time_layout.addWidget(self.Trigger_Time_type, 0, 1)
        self.Trigger_Time_layout.addWidget(self.Trigger_Time_even_week, 0, 2)
        self.Trigger_Time_layout.addWidget(self.Trigger_Time_edit, 1, 1)

        self.use_cfg_layout = QFormLayout()
        self.use_cfg_title = BodyLabel(Scheduled_Interface)
        self.use_cfg_title.setObjectName("use_cfg_title")
        self.use_cfg_combo = ComboBox(Scheduled_Interface)
        self.use_cfg_combo.setObjectName("use_cfg_combo")
        self.use_cfg_layout.addRow(self.use_cfg_title, self.use_cfg_combo)

        # 计划列表布局
        self.Schedule_list_layout = QVBoxLayout()
        self.Schedule_list_widget = ListWidget(Scheduled_Interface)
        self.Schedule_list_widget.setObjectName("Schedule_list_widget")
        self.Schedule_list_layout.addWidget(self.Schedule_list_widget)

        # 总布局

        self.Schedule_layout_all = QVBoxLayout()
        self.cfg_list = ListWidget(Scheduled_Interface)
        self.cfg_list.setObjectName("cfg_list")

        self.Schedule_layout_all.addLayout(self.Schedule_layout)
        self.Schedule_layout_all.addLayout(self.Trigger_Time_layout)
        self.Schedule_layout_all.addLayout(self.use_cfg_layout)
        self.Schedule_layout_all.addWidget(self.cfg_list)

        self.all_layout = QHBoxLayout()

        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.VLine)
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.all_layout.addLayout(self.List_layout)
        self.all_layout.addWidget(self.line)
        self.all_layout.addLayout(self.Schedule_layout_all)

        Scheduled_Interface.setLayout(self.all_layout)
        self.retranslateUi(Scheduled_Interface)
        QMetaObject.connectSlotsByName(Scheduled_Interface)

    def retranslateUi(self, Scheduled_Interface):
        _translate = QCoreApplication.translate
        Scheduled_Interface.setWindowTitle(
            _translate("Scheduled_Interface", "Scheduled Interface")
        )
        self.Add_cfg_Button.setText(_translate("Scheduled_Interface", "Add"))
        self.Delete_cfg_Button.setText(_translate("Scheduled_Interface", "Delete"))
        self.add_res_button.setText(_translate("Scheduled_Interface", "Add"))
        self.delete_res_button.setText(_translate("Scheduled_Interface", "Delete"))
        self.Schedule_name_title.setText(
            _translate("Scheduled_Interface", "Scheduled name")
        )
        self.Schedule_name_edit.setPlaceholderText(
            _translate("Scheduled_Interface", "please inter scheduled name")
        )
        self.Trigger_Time_title.setText(
            _translate("Scheduled_Interface", "Trigger Time")
        )
        self.use_cfg_title.setText(
            _translate("Scheduled_Interface", "Use Configuration")
        )
