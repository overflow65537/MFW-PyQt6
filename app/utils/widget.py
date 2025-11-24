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

"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 组件
作者:overflow65537
"""

from PySide6.QtWidgets import (
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
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
    QPainter,
    QPixmap,
)
from PySide6.QtCore import Qt, Signal, QMimeData

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
    CheckBox,
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
    encrypt,
    decrypt,
    get_override,
)
from ..utils.notice import send_thread
from ..common.config import cfg
from ..common.resource_config import res_cfg
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

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        super().mousePressEvent(e)


class RightCheckPrimaryPushButton(PrimaryPushButton):
    rightClicked = Signal()

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        super().mousePressEvent(e)


class NoticeType(MessageBoxBase):
    def __init__(self, parent=None, notice_type: str = ""):
        super().__init__(parent)
        self.notice_type = notice_type
        self.testButton = PushButton(self.tr("Test"), self)
        self.testButton.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        self.buttonLayout.insertWidget(1, self.testButton)
        self.buttonLayout.setStretch(0, 1)
        self.buttonLayout.setStretch(1, 1)
        self.buttonLayout.setStretch(2, 1)
        self.widget.setMinimumWidth(350)
        self.widget.setMinimumHeight(100)

        self.init_noticetype(notice_type)

        self.yesButton.clicked.connect(self.on_yes)
        self.testButton.clicked.connect(self.on_test)
        self.cancelButton.clicked.connect(self.on_cancel)

    def on_test(self):
        test_msg = {"title": "Test Title", "text": "Test Text"}
        try:
            send_thread.add_task(self.notice_type.lower(), test_msg, True)
            self.testButton.setEnabled(False)
        except Exception as e:
            logger.error(f"不支持的通知类型: {self.notice_type}")
            raise Exception(f"不支持的通知类型: {self.notice_type}")

    def notice_send_finished(self):
        self.testButton.setEnabled(True)

    def init_noticetype(self, notice_type):
        """根据通知类型初始化界面元素"""
        match notice_type:
            case "DingTalk":
                self.add_dingtalk_fields()
            case "Lark":
                self.add_lark_fields()
            case "Qmsg":
                self.add_qmsg_fields()
            case "SMTP":
                self.add_smtp_fields()
            case "WxPusher":
                self.add_wxpusher_fields()
            case "QYWX":
                self.add_qywx_fields()

    def save_noticetype(self, notice_type):
        """保存通知类型"""
        match notice_type:
            case "DingTalk":
                self.save_dingtalk_fields()
            case "Lark":
                self.save_lark_fields()
            case "Qmsg":
                self.save_qmsg_fields()
            case "SMTP":
                self.save_smtp_fields()
            case "WxPusher":
                self.save_wxpusher_fields()
            case "QYWX":
                self.save_qywx_fields()

    def encrypt_key(self, obj):
        """加密密钥"""
        with open("k.ey", "rb") as file:
            key = file.read()
            encrypt_key = encrypt(obj(), key)
        return encrypt_key

    def decode_key(self, key_name) -> str:
        """解密密钥"""
        mapping = {
            "dingtalk": cfg.Notice_DingTalk_secret,
            "lark": cfg.Notice_Lark_secret,
            "smtp": cfg.Notice_SMTP_password,
            "wxpusher": cfg.Notice_WxPusher_SPT_token,
            "QYWX": cfg.Notice_QYWX_key,
        }
        try:
            with open("k.ey", "rb") as key_file:
                key = key_file.read()
                return decrypt(cfg.get(mapping[key_name]), key)
        except Exception as e:
            logger.exception("获取ckd失败")
            return ""

    def save_dingtalk_fields(self):
        """保存钉钉相关的输入框"""
        cfg.set(cfg.Notice_DingTalk_url, self.dingtalk_url_input.text())
        cfg.set(
            cfg.Notice_DingTalk_secret,
            self.encrypt_key(self.dingtalk_secret_input.text),
        )
        cfg.set(cfg.Notice_DingTalk_status, self.dingtalk_status_switch.isChecked())

    def save_lark_fields(self):
        """保存飞书相关的输入框"""
        cfg.set(cfg.Notice_Lark_url, self.lark_url_input.text())
        cfg.set(cfg.Notice_Lark_secret, self.encrypt_key(self.lark_secret_input.text))
        cfg.set(cfg.Notice_Lark_status, self.lark_status_switch.isChecked())

    def save_qmsg_fields(self):
        """保存 Qmsg 相关的输入框"""
        cfg.set(cfg.Notice_Qmsg_sever, self.sever_input.text())
        cfg.set(cfg.Notice_Qmsg_key, self.encrypt_key(self.key_input.text))
        cfg.set(cfg.Notice_Qmsg_user_qq, self.user_qq_input.text())
        cfg.set(cfg.Notice_Qmsg_robot_qq, self.robot_qq_input.text())
        cfg.set(cfg.Notice_Qmsg_status, self.qmsg_status_switch.isChecked())

    def save_smtp_fields(self):
        """保存 SMTP 相关的输入框"""
        cfg.set(cfg.Notice_SMTP_sever_address, self.server_address_input.text())
        cfg.set(cfg.Notice_SMTP_sever_port, self.server_port_input.text())
        cfg.set(cfg.Notice_SMTP_used_ssl, self.used_ssl.isChecked())
        cfg.set(cfg.Notice_SMTP_user_name, self.user_name_input.text())
        cfg.set(cfg.Notice_SMTP_password, self.encrypt_key(self.password_input.text))
        cfg.set(cfg.Notice_SMTP_receive_mail, self.receive_mail_input.text())
        cfg.set(cfg.Notice_SMTP_status, self.smtp_status_switch.isChecked())

    def save_wxpusher_fields(self):
        """保存 WxPusher 相关的输入框"""
        cfg.set(
            cfg.Notice_WxPusher_SPT_token,
            self.encrypt_key(self.wxpusher_spt_input.text),
        )
        cfg.set(cfg.Notice_WxPusher_status, self.wxpusher_status_switch.isChecked())

    def save_qywx_fields(self):
        """保存 QYWX 相关的输入框"""
        cfg.set(cfg.Notice_QYWX_key, self.encrypt_key(self.qywx_key_input.text))
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
        self.dingtalk_secret_input.setText(self.decode_key("dingtalk"))
        self.dingtalk_status_switch.setChecked(cfg.get(cfg.Notice_DingTalk_status))

        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        col1.addWidget(dingtalk_url_title)
        col1.addWidget(dingtalk_secret_title)
        col1.addWidget(dingtalk_status_title)

        col2.addWidget(self.dingtalk_url_input)
        col2.addWidget(self.dingtalk_secret_input)
        col2.addWidget(self.dingtalk_status_switch)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(col1)
        mainLayout.addLayout(col2)
        self.viewLayout.addLayout(mainLayout)
        self.dingtalk_url_input.textChanged.connect(self.save_dingtalk_fields)
        self.dingtalk_secret_input.textChanged.connect(self.save_dingtalk_fields)

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
        self.lark_secret_input.setText(self.decode_key("lark"))
        self.lark_status_switch.setChecked(cfg.get(cfg.Notice_Lark_status))

        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        col1.addWidget(lark_url_title)
        col1.addWidget(lark_secret_title)
        col1.addWidget(lark_status_title)

        col2.addWidget(self.lark_url_input)
        col2.addWidget(self.lark_secret_input)
        col2.addWidget(self.lark_status_switch)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(col1)
        mainLayout.addLayout(col2)
        self.viewLayout.addLayout(mainLayout)

        self.lark_url_input.textChanged.connect(self.save_lark_fields)
        self.lark_secret_input.textChanged.connect(self.save_lark_fields)

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
        self.key_input.setText(self.decode_key("qmsg"))
        self.user_qq_input.setText(cfg.get(cfg.Notice_Qmsg_user_qq))
        self.robot_qq_input.setText(cfg.get(cfg.Notice_Qmsg_robot_qq))
        self.qmsg_status_switch.setChecked(cfg.get(cfg.Notice_Qmsg_status))

        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        col1.addWidget(sever_title)
        col1.addWidget(key_title)
        col1.addWidget(user_qq_title)
        col1.addWidget(robot_qq_title)
        col1.addWidget(qmsg_status_title)

        col2.addWidget(self.sever_input)
        col2.addWidget(self.key_input)
        col2.addWidget(self.user_qq_input)
        col2.addWidget(self.robot_qq_input)
        col2.addWidget(self.qmsg_status_switch)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(col1)
        mainLayout.addLayout(col2)
        self.viewLayout.addLayout(mainLayout)

        self.sever_input.textChanged.connect(self.save_qmsg_fields)
        self.key_input.textChanged.connect(self.save_qmsg_fields)
        self.user_qq_input.textChanged.connect(self.save_qmsg_fields)
        self.robot_qq_input.textChanged.connect(self.save_qmsg_fields)

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
        self.used_ssl = CheckBox(self.tr("Use SSL"), self)
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
        self.used_ssl.setChecked(cfg.get(cfg.Notice_SMTP_used_ssl))
        self.user_name_input.setText(cfg.get(cfg.Notice_SMTP_user_name))
        self.password_input.setText(self.decode_key("smtp"))
        self.receive_mail_input.setText(cfg.get(cfg.Notice_SMTP_receive_mail))
        self.smtp_status_switch.setChecked(cfg.get(cfg.Notice_SMTP_status))

        self.port_field = QHBoxLayout()
        self.port_field.addWidget(self.server_port_input)
        self.port_field.addWidget(self.used_ssl)

        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        col1.addWidget(server_address_title)
        col1.addWidget(server_port_title)
        col1.addWidget(user_name_title)
        col1.addWidget(password_title)
        col1.addWidget(receive_mail_title)
        col1.addWidget(smtp_status_title)

        col2.addWidget(self.server_address_input)
        col2.addLayout(self.port_field)
        col2.addWidget(self.user_name_input)
        col2.addWidget(self.password_input)
        col2.addWidget(self.receive_mail_input)
        col2.addWidget(self.smtp_status_switch)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(col1)
        mainLayout.addLayout(col2)

        self.viewLayout.addLayout(mainLayout)

        self.server_address_input.textChanged.connect(self.save_smtp_fields)
        self.server_port_input.textChanged.connect(self.save_smtp_fields)
        self.used_ssl.stateChanged.connect(self.save_smtp_fields)
        self.user_name_input.textChanged.connect(self.save_smtp_fields)
        self.password_input.textChanged.connect(self.save_smtp_fields)
        self.receive_mail_input.textChanged.connect(self.save_smtp_fields)

    def add_wxpusher_fields(self):
        """添加 WxPusher 相关的输入框"""
        wxpusher_spt_title = BodyLabel(self)
        wxpusher_status_title = BodyLabel(self)

        self.wxpusher_spt_input = PasswordLineEdit(self)
        self.wxpusher_status_switch = SwitchButton(self)

        wxpusher_spt_title.setText(self.tr("WxPusher Spt:"))
        wxpusher_status_title.setText(self.tr("WxPusher Status:"))

        self.wxpusher_spt_input.setText(self.decode_key("wxpusher"))
        self.wxpusher_status_switch.setChecked(cfg.get(cfg.Notice_WxPusher_status))

        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        col1.addWidget(wxpusher_spt_title)
        col1.addWidget(wxpusher_status_title)

        col2.addWidget(self.wxpusher_spt_input)
        col2.addWidget(self.wxpusher_status_switch)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(col1)
        mainLayout.addLayout(col2)

        self.viewLayout.addLayout(mainLayout)
        self.wxpusher_spt_input.textChanged.connect(self.save_wxpusher_fields)

    def add_qywx_fields(self):
        """添加 企业微信机器人 相关的输入框"""
        qywx_key_title = BodyLabel(self)
        qywx_status_title = BodyLabel(self)

        self.qywx_key_input = PasswordLineEdit(self)
        self.qywx_status_switch = SwitchButton(self)

        qywx_key_title.setText(self.tr("QYWXbot Key:"))
        qywx_status_title.setText(self.tr("QYWXbot Status:"))

        self.qywx_key_input.setText(self.decode_key("QYWX"))
        self.qywx_status_switch.setChecked(cfg.get(cfg.Notice_QYWX_status))

        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        col1.addWidget(qywx_key_title)
        col1.addWidget(qywx_status_title)

        col2.addWidget(self.qywx_key_input)
        col2.addWidget(self.qywx_status_switch)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(col1)
        mainLayout.addLayout(col2)

        self.viewLayout.addLayout(mainLayout)
        self.qywx_key_input.textChanged.connect(self.save_qywx_fields)

    def on_yes(self):
        self.save_noticetype(self.notice_type)
        logger.info(f"保存{self.notice_type}设置")
        self.accept()

    def on_cancel(self):
        logger.info("关闭通知设置对话框")
        self.close()


class ListWidge_Menu_Draggable(ListWidget):
    def __init__(self, parent=None):
        super(ListWidge_Menu_Draggable, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

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

        # 获取所有选中项的行号
        selected_items = self.selectedItems()
        selected_rows = [self.row(item) for item in selected_items]

        action_run_alone = Action(FIF.PLAY_SOLID, self.tr("Run Alone"))
        action_move_up = Action(FIF.UP, self.tr("Move Up"))
        action_move_down = Action(FIF.DOWN, self.tr("Move Down"))
        action_delete = Action(FIF.DELETE, self.tr("Delete"))
        action_delete_all = Action(FIF.DELETE, self.tr("Delete All"))

        if not selected_rows:
            action_run_alone.setEnabled(False)
            action_move_up.setEnabled(False)
            action_move_down.setEnabled(False)
            action_delete.setEnabled(False)

        action_run_alone.triggered.connect(self.Run_Alone)
        action_move_up.triggered.connect(self.Move_Up)
        action_move_down.triggered.connect(self.Move_Down)
        action_delete.triggered.connect(self.Delete_Task)
        action_delete_all.triggered.connect(self.Delete_All_Task)

        menu.addAction(action_run_alone)
        menu.addAction(action_move_up)
        menu.addAction(action_move_down)
        menu.addAction(action_delete)
        menu.addAction(action_delete_all)

        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)

    def Run_Alone(self):
        Select_Target = self.currentRow()
        if Select_Target == -1:
            return
        task_obj = res_cfg.config.get("task")[Select_Target]
        task_dict = get_override(task_obj, res_cfg.interface_config)
        signalBus.run_sp_task.emit(task_dict)

    def Delete_All_Task(self):
        self.clear()
        res_cfg.config["task"] = []
        Save_Config(res_cfg.config_path, res_cfg.config)
        signalBus.update_task_list.emit()
        signalBus.dragging_finished.emit()

    def Delete_Task(self):
        # 获取所有选中项的行号
        selected_items = self.selectedItems()
        selected_rows = sorted(
            [self.row(item) for item in selected_items], reverse=True
        )
        task_list = res_cfg.config.get("task", [])

        for row in selected_rows:
            if 0 <= row < len(task_list):
                self.takeItem(row)
                del task_list[row]

        self.update_task_config(task_list)
        self.clearSelection()

        signalBus.update_task_list.emit()
        signalBus.dragging_finished.emit()

    def Move_Up(self):
        # 获取所有选中项的行号
        selected_items = self.selectedItems()
        selected_rows = sorted([self.row(item) for item in selected_items])
        self.move_tasks(selected_rows, -1)

    def Move_Down(self):
        # 获取所有选中项的行号
        selected_items = self.selectedItems()
        selected_rows = sorted(
            [self.row(item) for item in selected_items], reverse=True
        )
        self.move_tasks(selected_rows, 1)

    def move_tasks(self, selected_rows, offset):
        task_list = res_cfg.config.get("task", [])
        moved_indices = []

        for row in selected_rows:
            new_index = row + offset
            if 0 <= new_index < len(task_list) and new_index not in moved_indices:
                task = task_list.pop(row)
                task_list.insert(new_index, task)
                moved_indices.append(new_index)

        self.update_task_config(task_list)
        self.clear()
        self.addItems(Get_Values_list_Option(res_cfg.config_path, "task"))

        # 重新设置选中状态
        for index in moved_indices:
            self.item(index).setSelected(True)

        signalBus.update_task_list.emit()
        signalBus.dragging_finished.emit()

    def update_task_config(self, Task_List):
        res_cfg.config["task"] = Task_List
        Save_Config(res_cfg.config_path, res_cfg.config)

    def update_selection(self, Select_Target):
        if Select_Target == 0 and self.count() > 0:
            self.setCurrentRow(Select_Target)
        elif Select_Target != -1 and self.count() > 1:
            self.setCurrentRow(Select_Target - 1)

    def startDrag(self, supportedActions):
        selected_items = self.selectedItems()
        if not selected_items:
            return

        # 创建一个组合的 pixmap 用于拖动显示
        combined_pixmap = self.create_combined_pixmap(selected_items)

        drag = QDrag(self)
        mimeData = QMimeData()
        # 存储所有选中项的文本，用换行符分隔
        texts = [item.text() for item in selected_items]
        mimeData.setText("\n".join(texts))
        # 存储所有选中项的行号，用逗号分隔
        rows = [str(self.row(item)) for item in selected_items]
        mimeData.setData("application/x-listwidgetrow", ",".join(rows).encode())

        drag.setMimeData(mimeData)
        drag.setPixmap(combined_pixmap)
        drag.setHotSpot(
            self.mapFromGlobal(QCursor.pos())
            - self.visualItemRect(selected_items[0]).topLeft()
        )

        drag.exec(supportedActions)

    def create_combined_pixmap(self, items):
        """创建组合的 pixmap 用于显示多个选中项"""
        rect = self.visualItemRect(items[0])
        width = rect.width()
        height = rect.height() * len(items)

        combined_pixmap = QPixmap(width, height)
        combined_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(combined_pixmap)
        for i, item in enumerate(items):
            pixmap = self.viewport().grab(self.visualItemRect(item))
            painter.drawPixmap(0, i * rect.height(), pixmap)
        painter.end()

        return combined_pixmap

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasText() and event.mimeData().hasFormat("application/x-listwidgetrow"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasText() and event.mimeData().hasFormat("application/x-listwidgetrow"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.source() == self:
            if event.proposedAction() == Qt.DropAction.MoveAction:
                selected_items = self.selectedItems()
                if not selected_items:
                    super(ListWidge_Menu_Draggable, self).dropEvent(event)
                    return

                source_rows = sorted(
                    [self.row(item) for item in selected_items], reverse=True
                )
                position = event.position().toPoint()
                target_item = self.itemAt(position)
                target_row = self.row(target_item) if target_item else self.count()

                task_list = res_cfg.config.get("task", [])
                # 先移除选中的任务
                moved_tasks = []
                for row in source_rows:
                    if 0 <= row < len(task_list):
                        moved_tasks.insert(0, task_list.pop(row))

                # 计算插入位置
                insert_index = target_row
                if insert_index > source_rows[0]:
                    insert_index -= len(source_rows)

                # 插入移动的任务
                for task in moved_tasks:
                    task_list.insert(insert_index, task)
                    insert_index += 1

                res_cfg.config["task"] = task_list
                Save_Config(res_cfg.config_path, res_cfg.config)

                # 刷新列表
                self.clear()
                self.addItems(Get_Values_list_Option(res_cfg.config_path, "task"))

                # 重新设置选中状态
                if selected_items:  # 添加空值检查
                    try:
                        for task_text in [item.text() for item in selected_items]:
                            for i in range(self.count()):
                                if self.item(i).text() == task_text:
                                    self.item(i).setSelected(True)
                                    break
                    except Exception as e:
                        logger.error(f"重新设置选中状态时出错: {e}")
                else:
                    logger.warning("selected_items 为空，跳过重新设置选中状态")

                signalBus.update_task_list.emit()
            super(ListWidge_Menu_Draggable, self).dropEvent(event)
            signalBus.dragging_finished.emit()
        else:
            event.ignore()


class SendSettingCard(MessageBoxBase):
    """选择发送通知的时机"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.widget.setMinimumWidth(350)
        self.widget.setMinimumHeight(100)
        self.init_widget()

    def init_widget(self):
        self.when_start_up = CheckBox(self.tr("When Start Up"), self)
        self.when_connect_failed = CheckBox(self.tr("When Connect Failed"), self)
        self.when_connect_success = CheckBox(self.tr("When Connect Succeed"), self)
        self.when_post_task = CheckBox(self.tr("When Post Task"), self)
        self.when_task_failed = CheckBox(self.tr("When Task Failed"), self)
        self.when_task_finished = CheckBox(self.tr("When Task Finished"), self)

        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        col1.addWidget(self.when_start_up)
        col1.addWidget(self.when_connect_failed)
        col1.addWidget(self.when_connect_success)
        col2.addWidget(self.when_post_task)
        col2.addWidget(self.when_task_failed)
        col2.addWidget(self.when_task_finished)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(col1)
        mainLayout.addLayout(col2)
        self.viewLayout.addLayout(mainLayout)

        self.when_start_up.setChecked(cfg.get(cfg.when_start_up))
        self.when_connect_failed.setChecked(cfg.get(cfg.when_connect_failed))
        self.when_connect_success.setChecked(cfg.get(cfg.when_connect_success))
        self.when_post_task.setChecked(cfg.get(cfg.when_post_task))
        self.when_task_failed.setChecked(cfg.get(cfg.when_task_failed))
        self.when_task_finished.setChecked(cfg.get(cfg.when_task_finished))

    def save_setting(self):
        cfg.set(cfg.when_start_up, self.when_start_up.isChecked())
        cfg.set(cfg.when_connect_failed, self.when_connect_failed.isChecked())
        cfg.set(cfg.when_connect_success, self.when_connect_success.isChecked())
        cfg.set(cfg.when_post_task, self.when_post_task.isChecked())
        cfg.set(cfg.when_task_failed, self.when_task_failed.isChecked())
        cfg.set(cfg.when_task_finished, self.when_task_finished.isChecked())


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
        comboBox=True,
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

        if comboBox:
            self.combobox = ComboBox(self)
            self.hBoxLayout.addWidget(self.combobox, 0, Qt.AlignmentFlag.AlignRight)
            self.hBoxLayout.addSpacing(16)
            self.combobox.addItems(
                [
                    self.tr("stable"),
                    self.tr("beta"),
                ]
            )
            self.combobox.currentIndexChanged.connect(self.setValue)

        self.hBoxLayout.addWidget(self.button2, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.button.clicked.connect(self.clicked)
        self.button2.clicked.connect(self.clicked2)

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
                # 优先尝试读取 interface.jsonc
                interface_path = os.path.join(os.path.dirname(self.folder), "interface.jsonc")
                if not os.path.exists(interface_path):
                    # 如果 interface.jsonc 不存在，再尝试 interface.json
                    interface_path = os.path.join(os.path.dirname(self.folder), "interface.json")
                resource_path = self.folder
                self.status = 0  # 0 直接选择resource目录，1选择resource目录的上级目录
            else:
                # 优先尝试读取 interface.jsonc
                interface_path = os.path.join(self.folder, "interface.jsonc")
                if not os.path.exists(interface_path):
                    # 如果 interface.jsonc 不存在，再尝试 interface.json
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
            # 优先尝试读取 interface.jsonc
            interface_path = os.path.join(os.path.dirname(self.folder), "interface.jsonc")
            if not os.path.exists(interface_path):
                # 如果 interface.jsonc 不存在，再尝试 interface.json
                interface_path = os.path.join(os.path.dirname(self.folder), "interface.json")
            resource_path = self.folder
            self.status = 0  # 0 直接选择resource目录，1选择resource目录的上级目录
        else:
            # 优先尝试读取 interface.jsonc
            interface_path = os.path.join(self.folder, "interface.jsonc")
            if not os.path.exists(interface_path):
                # 如果 interface.jsonc 不存在，再尝试 interface.json
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
            self.controller: str = controller
        else:
            self.controller: str = ""
        if controller_type:
            self.controller_type: str = controller_type
        else:
            self.controller_type: str = ""

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


class ProxySettingCard(SettingCard):
    def __init__(
        self, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None
    ):
        # 有一个下拉框和一个输入框
        super().__init__(icon, title, content, parent)
        self.input = LineEdit(self)
        self.input.setPlaceholderText("<IP>:<PORT>")
        self.combobox = ComboBox(self)
        self.combobox.addItems(["HTTP", "SOCKS5"])

        self.hBoxLayout.addWidget(self.combobox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.input, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
