from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QWidget
from qfluentwidgets import (
    FluentIcon as FIF,
    SettingCardGroup,
    SwitchSettingCard,
)

from app.common.config import cfg
from app.utils.crypto import crypto_manager
from app.utils.logger import logger

from app.view.update_interface.widget.LineEditCard import LineEditCard
from app.view.update_interface.widget.ProxySettingCard import ProxySettingCard


class UpdateSettingsSection:
    """
    Encapsulates the shared update settings widgets so they can be reused both in the
    main settings interface and a dedicated update page.
    """

    def __init__(
        self,
        parent: QWidget,
        interface_data: Optional[dict] = None,
    ):
        self.parent = parent
        self.interface_data = interface_data or {}
        self.group = SettingCardGroup(self.parent.tr("Update"), self.parent)

        holder_text = self._get_mirror_holder_text()
        self.MirrorCard = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.parent.tr("mirrorchyan CDK"),
            content=self.parent.tr("Enter mirrorchyan CDK for stable update path"),
            is_passwork=True,
            num_only=False,
            holderText=holder_text,
            button=True,
            button_type="primary",
            button_text=self.parent.tr("About Mirror"),
            parent=self.group,
        )

        self.auto_update = SwitchSettingCard(
            FIF.UPDATE,
            self.parent.tr("Auto Update resource"),
            self.parent.tr("Automatically update resources on every startup"),
            configItem=cfg.auto_update_resource,
            parent=self.group,
        )
        self.MFW_auto_update = SwitchSettingCard(
            FIF.UPDATE,
            self.parent.tr("Auto Update MFW"),
            self.parent.tr(
                "Automatically update MFW after opening the program. Not recommended, as it may cause the loss of the current running progress."
            ),
            configItem=cfg.auto_update_MFW,
            parent=self.group,
        )
        self.force_github = SwitchSettingCard(
            FIF.UPDATE,
            self.parent.tr("Force use GitHub"),
            self.parent.tr("Force use GitHub for resource update"),
            configItem=cfg.force_github,
            parent=self.group,
        )
        self.proxy = ProxySettingCard(
            FIF.GLOBE,
            self.parent.tr("Use Proxy"),
            self.parent.tr(
                "After filling in the proxy settings, all traffic except that to the Mirror will be proxied."
            ),
            parent=self.group,
        )

        self._initialize_proxy_controls()
        self._configure_mirror_card()
        self._register_layout()
        self.MirrorCard.lineEdit.textChanged.connect(self._onMirrorCardChange)

    def _initialize_proxy_controls(self):
        combox_index = cfg.get(cfg.proxy)
        self.proxy.combobox.setCurrentIndex(combox_index)

        if combox_index == 0:
            self.proxy.input.setText(cfg.get(cfg.http_proxy))
        elif combox_index == 1:
            self.proxy.input.setText(cfg.get(cfg.socks5_proxy))

        self.proxy.combobox.currentIndexChanged.connect(self.proxy_com_change)
        self.proxy.input.textChanged.connect(self.proxy_inp_change)

    def _register_layout(self):
        self.group.addSettingCard(self.MirrorCard)
        self.group.addSettingCard(self.auto_update)
        self.group.addSettingCard(self.MFW_auto_update)
        self.group.addSettingCard(self.force_github)
        self.group.addSettingCard(self.proxy)

    def set_interface_data(self, interface_data: dict):
        self.interface_data = interface_data or {}
        self._configure_mirror_card()

    def _configure_mirror_card(self):
        mirror_supported = bool(self.interface_data.get("mirrorchyan_rid"))
        if mirror_supported:
            self.MirrorCard.setContent(
                self.parent.tr("Enter mirrorchyan CDK for stable update path")
            )
            self.MirrorCard.lineEdit.setEnabled(True)
        else:
            self.MirrorCard.setContent(
                self.parent.tr(
                    "Resource does not support Mirrorchyan, right-click about mirror to unlock input"
                )
            )
            self.MirrorCard.lineEdit.setEnabled(False)

    def proxy_com_change(self):
        cfg.set(cfg.proxy, self.proxy.combobox.currentIndex())
        if self.proxy.combobox.currentIndex() == 0:
            self.proxy.input.setText(cfg.get(cfg.http_proxy))
        elif self.proxy.combobox.currentIndex() == 1:
            self.proxy.input.setText(cfg.get(cfg.socks5_proxy))

    def proxy_inp_change(self):
        if self.proxy.combobox.currentIndex() == 0:
            cfg.set(cfg.http_proxy, self.proxy.input.text())
        elif self.proxy.combobox.currentIndex() == 1:
            cfg.set(cfg.socks5_proxy, self.proxy.input.text())

    def _get_mirror_holder_text(self) -> str:
        encrypted = cfg.get(cfg.Mcdk)
        if not encrypted:
            return ""
        try:
            decrypted = crypto_manager.decrypt_payload(encrypted)
            if isinstance(decrypted, bytes):
                decrypted = decrypted.decode("utf-8", errors="ignore")
            return decrypted
        except Exception as exc:
            logger.warning("解密 Mirror CDK 失败: %s", exc)
            return ""

    def _onMirrorCardChange(self):
        try:
            encrypted = crypto_manager.encrypt_payload(self.MirrorCard.lineEdit.text())
            encrypted_value = (
                encrypted.decode("utf-8", errors="ignore")
                if isinstance(encrypted, bytes)
                else str(encrypted)
            )
            cfg.set(cfg.Mcdk, encrypted_value)
        except Exception as exc:
            logger.error("加密 Mirror CDK 失败: %s", exc)
            return
        cfg.set(cfg.is_change_cdk, True)

    def bind_to_mirror_actions(self, button_callback=None):
        if button_callback:
            self.MirrorCard.button.clicked.connect(button_callback)
