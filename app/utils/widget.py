#   This file is part of MFW-ChainFlow Assistant.

#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.

#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

import re
from PySide6.QtWidgets import (
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QDialog,
    QSpacerItem,
    QSizePolicy,
    QAbstractItemView,
    QFileDialog,
)
from PySide6.QtGui import (
    QIcon,
    QColor,
    QDrag,
    QDragMoveEvent,
    QDropEvent,
    QDragEnterEvent,
    QMouseEvent,
    QContextMenuEvent,
    QCursor,
    QIntValidator,
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData

from qfluentwidgets import (
    FluentIconBase,
    SwitchButton,
    IndicatorPosition,
    SettingCard,
    MessageBoxBase,
    IndeterminateProgressBar,
    SubtitleLabel,
    ProgressBar,
    BodyLabel,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    PasswordLineEdit,
    InfoBar,
    InfoBarPosition,
    ListWidget,
    RoundMenu,
    Action,
    MenuAnimationType,
    ToolButton,
    ComboBox,
    ConfigItem,
    qconfig,
    FluentIconBase,
    EditableComboBox,
)
from qfluentwidgets import FluentIcon as FIF

import traceback
import os
from typing import Union, Dict, List

from ..common.signal_bus import signalBus
from app.utils.logger import logger
from ..utils.tool import (
    Read_Config,
    Save_Config,
    Get_Values_list_Option,
    Get_Values_list2,
    access_nested_dict,
    find_key_by_value,
    rewrite_contorller,
    delete_contorller,
)
from ..utils.notice import lark_send, dingtalk_send, WxPusher_send, SMTP_send, QYWX_send
from ..common.config import cfg
from ..common.maa_config_data import maa_config_data
from ..utils.update import DownloadBundle


class SwitchSettingCardCustom(SettingCard):
    """自定义切换设置卡片"""

    checkedChanged = Signal(bool)

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title: str,
        target: str,
        content: str = "",
        parent=None,
    ):
        super().__init__(icon, title, content, parent)
        self.target = target
        self.switchButton = SwitchButton(self.tr("Off"), self, IndicatorPosition.RIGHT)

        # 将切换按钮添加到布局
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        # 读取初始状态并设置切换按钮状态
        self.initialize_switch_button()

        # 连接信号和槽
        self.switchButton.checkedChanged.connect(self._onCheckedChanged)

    def initialize_switch_button(self):
        """初始化切换按钮的状态"""
        try:
            config_path = os.path.join(
                os.getcwd(), "config", "custom_setting_config.json"
            )
            data = Read_Config(config_path)
            initial_state = data.get(self.target, False)  # 默认为 False（关闭状态）
            self.switchButton.setChecked(initial_state)
        except FileNotFoundError:
            # 如果文件不存在，将切换按钮设置为默认关闭状态
            self.switchButton.setChecked(False)
            Save_Config(
                os.path.join(os.getcwd(), "config", "custom_setting_config.json"),
                {self.target: False},
            )

    def _onCheckedChanged(self, isChecked: bool):
        """处理切换按钮状态变化"""
        try:
            config_path = os.path.join(
                os.getcwd(), "config", "custom_setting_config.json"
            )
            data = Read_Config(config_path)
            data[self.target] = isChecked
            Save_Config(config_path, data)
            self.checkedChanged.emit(isChecked)  # 发出信号通知状态变化
        except Exception as e:
            logger.info(f"保存设置时出错: {e}")


def show_error_message():
    """显示错误消息框"""
    logger.exception("发生了一个异常：")
    traceback_info = traceback.format_exc()

    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("错误")
    msg_box.setText(f"发生了一个异常：\n{str(traceback_info)}")

    msg_box.setWindowIcon(QIcon("./icon/ERROR.png"))

    msg_box.exec()


