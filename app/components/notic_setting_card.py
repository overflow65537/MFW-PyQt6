from typing import Union

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QFormLayout,
    QDialog,
    QSpacerItem,
    QSizePolicy,
)
from qfluentwidgets import (
    LineEdit,
    PrimaryPushButton,
    PushButton,
    BodyLabel,
    SettingCard,
    FluentIconBase,
)
from ..common.config import cfg


class NoticeType(QDialog):
    def __init__(self, parent=None, notice_type: str = None):
        super().__init__(parent)
        self.notice_type = notice_type
        self.setWindowTitle(self.notice_type)
        self.setObjectName("NoticeType")
        self.resize(900, 600)
        self.setMinimumSize(QSize(0, 0))

        # 创建主布局
        self.main_layout = QFormLayout(self)

        # 根据通知类型初始化界面元素
        self.init_noticetype()

        # 按钮布局
        button_layout = QHBoxLayout()
        self.okButton = PushButton(self.tr("OK"), self)
        self.clearButton = PushButton(self.tr("Clear"), self)

        # 垂直伸缩器
        vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        # 添加布局
        button_layout.addWidget(self.okButton)
        button_layout.addWidget(self.clearButton)
        self.main_layout.addItem(vertical_spacer)
        self.main_layout.addRow(button_layout)

        # 连接按钮事件
        self.okButton.clicked.connect(self.on_ok)
        self.clearButton.clicked.connect(self.on_clear)

    def init_noticetype(self):
        """根据通知类型初始化界面元素"""
        if self.notice_type == "DingTalk":
            self.add_dingtalk_fields()
        elif self.notice_type == "Lark":
            self.add_lark_fields()
        elif self.notice_type == "Qmsg":
            self.add_qmsg_fields()
        elif self.notice_type == "SMTP":
            self.add_smtp_fields()

    def save_noticetype(self):
        """保存通知类型"""
        if self.notice_type == "DingTalk":
            self.save_dingtalk_fields()
        elif self.notice_type == "Lark":
            self.save_lark_fields()
        elif self.notice_type == "Qmsg":
            self.save_qmsg_fields()
        elif self.notice_type == "SMTP":
            self.save_smtp_fields()

    def save_dingtalk_fields(self):
        """保存钉钉相关的输入框"""
        data = cfg.get(cfg.Notice_Webhook)
        data["DingTalk"]["url"] = self.dingtalk_url_input.text()
        data["DingTalk"]["secret"] = self.dingtalk_secret_input.text()
        cfg.set(cfg.Notice_Webhook, data)

    def save_lark_fields(self):
        """保存飞书相关的输入框"""
        data = cfg.get(cfg.Notice_Webhook)
        data["Lark"]["url"] = self.lark_url_input.text()
        data["Lark"]["secret"] = self.lark_secret_input.text()
        cfg.set(cfg.Notice_Webhook, data)

    def save_qmsg_fields(self):
        """保存 Qmsg 相关的输入框"""
        data = cfg.get(cfg.Notice_Qmsg)
        data["Server"] = self.sever_input.text()
        data["Key"] = self.key_input.text()
        data["UserQQ"] = self.user_qq_input.text()
        data["RobotQQ"] = self.robot_qq_input.text()
        cfg.set(cfg.Notice_Qmsg, data)

    def save_smtp_fields(self):
        """保存 SMTP 相关的输入框"""
        data = cfg.get(cfg.Notice_SMTP)
        data["ServerAddress"] = self.server_address_input.text()
        data["ServerPort"] = self.server_port_input.text()
        data["UserName"] = self.user_name_input.text()
        data["Password"] = self.password_input.text()
        data["SendMail"] = self.send_mail_input.text()
        data["ReceiveMail"] = self.receive_mail_input.text()
        cfg.set(cfg.Notice_SMTP, data)

    def add_dingtalk_fields(self):
        """添加钉钉相关的输入框"""
        dingtalk_url_title = BodyLabel(self)
        dingtalk_secret_title = BodyLabel(self)
        self.dingtalk_url_input = LineEdit(self)
        self.dingtalk_secret_input = LineEdit(self)

        dingtalk_url_title.setText(self.tr("DingTalk Webhook URL:"))
        dingtalk_secret_title.setText(self.tr("DingTalk Secret:"))

        self.main_layout.addRow(dingtalk_url_title, self.dingtalk_url_input)
        self.main_layout.addRow(dingtalk_secret_title, self.dingtalk_secret_input)

    def add_lark_fields(self):
        """添加飞书相关的输入框"""
        lark_url_title = BodyLabel(self)
        lark_secret_title = BodyLabel(self)
        self.lark_url_input = LineEdit(self)
        self.lark_secret_input = LineEdit(self)

        lark_url_title.setText(self.tr("Lark Webhook URL:"))
        lark_secret_title.setText(self.tr("Lark App Key:"))

        self.main_layout.addRow(lark_url_title, self.lark_url_input)
        self.main_layout.addRow(lark_secret_title, self.lark_secret_input)

    def add_qmsg_fields(self):
        """添加 Qmsg 相关的输入框"""
        sever_title = BodyLabel(self)
        key_title = BodyLabel(self)
        user_qq_title = BodyLabel(self)
        robot_qq_title = BodyLabel(self)

        self.sever_input = LineEdit(self)
        self.key_input = LineEdit(self)
        self.user_qq_input = LineEdit(self)
        self.robot_qq_input = LineEdit(self)

        sever_title.setText(self.tr("Server:"))
        key_title.setText(self.tr("Key:"))
        user_qq_title.setText(self.tr("User QQ:"))
        robot_qq_title.setText(self.tr("Robot QQ:"))

        self.main_layout.addRow(sever_title, self.sever_input)
        self.main_layout.addRow(key_title, self.key_input)
        self.main_layout.addRow(user_qq_title, self.user_qq_input)
        self.main_layout.addRow(robot_qq_title, self.robot_qq_input)

    def add_smtp_fields(self):
        """添加 SMTP 相关的输入框"""
        server_address_title = BodyLabel(self)
        server_port_title = BodyLabel(self)
        user_name_title = BodyLabel(self)
        password_title = BodyLabel(self)
        send_mail_title = BodyLabel(self)
        receive_mail_title = BodyLabel(self)

        self.server_address_input = LineEdit(self)
        self.server_port_input = LineEdit(self)
        self.user_name_input = LineEdit(self)
        self.password_input = LineEdit(self)
        self.send_mail_input = LineEdit(self)
        self.receive_mail_input = LineEdit(self)

        server_address_title.setText(self.tr("Server Address:"))
        server_port_title.setText(self.tr("Server Port:"))
        user_name_title.setText(self.tr("User Name:"))
        password_title.setText(self.tr("Password:"))
        send_mail_title.setText(self.tr("Send Mail:"))
        receive_mail_title.setText(self.tr("Receive Mail:"))

        self.main_layout.addRow(server_address_title, self.server_address_input)
        self.main_layout.addRow(server_port_title, self.server_port_input)
        self.main_layout.addRow(user_name_title, self.user_name_input)
        self.main_layout.addRow(password_title, self.password_input)
        self.main_layout.addRow(send_mail_title, self.send_mail_input)
        self.main_layout.addRow(receive_mail_title, self.receive_mail_input)

    def on_ok(self):
        self.save_noticetype()
        print(f"保存{self.notice_type}设置")
        self.close()

    def on_clear(self):
        print("Clear button clicked!")
        self.close()


