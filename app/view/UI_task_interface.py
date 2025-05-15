# -*- coding: utf-8 -*-

from PySide6.QtCore import QSize, QMetaObject, Qt
from PySide6.QtWidgets import (
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QFrame,
    QAbstractItemView,
    QWidget,
)

from qfluentwidgets import (
    PushButton,
    BodyLabel,
    ComboBox,
    ScrollArea,
)
from ..common.style_sheet import StyleSheet
from ..components.listwidge_menu_draggable import ListWidge_Menu_Draggable
from ..components.right_check_button import RightCheckButton



class Ui_Task_Interface(object):
    def setupUi(self, Task_Interface):
        Task_Interface.setObjectName("Task_Interface")
        Task_Interface.resize(900, 600)
        Task_Interface.setMinimumSize(QSize(0, 0))
        # 设置主窗口
        self.main_layout = QHBoxLayout(self)

        # 自动检测按钮;资源,控制器和完成后运行标签布局
        self.AutoDetBut_ResTit_CtlTit = QVBoxLayout()
        self.Resource_Title = BodyLabel(Task_Interface)
        self.Control_Title = BodyLabel(Task_Interface)
        self.AutoDetect_Button = PushButton(Task_Interface)
        self.Resource_Title.setObjectName("Resource_Title")
        self.Control_Title.setObjectName("Control_Title")
        self.AutoDetect_Button.setObjectName("AutoDetect_Button")
        self.AutoDetect_Button.setFixedSize(100, 30)
        self.Finish_title = BodyLabel(Task_Interface)
        self.Finish_title.setObjectName("Finish_title")
        self.Finish_title.setFixedSize(70, 30)
        self.Resource_Title.setFixedSize(70, 30)
        self.Control_Title.setFixedSize(70, 30)

        self.AutoDetBut_ResTit_CtlTit.addWidget(self.Resource_Title)
        self.AutoDetBut_ResTit_CtlTit.addWidget(self.Control_Title)
        self.AutoDetBut_ResTit_CtlTit.addWidget(self.AutoDetect_Button)
        self.AutoDetBut_ResTit_CtlTit.addWidget(self.Finish_title)

        # 左下下拉栏布局
        self.AutoDetCom_ResCom_CtlCom = QVBoxLayout()
        self.Resource_Combox = ComboBox(Task_Interface)
        self.Control_Combox = ComboBox(Task_Interface)
        self.Autodetect_combox = ComboBox(Task_Interface)
        self.Finish_combox = ComboBox(Task_Interface)
        self.Finish_combox.setObjectName("Finish_combox")

        self.Resource_Combox.setObjectName("Resource_Combox")
        self.Control_Combox.setObjectName("Control_Combox")
        self.Autodetect_combox.setObjectName("Autodetect_combox")

        self.AutoDetCom_ResCom_CtlCom.addWidget(self.Resource_Combox)
        self.AutoDetCom_ResCom_CtlCom.addWidget(self.Control_Combox)
        self.AutoDetCom_ResCom_CtlCom.addWidget(self.Autodetect_combox)
        self.AutoDetCom_ResCom_CtlCom.addWidget(self.Finish_combox)

        # 左下完整布局
        self.AutoDet_Res_Ctl_Layout = QHBoxLayout()
        self.AutoDet_Res_Ctl_Layout.addLayout(self.AutoDetBut_ResTit_CtlTit)
        self.AutoDet_Res_Ctl_Layout.addLayout(self.AutoDetCom_ResCom_CtlCom)

        # 完成后操作

        self.Finish_combox_res = ComboBox(Task_Interface)
        self.Finish_combox_cfg = ComboBox(Task_Interface)
        self.Finish_combox_layout = QHBoxLayout()

        self.Finish_combox_layout.addWidget(self.Finish_combox_res)
        self.Finish_combox_layout.addWidget(self.Finish_combox_cfg)

        self.Finish_combox_res.setObjectName("Finish_combox_res")
        self.Finish_combox_cfg.setObjectName("Finish_combox_cfg")

        # 启动/停止按钮和完成后操作标签

        self.S2But_FinLayout = QHBoxLayout()
        self.S2_Button = PushButton(Task_Interface)
        self.S2_Button.setObjectName("S2_Button")

        self.S2But_FinLayout.addWidget(self.S2_Button)
        self.S2But_FinLayout.addStretch()
        self.S2But_FinLayout.addLayout(self.Finish_combox_layout)

        # 左下完整布局
        self.FullLayout_LeftDown = QVBoxLayout()
        self.FullLayout_LeftDown.addLayout(self.AutoDet_Res_Ctl_Layout)
        self.FullLayout_LeftDown.addLayout(self.S2But_FinLayout)

        # 添加任务区布局
        self.AddMission_layout = QVBoxLayout()
        self.Main_Task_Label = QHBoxLayout()

        self.TaskName_Title_1 = BodyLabel(Task_Interface)
        self.TaskName_Title_1.setObjectName("TaskName_Title_1")
        self.TaskName_Title_1.setFixedSize(60, 30)

        self.SelectTask_Combox_1 = ComboBox(Task_Interface)
        self.SelectTask_Combox_1.setMaximumWidth(200)

        self.AddTask_Button = RightCheckButton(Task_Interface)
        self.AddTask_Button.setObjectName("AddTask_Button")
        self.AddTask_Button.setFixedSize(60, 30)

        self.Main_Task_Label.addWidget(self.TaskName_Title_1)
        self.Main_Task_Label.addWidget(self.SelectTask_Combox_1)
        self.Main_Task_Label.addWidget(self.AddTask_Button)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Plain)

        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.Shape.HLine)
        self.line1.setFrameShadow(QFrame.Shadow.Plain)

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
            QSizePolicy.Policy.Minimum   # 垂直策略根据内容自动调整
        )
        
        # doc区域
        self.doc_widget = QWidget()
        self.doc_layout = QVBoxLayout(self.doc_widget)
        self.doc_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,  # 水平策略保持不变
            QSizePolicy.Policy.Minimum     # 垂直策略根据内容自动调整
        )
        
        # 主滚动区域布局
        self.main_scroll_layout = QVBoxLayout(self.scroll_area_content)
        self.main_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_scroll_layout.addWidget(self.option_widget)
        self.main_scroll_layout.addWidget(self.doc_widget)
        
        self.scroll_area.setWidget(self.scroll_area_content)

        self.Option_area_Label = QVBoxLayout()
        self.Option_area_Label.addWidget(self.scroll_area, 1)

        self.AddMission_layout.addLayout(self.Main_Task_Label)
        self.AddMission_layout.addWidget(self.line)
        self.AddMission_layout.addLayout(self.Option_area_Label)

        # 左侧布局
        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.Shape.HLine)
        self.line2.setFrameShadow(QFrame.Shadow.Plain)

        self.left_layout = QVBoxLayout()
        self.left_layout.addLayout(self.AddMission_layout)
        self.left_layout.addWidget(self.line2)
        self.left_layout.addLayout(self.FullLayout_LeftDown)

        # 中间布局（包含任务列表）
        self.middle_layout = QVBoxLayout()
        self.Task_List = ListWidge_Menu_Draggable(self)

        self.Task_List.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)

        self.Delete_label = BodyLabel(self)
        self.Delete_label.setObjectName("Delete_label")
        self.Delete_label.setFixedHeight(30)
        self.Delete_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.Delete_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.Delete_label.setAcceptDrops(True)
        self.middle_layout.addWidget(self.Task_List)
        self.middle_layout.addWidget(self.Delete_label)

        # 右侧布局（包含文本编辑区域）
        self.scroll_area = ScrollArea(Task_Interface)
        self.scroll_area.setStyleSheet("background-color: transparent;")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)
        self.scroll_area.setWidgetResizable(True)
        
        self.right_layout = QVBoxLayout(self.content_widget)
        self.right_layout.addStretch()
        
        
        # 将子布局添加到主布局中
        self.main_layout.addLayout(self.left_layout, 3)
        self.main_layout.addLayout(self.middle_layout, 3)
        self.main_layout.addWidget(self.scroll_area, 3)

        QMetaObject.connectSlotsByName(Task_Interface)