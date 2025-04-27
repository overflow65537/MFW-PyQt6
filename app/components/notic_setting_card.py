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
    SwitchButton,
    PasswordLineEdit,
    InfoBar,
    InfoBarPosition,
)
from ..common.config import cfg
from ..utils.logger import logger
from ..utils.notice import lark_send, dingtalk_send, WxPusher_send, SMTP_send, QYWX_send


class NoticeType(QDialog):
    def __init__(self, parent=None, notice_type: str = ""):
        super().__init__(parent)
        self.notice_type = notice_type
        self.setWindowTitle(self.notice_type)
        self.setObjectName("NoticeType")
        self.resize(400, 300)
        self.setMinimumSize(QSize(0, 0))

        # 创建主布局
        self.main_layout = QFormLayout(self)

        # 根据通知类型初始化界面元素
        self.init_noticetype()

        # 按钮布局
        button_layout = QHBoxLayout()
        self.okButton = PushButton(self.tr("OK"), self)
        self.testButton = PushButton(self.tr("test"), self)
        self.clearButton = PushButton(self.tr("Clear"), self)

        # 垂直伸缩器
        vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        # 添加布局
        button_layout.addWidget(self.okButton)
        button_layout.addWidget(self.testButton)
        button_layout.addWidget(self.clearButton)
        self.main_layout.addItem(vertical_spacer)
        self.main_layout.addRow(button_layout)

        # 连接按钮事件
        self.okButton.clicked.connect(self.on_ok)
        self.testButton.clicked.connect(self.bind_test_button)
        self.clearButton.clicked.connect(self.on_clear)

    def bind_test_button(self):
        test_msg = {"title": "Test Title", "text": "Test Text"}
        try:
            # 创建一个字典来映射通知类型和发送函数
            notification_methods = {
                "DingTalk": dingtalk_send,
                "Lark": lark_send,
                "SMTP": SMTP_send,
                "WxPusher": WxPusher_send,
                "QYWX": QYWX_send,
            }

            # 获取对应的发送函数
            send_method = notification_methods.get(self.notice_type)

            if send_method:
                if send_method(test_msg, True):
                    self.shwo_success(
                        f"{self.notice_type}" + self.tr("send test message success")
                    )
                else:
                    self.show_error(
                        f"{self.notice_type}" + self.tr("send test message failed")
                    )

        except Exception as e:
            logger.error(f"测试 {self.notice_type} Error: {e}")
            self.show_error(str(e))

    def show_error(self, error_message):
        InfoBar.error(
            title=self.tr("Error"),
            content=error_message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self,
        )

    def shwo_success(self, success_message):
        InfoBar.success(
            title=self.tr("Success"),
            content=success_message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self,
        )

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
        elif self.notice_type == "WxPusher":
            self.add_wxpusher_fields()
        elif self.notice_type == "QYWX":
            self.add_qywx_fields()

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
        elif self.notice_type == "WxPusher":
            self.save_wxpusher_fields()
        elif self.notice_type == "QYWX":
            self.save_qywx_fields()

    def save_dingtalk_fields(self):
        """保存钉钉相关的输入框"""

        cfg.set(cfg.Notice_DingTalk_url, self.dingtalk_url_input.text())
        cfg.set(cfg.Notice_DingTalk_secret, self.dingtalk_secret_input.text())
        cfg.set(cfg.Notice_DingTalk_status, self.dingtalk_status_switch.isChecked())

    def save_lark_fields(self):
        """保存飞书相关的输入框"""
        cfg.set(cfg.Notice_Lark_url, self.lark_url_input.text())
        cfg.set(cfg.Notice_Lark_secret, self.lark_secret_input.text())
        cfg.set(cfg.Notice_Lark_status, self.lark_status_switch.isChecked())

    def save_qmsg_fields(self):
        """保存 Qmsg 相关的输入框"""
        cfg.set(cfg.Notice_Qmsg_sever, self.sever_input.text())
        cfg.set(cfg.Notice_Qmsg_key, self.key_input.text())
        cfg.set(cfg.Notice_Qmsg_user_qq, self.user_qq_input.text())
        cfg.set(cfg.Notice_Qmsg_robot_qq, self.robot_qq_input.text())
        cfg.set(cfg.Notice_Qmsg_status, self.qmsg_status_switch.isChecked())

    def save_smtp_fields(self):
        """保存 SMTP 相关的输入框"""
        cfg.set(cfg.Notice_SMTP_sever_address, self.server_address_input.text())
        cfg.set(cfg.Notice_SMTP_sever_port, self.server_port_input.text())
        cfg.set(cfg.Notice_SMTP_user_name, self.user_name_input.text())
        cfg.set(cfg.Notice_SMTP_password, self.password_input.text())
        cfg.set(cfg.Notice_SMTP_receive_mail, self.receive_mail_input.text())
        cfg.set(cfg.Notice_SMTP_status, self.smtp_status_switch.isChecked())

    def save_wxpusher_fields(self):
        """保存 WxPusher 相关的输入框"""
        cfg.set(cfg.Notice_WxPusher_SPT_token, self.wxpusher_spt_input.text())
        cfg.set(cfg.Notice_WxPusher_status, self.wxpusher_status_switch.isChecked())

    def save_qywx_fields(self):
        """保存 QYWX 相关的输入框"""
        cfg.set(cfg.Notice_QYWX_key, self.qywx_key_input.text())
        cfg.set(cfg.Notice_QYWX_status, self.qywx_status_switch.isChecked())

    def add_dingtalk_fields(self):
        """添加钉钉相关的输入框"""
        dingtalk_url_title = BodyLabel(self)
        dingtalk_secret_title = BodyLabel(self)
        dingtalk_status_title = BodyLabel(self)
        self.dingtalk_url_input = LineEdit(self)
        self.dingtalk_secret_input = PasswordLineEdit(self)
        self.dingtalk_status_switch = SwitchButton(self)

        dingtalk_url_title.setText(self.tr("DingTalk Webhook URL:"))
        dingtalk_secret_title.setText(self.tr("DingTalk Secret:"))
        dingtalk_status_title.setText(self.tr("DingTalk Status:"))

        self.dingtalk_url_input.setText(cfg.get(cfg.Notice_DingTalk_url))
        self.dingtalk_secret_input.setText(cfg.get(cfg.Notice_DingTalk_secret))
        self.dingtalk_status_switch.setChecked(cfg.get(cfg.Notice_DingTalk_status))

        self.main_layout.addRow(dingtalk_url_title, self.dingtalk_url_input)
        self.main_layout.addRow(dingtalk_secret_title, self.dingtalk_secret_input)
        self.main_layout.addRow(dingtalk_status_title, self.dingtalk_status_switch)

    def add_lark_fields(self):
        """添加飞书相关的输入框"""
        lark_url_title = BodyLabel(self)
        lark_secret_title = BodyLabel(self)
        lark_status_title = BodyLabel(self)
        self.lark_url_input = LineEdit(self)
        self.lark_secret_input = PasswordLineEdit(self)
        self.lark_status_switch = SwitchButton(self)

        lark_url_title.setText(self.tr("Lark Webhook URL:"))
        lark_secret_title.setText(self.tr("Lark App Key:"))
        lark_status_title.setText(self.tr("Lark Status:"))

        self.lark_url_input.setText(cfg.get(cfg.Notice_Lark_url))
        self.lark_secret_input.setText(cfg.get(cfg.Notice_Lark_secret))
        self.lark_status_switch.setChecked(cfg.get(cfg.Notice_Lark_status))

        self.main_layout.addRow(lark_url_title, self.lark_url_input)
        self.main_layout.addRow(lark_secret_title, self.lark_secret_input)
        self.main_layout.addRow(lark_status_title, self.lark_status_switch)

    def add_qmsg_fields(self):
        """添加 Qmsg 相关的输入框"""
        sever_title = BodyLabel(self)
        key_title = BodyLabel(self)
        user_qq_title = BodyLabel(self)
        robot_qq_title = BodyLabel(self)
        qmsg_status_title = BodyLabel(self)

        self.sever_input = LineEdit(self)
        self.key_input = PasswordLineEdit(self)
        self.user_qq_input = LineEdit(self)
        self.robot_qq_input = LineEdit(self)
        self.qmsg_status_switch = SwitchButton(self)

        sever_title.setText(self.tr("Server:"))
        key_title.setText(self.tr("Key:"))
        user_qq_title.setText(self.tr("User QQ:"))
        robot_qq_title.setText(self.tr("Robot QQ:"))
        qmsg_status_title.setText(self.tr("Qmsg Status:"))

        self.sever_input.setText(cfg.get(cfg.Notice_Qmsg_sever))
        self.key_input.setText(cfg.get(cfg.Notice_Qmsg_key))
        self.user_qq_input.setText(cfg.get(cfg.Notice_Qmsg_user_qq))
        self.robot_qq_input.setText(cfg.get(cfg.Notice_Qmsg_robot_qq))
        self.qmsg_status_switch.setChecked(cfg.get(cfg.Notice_Qmsg_status))

        self.main_layout.addRow(sever_title, self.sever_input)
        self.main_layout.addRow(key_title, self.key_input)
        self.main_layout.addRow(user_qq_title, self.user_qq_input)
        self.main_layout.addRow(robot_qq_title, self.robot_qq_input)
        self.main_layout.addRow(qmsg_status_title, self.qmsg_status_switch)

    def add_smtp_fields(self):
        """添加 SMTP 相关的输入框"""
        server_address_title = BodyLabel(self)
        server_port_title = BodyLabel(self)
        user_name_title = BodyLabel(self)
        password_title = BodyLabel(self)
        receive_mail_title = BodyLabel(self)
        smtp_status_title = BodyLabel(self)

        self.server_address_input = LineEdit(self)
        self.server_port_input = LineEdit(self)
        self.user_name_input = LineEdit(self)
        self.password_input = PasswordLineEdit(self)
        self.receive_mail_input = LineEdit(self)
        self.smtp_status_switch = SwitchButton(self)

        server_address_title.setText(self.tr("Server Address:"))
        server_port_title.setText(self.tr("Server Port:"))
        user_name_title.setText(self.tr("User Name:"))
        password_title.setText(self.tr("Password:"))
        receive_mail_title.setText(self.tr("Receive Mail:"))
        smtp_status_title.setText(self.tr("SMTP Status:"))

        self.server_address_input.setText(cfg.get(cfg.Notice_SMTP_sever_address))
        self.server_port_input.setText(cfg.get(cfg.Notice_SMTP_sever_port))
        self.user_name_input.setText(cfg.get(cfg.Notice_SMTP_user_name))
        self.password_input.setText(cfg.get(cfg.Notice_SMTP_password))
        self.receive_mail_input.setText(cfg.get(cfg.Notice_SMTP_receive_mail))
        self.smtp_status_switch.setChecked(cfg.get(cfg.Notice_SMTP_status))

        self.main_layout.addRow(server_address_title, self.server_address_input)
        self.main_layout.addRow(server_port_title, self.server_port_input)
        self.main_layout.addRow(user_name_title, self.user_name_input)
        self.main_layout.addRow(password_title, self.password_input)
        self.main_layout.addRow(receive_mail_title, self.receive_mail_input)
        self.main_layout.addRow(smtp_status_title, self.smtp_status_switch)

    def add_wxpusher_fields(self):
        """添加 WxPusher 相关的输入框"""
        wxpusher_spt_title = BodyLabel(self)
        wxpusher_status_title = BodyLabel(self)

        self.wxpusher_spt_input = PasswordLineEdit(self)
        self.wxpusher_status_switch = SwitchButton(self)

        wxpusher_spt_title.setText(self.tr("WxPusher Spt:"))
        wxpusher_status_title.setText(self.tr("WxPusher Status:"))

        self.wxpusher_spt_input.setText(cfg.get(cfg.Notice_WxPusher_SPT_token))
        self.wxpusher_status_switch.setChecked(cfg.get(cfg.Notice_WxPusher_status))

        self.main_layout.addRow(wxpusher_spt_title, self.wxpusher_spt_input)
        self.main_layout.addRow(wxpusher_status_title, self.wxpusher_status_switch)

    def add_qywx_fields(self):
        """添加 企业微信 相关的输入框"""
        qywx_key_title = BodyLabel(self)
        qywx_status_title = BodyLabel(self)

        self.qywx_key_input = PasswordLineEdit(self)
        self.qywx_status_switch = SwitchButton(self)

        qywx_key_title.setText(self.tr("QYWXbot Key"))
        qywx_status_title.setText(self.tr("QYWXbot Status:"))

        self.qywx_key_input.setText(cfg.get(cfg.Notice_QYWX_key))
        self.qywx_status_switch.setChecked(cfg.get(cfg.Notice_QYWX_status))

        self.main_layout.addRow(qywx_key_title, self.qywx_key_input)
        self.main_layout.addRow(qywx_status_title, self.qywx_status_switch)

    def on_ok(self):
        self.save_noticetype()
        logger.info(f"保存{self.notice_type}设置")
        self.accept()

    def on_clear(self):
        logger.info("关闭通知设置对话框")
        self.close()


class NoticeButtonSettingCard(SettingCard):
    clicked = pyqtSignal()

    def __init__(
        self,
        text,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        notice_type: str = "",
        content=None,
        parent=None,
    ):
        self.notice_type = notice_type

        super().__init__(icon, title, content, parent)
        self.rewirte_text()
        # 创建标签

        self.button = PrimaryPushButton(text, self)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.button.clicked.connect(self.showDialog)

    def rewirte_text(self):
        notification_types = {
            "DingTalk": cfg.Notice_DingTalk_status,
            "Lark": cfg.Notice_Lark_status,
            "Qmsg": cfg.Notice_Qmsg_status,
            "SMTP": cfg.Notice_SMTP_status,
            "WxPusher": cfg.Notice_WxPusher_status,
            "QYWX": cfg.Notice_QYWX_status,
        }

        if self.notice_type in notification_types:
            status = cfg.get(notification_types[self.notice_type])
            self.setContent(
                self.notice_type + self.tr("Notification Enabled")
                if status
                else self.notice_type + self.tr("Notification disabled")
            )

    def showDialog(self):
        w = NoticeType(self, self.notice_type)
        if w.exec():
            self.rewirte_text()