class ShowDownload(MessageBoxBase):
    """下载进度对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        transparent_color = QColor(255, 255, 255, 0)
        self.setMaskColor(transparent_color)
        self.titleLabel = SubtitleLabel(self.tr("Downloading..."), self)

        self.widget.setMinimumWidth(350)
        self.widget.setMinimumHeight(100)
        self.progressBar_layout = QVBoxLayout()
        self.progressBar = ProgressBar(self)
        self.inProgressBar = IndeterminateProgressBar(self)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.hide()
        self.progressBar_layout.addWidget(self.progressBar)
        self.progressBar_layout.addWidget(self.inProgressBar)
        self.progressBar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cancelButton.setText(self.tr("Cancel"))
        # 进度数字标签
        self.progressLabel = BodyLabel("0 / 0 " + self.tr("bytes"), self)
        self.progressLabel.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addLayout(self.progressBar_layout)
        self.viewLayout.addWidget(self.progressLabel)
        self.yesButton.hide()

        signalBus.bundle_download_progress.connect(self.setProgress)
        signalBus.bundle_download_finished.connect(self.close)

        signalBus.mirror_bundle_download_progress.connect(self.setProgress)
        signalBus.mirror_bundle_download_finished.connect(self.close)

        signalBus.download_self_progress.connect(self.setProgress)
        signalBus.download_self_finished.connect(self.chooseclose)

        self.cancelButton.clicked.connect(self.cancelDownload)

    def setProgress(self, downloaded, total):
        if total == 0:
            self.progressBar.setValue(0)
            self.progressLabel.setText("0 B")
        else:
            self.progressBar.show()
            self.inProgressBar.hide()
            progress_value = int((downloaded / total) * 100)
            self.progressBar.setValue(progress_value)

            total_str = self.format_size(total)
            downloaded_str = self.format_size(downloaded)
            self.progressLabel.setText(f"{downloaded_str} / {total_str}")

    def chooseclose(self, status: dict):
        if status.get("status") != "info" and status.get("status") != "failed_info":
            self.close()

    def format_size(self, size):

        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.2f} {units[unit_index]}"

    def cancelDownload(self):
        signalBus.bundle_download_stopped.emit()
        signalBus.download_self_stopped.emit()
        signalBus.mirror_bundle_download_stopped.emit()
        signalBus.update_download_stopped.emit()
        self.close()


class RightCheckButton(PushButton):
    rightClicked = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        super().mousePressEvent(event)


class RightCheckPrimaryPushButton(PrimaryPushButton):
    rightClicked = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        super().mousePressEvent(event)


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
        """添加 企业微信机器人 相关的输入框"""
        qywx_key_title = BodyLabel(self)
        qywx_status_title = BodyLabel(self)

        self.qywx_key_input = PasswordLineEdit(self)
        self.qywx_status_switch = SwitchButton(self)

        qywx_key_title.setText(self.tr("QYWXbot Key:"))
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
    clicked = Signal()

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


class ListWidge_Menu_Draggable(ListWidget):
    def __init__(self, parent=None):
        super(ListWidge_Menu_Draggable, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def get_task_list_widget(self) -> list:
        items = []
        for i in range(self.count()):
            item = self.item(i)
            if item is not None:
                items.append(item.text())
        return items

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(e.pos())
            if item is None:
                self.clearSelection()
                signalBus.dragging_finished.emit()
            else:
                super(ListWidge_Menu_Draggable, self).mousePressEvent(e)
        else:
            super(ListWidge_Menu_Draggable, self).mousePressEvent(e)

    def contextMenuEvent(self, e: QContextMenuEvent):
        menu = RoundMenu(parent=self)

        selected_row = self.currentRow()

        action_move_up = Action(FIF.UP, self.tr("Move Up"))
        action_move_down = Action(FIF.DOWN, self.tr("Move Down"))
        action_delete = Action(FIF.DELETE, self.tr("Delete"))
        action_delete_all = Action(FIF.DELETE, self.tr("Delete All"))

        if selected_row == -1:
            action_move_up.setEnabled(False)
            action_move_down.setEnabled(False)
            action_delete.setEnabled(False)

        action_move_up.triggered.connect(self.Move_Up)
        action_move_down.triggered.connect(self.Move_Down)
        action_delete.triggered.connect(self.Delete_Task)
        action_delete_all.triggered.connect(self.Delete_All_Task)

        menu.addAction(action_move_up)
        menu.addAction(action_move_down)
        menu.addAction(action_delete)
        menu.addAction(action_delete_all)

        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)

    def Delete_All_Task(self):
        self.clear()
        maa_config_data.config["task"] = []
        Save_Config(maa_config_data.config_path, maa_config_data.config)
        signalBus.update_task_list.emit()
        signalBus.dragging_finished.emit()

    def Delete_Task(self):
        Select_Target = self.currentRow()

        if Select_Target == -1:
            return

        self.takeItem(Select_Target)
        Task_List = Get_Values_list2(maa_config_data.config_path, "task")

        # 只有在有效索引时更新任务配置
        if 0 <= Select_Target < len(Task_List):
            del Task_List[Select_Target]
            self.update_task_config(Task_List)

        self.update_selection(Select_Target)

        signalBus.update_task_list.emit()
        signalBus.dragging_finished.emit()

    def Move_Up(self):
        Select_Target = self.currentRow()
        self.move_task(Select_Target, Select_Target - 1)

    def Move_Down(self):
        Select_Target = self.currentRow()
        self.move_task(Select_Target, Select_Target + 1)

    def move_task(self, from_index, to_index):
        if (
            from_index < 0
            or from_index >= self.count()
            or to_index < 0
            or to_index >= self.count()
        ):
            return  # 索引无效，直接返回

        # 执行移动操作
        Select_Task = maa_config_data.config["task"].pop(from_index)
        maa_config_data.config["task"].insert(to_index, Select_Task)
        Save_Config(maa_config_data.config_path, maa_config_data.config)

        self.clear()
        self.addItems(Get_Values_list_Option(maa_config_data.config_path, "task"))
        self.setCurrentRow(to_index)

        signalBus.update_task_list.emit()
        signalBus.dragging_finished.emit()

    def update_task_config(self, Task_List):
        maa_config_data.config["task"] = Task_List
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def update_selection(self, Select_Target):
        if Select_Target == 0 and self.count() > 0:
            self.setCurrentRow(Select_Target)
        elif Select_Target != -1 and self.count() > 1:
            self.setCurrentRow(Select_Target - 1)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is not None:
            item_rect = self.visualItemRect(item)
            pixmap = self.viewport().grab(item_rect)

            drag = QDrag(self)
            mimeData = QMimeData()
            mimeData.setText(item.text())

            drag.setMimeData(mimeData)
            drag.setPixmap(pixmap)
            drag.setHotSpot(self.mapFromGlobal(QCursor.pos()) - item_rect.topLeft())

            drag.exec(supportedActions)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.proposedAction() == Qt.DropAction.MoveAction:
            # 获取拖拽开始的索引
            source_item = self.currentItem()
            if source_item is None:
                super(ListWidge_Menu_Draggable, self).dropEvent(event)
                return

            begin = self.row(source_item)

            # 获取拖拽结束的索引
            position = event.position().toPoint()
            dragged_item = self.itemAt(position)
            end = self.row(dragged_item) if dragged_item else self.count()

            if begin != end:  # 只有在移动操作时更新任务配置
                task_list = maa_config_data.config["task"]
                if 0 <= begin < len(task_list) and 0 <= end < len(task_list):
                    # 移动任务配置
                    task_to_move = task_list.pop(begin)
                    task_list.insert(end, task_to_move)
                    maa_config_data.config["task"] = task_list
                    Save_Config(maa_config_data.config_path, maa_config_data.config)

                    signalBus.update_task_list.emit()
                    self.setCurrentRow(end)
                    signalBus.dragging_finished.emit()
        super(ListWidge_Menu_Draggable, self).dropEvent(event)
        signalBus.dragging_finished.emit()


class LineEditCard(SettingCard):
    """设置中的输入框卡片"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title: str,
        holderText: str = "",
        target: str = "",
        content=None,
        parent=None,
        is_passwork: bool = False,
        num_only=True,
        button: bool = False,
        button_type: str = "",
        button_text: str = "",
    ):
        """
        初始化输入框卡片。

        :param icon: 图标
        :param title: 标题
        :param holderText: 占位符文本
        :param target: 修改目标（custom页面要用）
        :param content: 内容
        :param parent: 父级控件
        :param num_only: 是否只能输入数字
        """
        super().__init__(icon, title, content, parent)

        self.target = target
        if is_passwork:
            self.lineEdit = PasswordLineEdit(self)
        else:
            self.lineEdit = LineEdit(self)
        if button_type == "primary":
            self.button = RightCheckPrimaryPushButton(button_text, self)
            self.button.rightClicked.connect(self._on_right_clicked)
        else:
            self.toolbutton = ToolButton(FIF.FOLDER_ADD, self)

        # 设置布局
        self.hBoxLayout.addWidget(self.lineEdit, 0)
        self.hBoxLayout.addSpacing(16)

        if button:
            if button_type == "primary":
                self.hBoxLayout.addWidget(self.button, 0)
            else:
                self.hBoxLayout.addWidget(self.toolbutton, 0)
            self.hBoxLayout.addSpacing(16)
            self.lineEdit.setFixedWidth(300)

        else:
            self.toolbutton.hide()
        # 设置占位符文本

        self.lineEdit.setText(str(holderText))

        # 设置输入限制
        if num_only:
            self.lineEdit.setValidator(QIntValidator())

        # 连接文本变化信号
        self.lineEdit.textChanged.connect(self._on_text_changed)

    def _on_right_clicked(self):
        """处理右键点击事件"""
        self.lineEdit.setEnabled(True)

    def _on_text_changed(self):
        """处理文本变化事件"""
        text = self.lineEdit.text()

        if self.target != "":
            self._save_text_to_config(text)

    def _save_text_to_config(self, text: str):
        """将文本保存到配置文件"""
        try:
            config_path = os.path.join(
                os.getcwd(), "config", "custom_setting_config.json"
            )
            data = Read_Config(config_path)
            data[self.target] = text
            Save_Config(config_path, data)
        except Exception as e:
            logger.warning(f"保存配置时出错: {e}")