class CustomClickButton(PrimaryPushButton):
    rightClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        super().mousePressEvent(event)


class NoticeButtonSettingCard(SettingCard):
    clicked = pyqtSignal()

    def __init__(
        self,
        text,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        notice_type: str = None,
        content=None,
        parent=None,
    ):
        self.notice_type = notice_type
        super().__init__(icon, title, content, parent)

        # 创建标签

        if self.notice_type == "DingTalk":
            print(cfg.get(cfg.Notice_Webhook))
            self.notice = cfg.get(cfg.Notice_Webhook)["DingTalk"]
        elif self.notice_type == "Lark":
            self.notice = cfg.get(cfg.Notice_Webhook)["Lark"]
        elif self.notice_type == "Qmsg":
            self.notice = cfg.get(cfg.Notice_Qmsg)
        elif self.notice_type == "SMTP":
            self.notice = cfg.get(cfg.Notice_SMTP)

        self.label = BodyLabel(self)
        if self.notice["status"]:
            self.label.setText(self.notice_type + self.tr("Notification Enabled"))
        else:
            self.label.setText(self.notice_type + self.tr("Notification disabled"))
        self.hBoxLayout.addWidget(self.label)

        # 使用自定义右键按钮
        self.button = CustomClickButton(text, self)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.button.clicked.connect(self.showDialog)
        self.button.rightClicked.connect(self.onRightClick)  # 连接右键点击信号

    def showDialog(self):
        w = NoticeType(self, self.notice_type)
        w.exec()

    def onRightClick(self):
        # 处理右键点击事件
        if self.label.text() == self.tr("Notification Enabled"):
            self.label.setText(self.tr("Notification disabled"))
            data = self.notice
            data["status"] = False
            if self.notice_type == "DingTalk":
                original_data = cfg.get(cfg.Notice_Webhook)
                original_data["DingTalk"] = data
                cfg.set(cfg.Notice_Webhook,original_data)
            elif self.notice_type == "Lark":
                original_data = cfg.get(cfg.Notice_Webhook)
                original_data["Lark"] = data
                cfg.set(cfg.Notice_Webhook,original_data)
            elif self.notice_type == "Qmsg":
                original_data = data
                cfg.set(cfg.Notice_Qmsg,original_data)
            elif self.notice_type == "SMTP":
                original_data = data
                cfg.set(cfg.Notice_SMTP,original_data)
        else:
            self.label.setText(self.tr("Notification Enabled"))
            data = self.notice
            data["status"] = True
            if self.notice_type == "DingTalk":
                original_data = cfg.get(cfg.Notice_Webhook)
                original_data["DingTalk"] = data
                cfg.set(cfg.Notice_Webhook,original_data)
            elif self.notice_type == "Lark":
                original_data = cfg.get(cfg.Notice_Webhook)
                original_data["Lark"] = data
                cfg.set(cfg.Notice_Webhook,original_data)
            elif self.notice_type == "Qmsg":
                original_data = data
                cfg.set(cfg.Notice_Qmsg,original_data)
            elif self.notice_type == "SMTP":
                original_data = data
                cfg.set(cfg.Notice_SMTP,original_data)