class DoubleButtonSettingCard(SettingCard):
    """Setting card with a push button"""

    clicked = Signal()
    clicked2 = Signal()

    def __init__(
        self,
        text,
        text2,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        configItem: ConfigItem | None = None,
        content=None,
        parent=None,
    ):
        """
        Parameters
        ----------
        text: str
            the text of push button
        text2: str
            the text of push button
        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        parent: QWidget
            parent widget
        """
        super().__init__(icon, title, content, parent)
        self.button = PrimaryPushButton(text, self)
        self.button2 = PrimaryPushButton(text2, self)
        self.combobox = ComboBox(self)

        self.hBoxLayout.addWidget(self.combobox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.button2, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)

        self.combobox.addItems(
            [
                self.tr("stable"),
                self.tr("beta"),
                self.tr("alpha"),
            ]
        )

        self.button.clicked.connect(self.clicked)
        self.button2.clicked.connect(self.clicked2)
        self.combobox.currentIndexChanged.connect(self.setValue)
        self.configItem = configItem
        if configItem:
            self.setValue(qconfig.get(configItem))
            configItem.valueChanged.connect(self.setValue)

    def setValue(self, value):
        if self.configItem:
            qconfig.set(self.configItem, value)


class ComboWithActionSettingCard(SettingCard):
    """Setting card with a push button"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        res=False,
        content=None,
        parent=None,
    ):

        super().__init__(icon, title, content, parent)
        self.add_button = ToolButton(FIF.ADD, self)
        self.delete_button = ToolButton(FIF.DELETE, self)
        if res:
            self.combox = ComboBox(self)
            self.combox.setObjectName("combox")
            self.delete_button.setObjectName("delete_button")
            self.add_button.setObjectName("add_button")
        else:
            self.combox = EditableComboBox(self)
            # 设置占用最小宽度
            self.combox.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )

        self.hBoxLayout.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.combox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.delete_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class ClickableLabel(BodyLabel):

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            signalBus.dragging_finished.emit()
        super().mousePressEvent(event)
        signalBus.dragging_finished.emit()


class CustomMessageBox(MessageBoxBase):
    """Custom message box"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.download_bundle = DownloadBundle()
        signalBus.bundle_download_stopped.connect(self.download_bundle.stop)
        transparent_color = QColor(255, 255, 255, 0)
        self.setMaskColor(transparent_color)
        self.folder = None
        self.status = 0
        self.titleLabel = SubtitleLabel(self.tr("choose Resource"), self)

        self.name_layout = QHBoxLayout()
        self.name_LineEdit = LineEdit(self)
        self.name_LineEdit.setPlaceholderText(self.tr("Enter the name of the resource"))
        self.name_LineEdit.setClearButtonEnabled(True)

        self.name_layout.addWidget(self.name_LineEdit)

        self.path_layout = QHBoxLayout()
        self.path_LineEdit = LineEdit(self)
        self.path_LineEdit.setPlaceholderText(self.tr("Enter the path of the resource"))
        self.path_LineEdit.setClearButtonEnabled(True)

        self.path_layout.addWidget(self.path_LineEdit)
        self.resourceButton = ToolButton(FIF.FOLDER_ADD, self)
        self.resourceButton.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.resourceButton.clicked.connect(self.type_resource_name)
        signalBus.download_finished.connect(self.download_finished)

        self.path_layout.addWidget(self.resourceButton)

        self.update_LineEdit = LineEdit(self)
        self.update_LineEdit.setPlaceholderText(self.tr("Enter update link (optional)"))
        self.update_LineEdit.setClearButtonEnabled(True)
        self.search_button = ToolButton(FIF.SEARCH, self)
        self.search_button.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.search_button.clicked.connect(self.search_bundle)
        self.update_layout = QHBoxLayout()
        self.update_layout.addWidget(self.update_LineEdit)
        self.update_layout.addWidget(self.search_button)

        self.path_layout.setStretch(0, 9)
        self.path_layout.setStretch(1, 1)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addLayout(self.path_layout)
        self.viewLayout.addLayout(self.name_layout)
        self.viewLayout.addLayout(self.update_layout)

        self.yesButton.setText(self.tr("Confirm"))
        self.cancelButton.setText(self.tr("Cancel"))

        self.widget.setMinimumWidth(350)
        self.yesButton.clicked.connect(self.click_yes_button)

    def search_bundle(self) -> None:
        if self.update_LineEdit.text() == "":
            self.show_error(self.tr("Please enter the update link"))
            return
        self.search_button.setIcon(FIF.MORE)
        updata_link = self.update_LineEdit.text()
        logger.info(f"更新链接 {updata_link}")

        self.download_bundle.project_url = updata_link

        self.download_bundle.start()
        self.w = ShowDownload(self)
        self.w.show()

    def download_finished(self, message: Dict[str, str]) -> None:
        print(message)
        if not message["status"] == "failed":
            self.folder = message["target_path"]
            if os.path.basename(self.folder) == "resource":
                interface_path = os.path.join(
                    os.path.dirname(self.folder), "interface.json"
                )
                resource_path = self.folder
                self.status = 0  # 0 直接选择resource目录，1选择resource目录的上级目录
            else:
                interface_path = os.path.join(self.folder, "interface.json")
                resource_path = os.path.join(self.folder, "resource")
                self.status = 1  # 0 直接选择resource目录，1选择resource目录的上级目录

            if not os.path.exists(interface_path):
                self.show_error(self.tr("The resource does not have an interface.json"))
                return
            elif not os.path.exists(resource_path):
                self.show_error(self.tr("The resource is not a resource directory"))
                return

            self.path_LineEdit.setText(self.folder)
            logger.info(f"资源路径 {self.folder}")
            logger.info(f"interface.json路径 {interface_path}")
            self.interface_data: dict = Read_Config(interface_path)
            project_name = self.interface_data.get("name", "")
            self.name_LineEdit.clear()
            self.name_LineEdit.setText(project_name)
            try:
                self.w.close()
            except:
                pass
        self.search_button.setIcon(FIF.SEARCH)

    def type_resource_name(self) -> None:
        self.folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./"
        )
        if os.path.basename(self.folder) == "resource":
            interface_path = os.path.join(
                os.path.dirname(self.folder), "interface.json"
            )
            resource_path = self.folder
            self.status = 0  # 0 直接选择resource目录，1选择resource目录的上级目录
        else:
            interface_path = os.path.join(self.folder, "interface.json")
            resource_path = os.path.join(self.folder, "resource")
            self.status = 1  # 0 直接选择resource目录，1选择resource目录的上级目录

        if not os.path.exists(interface_path):
            self.show_error(self.tr("The resource does not have an interface.json"))
            return
        elif not os.path.exists(resource_path):
            self.show_error(self.tr("The resource is not a resource directory"))
            return

        self.path_LineEdit.setText(self.folder)
        logger.info(f"资源路径 {self.folder}")
        logger.info(f"interface.json路径 {interface_path}")
        self.interface_data = Read_Config(interface_path)
        project_name = self.interface_data.get("name", "")
        projece_url = self.interface_data.get("url", "")
        self.name_LineEdit.clear()
        self.name_LineEdit.setText(project_name)
        self.update_LineEdit.clear()
        self.update_LineEdit.setText(projece_url)

    def show_error(self, message) -> None:
        InfoBar.error(
            title=self.tr("Error"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self,
        )

    def click_yes_button(self) -> None:
        self.name_data = self.name_LineEdit.text()
        path_data = self.path_LineEdit.text()
        interface_path = ""
        if self.status == 0:
            # 直接选择resource目录
            interface_path = os.path.join(os.path.dirname(path_data), "interface.json")
            path_data = os.path.dirname(path_data)
        elif self.status == 1:
            # 选择resource目录的上级目录
            interface_path = os.path.join(path_data, "interface.json")
            path_data = path_data

        update_data = self.update_LineEdit.text()
        resource_data = cfg.get(cfg.maa_resource_list)
        resource_list = list(resource_data)
        resource_path_list = list(resource_data.values())
        maa_config_list = cfg.get(cfg.maa_config_list)
        if self.name_data == "":
            self.show_error(self.tr("Resource name cannot be empty"))
            return
        elif not path_data:
            self.show_error(self.tr("Resource path cannot be empty"))
            return
        elif self.name_data in resource_list or path_data in resource_path_list:
            self.show_error(self.tr("Resource already exists"))
            return

        # 将名字和更新链接写入interface.json文件
        self.interface_data["name"] = self.name_data
        if update_data != "":
            self.interface_data["url"] = update_data
        if interface_path == "":
            return
        Save_Config(interface_path, self.interface_data)

        # 将信息写入maa_resource_list
        resource_data[self.name_data] = path_data
        cfg.set(cfg.maa_resource_list, resource_data)
        maa_pi_config_Path = os.path.join(
            os.getcwd(),
            "config",
            self.name_data,
            "config",
            "default",
            "maa_pi_config.json",
        )
        # 将信息写入maa_config_list
        maa_config_list[self.name_data] = {"default": maa_pi_config_Path}
        cfg.set(cfg.maa_config_list, maa_config_list)
        # 设置显示当前资源
        cfg.set(cfg.maa_config_name, "default")
        cfg.set(cfg.maa_config_path, maa_pi_config_Path)
        data = {
            "adb": {
                "adb_path": "",
                "address": "",
                "input_method": 0,
                "screen_method": 0,
                "config": {},
            },
            "win32": {
                "hwnd": 0,
                "input_method": 0,
                "screen_method": 0,
            },
            "controller": {"name": ""},
            "gpu": -1,
            "resource": "",
            "task": [],
            "finish_option": 0,
            "finish_option_res": 0,
            "finish_option_cfg": 0,
            "run_before_start": "",
            "run_before_start_args": "",
            "run_after_finish": "",
            "run_after_finish_args": "",
            "emu_path": "",
            "emu_args": "",
            "emu_wait_time": 10,
            "exe_path": "",
            "exe_args": "",
            "exe_wait_time": 10,
        }
        Save_Config(maa_pi_config_Path, data)
        cfg.set(cfg.maa_resource_name, self.name_data)
        cfg.set(cfg.maa_resource_path, path_data)
        cfg.set(cfg.resource_exist, True)


class ComboBoxSettingCardCustom(SettingCard):
    """自定义ComboBox设置卡片"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        texts: List[str],
        path,
        target: list = [],
        controller=None,
        controller_type=None,
        content=None,
        parent=None,
        mode: str = "",
        mapping: dict = {},
    ):
        """
        初始化自定义ComboBox设置卡片。

        :param icon: 图标
        :param title: 标题
        :param path: 目标路径
        :param target: 目标键
        :param controller: 控制器
        :param controller_type: 控制器类型
        :param content: 内容
        :param texts: 选项文本
        :param parent: 父级
        :param mode: 模式（如setting, custom, interface_setting）
        :param mapping: 映射表
        """
        super().__init__(icon, title, content, parent)
        self.path = path
        self.target = target
        self.mode = mode
        self.mapping = mapping
        if controller:
            self.controller:str = controller
        else:
            self.controller :str= ""
        if controller_type:
            self.controller_type :str= controller_type
        else:
            self.controller_type :str= ""

        # 创建ComboBox并添加到布局
        self.comboBox = ComboBox(self)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        # 添加文本项到ComboBox
        self.comboBox.addItems(texts)

        # 读取配置并设置当前选项
        self.set_current_text()

        # 连接选项改变信号
        self.comboBox.currentIndexChanged.connect(self._onCurrentIndexChanged)
        logger.debug(f"初始化自定义ComboBox设置卡片: {title}")

    def set_current_text(self):
        """根据模式设置ComboBox的当前文本。"""
        if self.path == "":
            self.comboBox.setCurrentText("")  # 设置为空文本或默认值
            return

        # 读取配置
        data = Read_Config(self.path)
        if self.mode == "setting":
            value = access_nested_dict(data, self.target)
            if value in self.mapping:
                current_text = self.mapping[value]
            else:
                current_text = self.mapping.get(0)
        elif self.mode == "custom":
            current_text = access_nested_dict(data, self.target)
        elif self.mode == "interface_setting":
            value = rewrite_contorller(data, self.controller, self.controller_type)
            current_text = self.mapping.get(
                value, self.tr("default") if value is None else value
            )
        else:
            current_text = ""

        self.comboBox.setCurrentText(current_text)

    def _onCurrentIndexChanged(self):
        """处理ComboBox当前索引变化的事件。"""
        text = self.comboBox.text()
        data = Read_Config(self.path)

        if self.mode == "setting":
            result = find_key_by_value(self.mapping, text)
            if result is None:
                return
            access_nested_dict(data, self.target, value=result)
        elif self.mode == "custom":
            access_nested_dict(data, self.target, value=text)
        elif self.mode == "interface_setting":
            result = find_key_by_value(self.mapping, text)
            if result is None:
                return
            if result == 0:
                delete_contorller(data, self.controller, self.controller_type)
            else:
                rewrite_contorller(data, self.controller, self.controller_type, result)

        Save_Config(self.path, data)
