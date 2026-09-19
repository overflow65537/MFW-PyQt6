#   This file is part of MFW-ChainFlow Assistant.

#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/agpl-3.0.html>.

#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 外部通知单元
作者:weinibuliu，overflow65537,FDrag0n
"""

import re
import time
import hmac
import hashlib
import base64
import urllib.parse
import threading
from enum import IntEnum

import requests
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from queue import Queue
from PySide6.QtCore import QCoreApplication, QThread

from app.common.signal_bus import signalBus
from app.common.config import cfg
from app.utils.logger import logger
from app.utils.crypto import crypto_manager
from app.utils.notice_content import (
    build_custom_message,
    build_log_summary,
    build_simple_message,
)
from app.utils.notice_image import (
    DEFAULT_MAX_IMAGE_BYTES,
    encode_image_payload,
)
from app.utils.network_error_helper import (
    format_notice_result_message,
    normalize_network_error,
    set_notice_error_context,
)


def _notice_tr(text: str) -> str:
    return QCoreApplication.translate("NoticeSendThread", text)


def _normalize_message_dict(msg_dict: dict) -> dict:
    if "html" in msg_dict and "markdown" in msg_dict:
        return msg_dict
    return build_simple_message(
        str(msg_dict.get("title", "")),
        str(msg_dict.get("text", "")),
        image_bytes=msg_dict.get("image_bytes"),
    ).as_message_dict()


def _truncate_utf8(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    suffix = "\n\n…"
    budget = max(0, max_bytes - len(suffix.encode("utf-8")))
    truncated = encoded[:budget]
    while truncated:
        try:
            return truncated.decode("utf-8") + suffix
        except UnicodeDecodeError:
            truncated = truncated[:-1]
    return suffix.strip()


# 解码密钥
def decode_key(key_name) -> str:
    mapping = {
        "dingtalk": cfg.Notice_DingTalk_secret,
        "lark": cfg.Notice_Lark_secret,
        "smtp": cfg.Notice_SMTP_password,
        "wxpusher": cfg.Notice_WxPusher_SPT_token,
        "QYWX": cfg.Notice_QYWX_key,
        "gotify": cfg.Notice_Gotify_token,
        "webhook": cfg.Notice_Webhook_token,
    }

    config_item = mapping.get(key_name)
    if config_item is None:
        logger.error("无法识别的通知密钥类型: %s", key_name)
        return ""

    encrypted_value = cfg.get(config_item)
    if not encrypted_value:
        logger.warning("尚未配置 %s 的密钥", key_name)
        return ""

    try:
        decrypted_bytes = crypto_manager.decrypt_payload(encrypted_value)
        return (
            decrypted_bytes.decode("utf-8")
            if isinstance(decrypted_bytes, (bytes, bytearray))
            else str(decrypted_bytes)
        )
    except Exception:
        logger.exception("获取ckd失败")
        return ""


class NoticeErrorCode(IntEnum):
    """通知模块错误码枚举."""

    SUCCESS = 0  # 成功
    DISABLED = 1  # 通知未启用
    PARAM_EMPTY = 2  # 关键参数为空
    PARAM_INVALID = 3  # 参数格式错误
    NETWORK_ERROR = 4  # 网络请求异常
    RESPONSE_ERROR = 5  # 接口返回状态错误
    UNKNOWN_ERROR = 6  # 未知错误
    SMTP_PORT_INVALID = 7  # SMTP端口非整数
    SMTP_CONNECT_FAILED = 8  # SMTP连接失败


class NoticeTiming(IntEnum):
    """通知触发的时机."""

    WHEN_FLOW_STARTED = 1  # 任务流启动时
    WHEN_CONNECT_SUCCESS = 2  # 连接成功时
    WHEN_CONNECT_FAILED = 3  # 连接失败时
    WHEN_TASK_SUCCESS = 4  # 任务成功时
    WHEN_TASK_FAILED = 5  # 任务失败时
    WHEN_POST_TASK = 6  # 任务流完成时
    WHEN_TASK_TIMEOUT = 7  # 任务超时


class DingTalk:
    def __init__(self) -> None:
        self.correct_url = r"^https://oapi.dingtalk.com/robot/.*$"
        self.headers = {"Content-Type": "application/json"}
        self.codename = "errcode"
        self.code = 0

    def msg(self, msg_dict: dict) -> dict:
        return {
            "msgtype": "markdown",
            "markdown": {
                "title": msg_dict["title"],
                "text": _truncate_utf8(msg_dict["markdown"], 19000),
            },
        }

    def sign(self) -> list[str]:
        # 钉钉的签名校验方法为将 sign 与 timestamp 组合进 url 中
        url = cfg.get(cfg.Notice_DingTalk_url)
        secret = decode_key("dingtalk")

        if url == "":
            logger.error("DingTalk 通知地址为空")
            return [url]
        if secret == "":
            logger.error("DingTalk 密钥为空")
            return [url]

        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode("utf-8")
        string_to_sign = "{}\n{}".format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        final_url = f"{url}&timestamp={timestamp}&sign={sign}"

        return [final_url]


class Lark:
    def __init__(self) -> None:
        self.correct_url = r"^https://open.feishu.cn/open-apis/bot/.*$"
        self.headers = {"Content-Type": "application/json"}
        self.codename = "code"
        self.code = 0

    def msg(self, msg_dict: dict) -> dict:
        sign_cache = self.sign()
        return {
            "timestamp": sign_cache[1],
            "sign": sign_cache[2],
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": msg_dict["title"],
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": _truncate_utf8(
                                msg_dict["markdown"],
                                28000,
                            ),
                        },
                    }
                ],
            },
        }

    def sign(self) -> list[str]:
        # 飞书的签名校验方法为将 sign 与 timestamp 写进 message 中
        secret = decode_key("lark")
        timestamp = str(round(time.time()))
        # 拼接timestamp和secret
        string_to_sign = "{}\n{}".format(timestamp, secret)
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        # 对结果进行base64处理
        sign = base64.b64encode(hmac_code).decode("utf-8")

        return [cfg.get(cfg.Notice_Lark_url), timestamp, sign]


class SMTP:
    def msg(self, msg_dict: dict) -> MIMEText | MIMEMultipart:
        image_bytes = msg_dict.get("image_bytes")
        if image_bytes:
            image_payload = encode_image_payload(image_bytes)
            body = (
                msg_dict["html"]
                + '<div style="margin-top:16px"><img src="cid:screenshot" '
                'alt="screenshot" style="max-width:100%;height:auto"></div>'
            )
            text_part = MIMEText(body, "html", "utf-8")
            msg = MIMEMultipart("related")
            msg.attach(text_part)

            subtype = "jpeg" if image_payload.mime_type == "image/jpeg" else "png"
            inline_image = MIMEImage(image_payload.data, _subtype=subtype)
            inline_image.add_header("Content-ID", "<screenshot>")
            inline_image.add_header(
                "Content-Disposition",
                "inline",
                filename=image_payload.filename,
            )
            msg.attach(inline_image)

            attachment = MIMEImage(image_payload.data, _subtype=subtype)
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=image_payload.filename,
            )
            msg.attach(attachment)
        else:
            msg = MIMEText(msg_dict["html"], "html", "utf-8")

        msg["Subject"] = msg_dict["title"]
        msg["From"] = cfg.get(cfg.Notice_SMTP_user_name)
        msg["To"] = cfg.get(cfg.Notice_SMTP_receive_mail)

        return msg

    def send(self, msg_dict: dict) -> NoticeErrorCode:
        msg = self.msg(msg_dict)
        try:
            port = int(cfg.get(cfg.Notice_SMTP_sever_port))
        except ValueError:
            logger.error(
                f"SMTP 端口号 {cfg.get(cfg.Notice_SMTP_sever_port)} 不是有效的整数"
            )
            return NoticeErrorCode.SMTP_PORT_INVALID

        try:
            if cfg.get(cfg.Notice_SMTP_used_ssl):
                smtp = smtplib.SMTP_SSL(cfg.get(cfg.Notice_SMTP_sever_address), port)
            else:
                smtp = smtplib.SMTP(
                    cfg.get(cfg.Notice_SMTP_sever_address), port, timeout=1
                )
            smtp.login(cfg.get(cfg.Notice_SMTP_user_name), decode_key("smtp"))
        except Exception as e:
            info = normalize_network_error(e, source="smtp")
            set_notice_error_context("smtp", info)
            logger.error(info.log_message)
            return NoticeErrorCode.SMTP_CONNECT_FAILED

        try:
            smtp.sendmail(
                cfg.get(cfg.Notice_SMTP_user_name),
                cfg.get(cfg.Notice_SMTP_receive_mail),
                msg.as_string(),
            )
            return NoticeErrorCode.SUCCESS
        except Exception as e:
            info = normalize_network_error(e, source="smtp")
            set_notice_error_context("smtp", info)
            logger.error(info.log_message)
            return NoticeErrorCode.NETWORK_ERROR
        finally:
            smtp.quit()


class WxPusher:
    def msg(self, msg_dict: dict) -> dict:
        content = msg_dict["html"]
        image_bytes = msg_dict.get("image_bytes")
        if image_bytes:
            image_payload = encode_image_payload(
                image_bytes,
                max_bytes=40 * 1024,
            )
            image_html = (
                '<div style="margin-top:16px">'
                f'<img src="{image_payload.data_uri}" alt="screenshot" '
                'style="max-width:100%;height:auto"></div>'
            )
            if len((content + image_html).encode("utf-8")) <= 65000:
                content += image_html
            else:
                logger.warning("WxPusher 截图编码后超过内容限制，本次仅发送正文")
        return {
            "content": content,
            "summary": msg_dict["title"],
            "contentType": 2,
            "spt": decode_key("wxpusher"),
        }

    def send(self, msg_type: dict) -> bool:

        url = "https://wxpusher.zjiecode.com/api/send/message/simple-push"
        msg = self.msg(msg_type)
        try:
            response = requests.post(url=url, json=msg)
            status_code = response.json()["code"]
        except Exception as e:
            info = normalize_network_error(e, source="wxpusher")
            set_notice_error_context("wxpusher", info)
            logger.error(info.log_message)
            return False

        if status_code != 1000:
            logger.error(f"WxPusher 发送失败 {response.json()}")
            return False

        else:
            return True


class QYWX:
    def msg(self, msg_dict: dict) -> dict:
        return {
            "msgtype": "markdown",
            "markdown": {
                "content": _truncate_utf8(msg_dict["markdown"], 3900)
            },
        }

    @staticmethod
    def image_msg(image_bytes: bytes) -> dict | None:
        image_payload = encode_image_payload(image_bytes)
        if len(image_payload.data) > DEFAULT_MAX_IMAGE_BYTES:
            logger.warning("企业微信截图压缩后仍超过 2MB，已跳过图片消息")
            return None
        return {
            "msgtype": "image",
            "image": {
                "base64": image_payload.base64_data,
                "md5": image_payload.md5,
            },
        }

    def send(self, msg_dict: dict) -> NoticeErrorCode:
        qywx_key = decode_key("QYWX")
        if not qywx_key:
            return NoticeErrorCode.PARAM_EMPTY
        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={qywx_key}"

        try:
            response = requests.post(url=url, json=self.msg(msg_dict), timeout=15)
            response_data = response.json()
            if response_data.get("errcode") != 0:
                logger.error("企业微信机器人正文发送失败 %s", response_data)
                return NoticeErrorCode.RESPONSE_ERROR
        except Exception as e:
            info = normalize_network_error(e, source="qywx")
            set_notice_error_context("qywx", info)
            logger.error(info.log_message)
            return NoticeErrorCode.NETWORK_ERROR

        image_bytes = msg_dict.get("image_bytes")
        image_msg = self.image_msg(image_bytes) if image_bytes else None
        if image_msg is not None:
            try:
                image_response = requests.post(
                    url=url,
                    json=image_msg,
                    timeout=15,
                )
                image_data = image_response.json()
                if image_data.get("errcode") != 0:
                    logger.warning(
                        "企业微信机器人正文已发送，但图片发送失败 %s",
                        image_data,
                    )
            except Exception as e:
                info = normalize_network_error(e, source="qywx")
                logger.warning(
                    "企业微信机器人正文已发送，但图片发送异常: %s",
                    info.log_message,
                )

        return NoticeErrorCode.SUCCESS


class Gotify:
    def msg(self, msg_dict: dict) -> dict:
        return {
            "title": msg_dict["title"],
            "message": msg_dict["text"],
            "priority": int(cfg.get(cfg.Notice_Gotify_priority)),
        }

    def send(self, msg_dict: dict) -> NoticeErrorCode:
        gotify_token = decode_key("gotify")
        url = cfg.get(cfg.Notice_Gotify_url)
        if not url:
            logger.error("Gotify URL为空")
            return NoticeErrorCode.PARAM_EMPTY
        
        if not gotify_token:
            logger.error("Gotify Token为空")
            return NoticeErrorCode.PARAM_EMPTY

        if msg_dict.get("image_bytes"):
            logger.debug("Gotify 不支持直接上传截图，本次仅发送正文")
        
        msg = self.msg(msg_dict)
        headers = {
            "X-Gotify-Key": gotify_token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url=url, json=msg, headers=headers)
            if response.status_code == 200:
                return NoticeErrorCode.SUCCESS
            else:
                logger.error(f"Gotify 发送失败，状态码: {response.status_code}，响应: {response.text}")
                return NoticeErrorCode.RESPONSE_ERROR
        except Exception as e:
            info = normalize_network_error(e, source="gotify")
            set_notice_error_context("gotify", info)
            logger.error(info.log_message)
            return NoticeErrorCode.NETWORK_ERROR


class Webhook:
    """通用 Webhook：向任意 URL POST JSON，不绑定特定服务协议。"""

    def __init__(self) -> None:
        self.correct_url = r"^https?://.+"

    def msg(self, msg_dict: dict) -> dict:
        message = {
            "title": msg_dict["title"],
            "message": msg_dict["text"],
            "text": msg_dict["text"],
            "html": msg_dict["html"],
            "markdown": msg_dict["markdown"],
        }
        image_bytes = msg_dict.get("image_bytes")
        if image_bytes:
            image_payload = encode_image_payload(image_bytes)
            message.update(
                {
                    "image_base64": image_payload.base64_data,
                    "image_md5": image_payload.md5,
                    "image_content_type": image_payload.mime_type,
                }
            )
        return message

    @staticmethod
    def _multipart_payload(msg_dict: dict) -> tuple[dict, dict] | None:
        image_bytes = msg_dict.get("image_bytes")
        if not image_bytes:
            return None
        image_payload = encode_image_payload(image_bytes)
        data = {
            "title": msg_dict["title"],
            "content": msg_dict["text"],
            "message": msg_dict["text"],
            "text": msg_dict["text"],
            "html": msg_dict["html"],
            "markdown": msg_dict["markdown"],
        }
        files = {
            "image": (
                image_payload.filename,
                image_payload.data,
                image_payload.mime_type,
            )
        }
        return data, files

    def send(self, msg_dict: dict) -> NoticeErrorCode:
        url = (cfg.get(cfg.Notice_Webhook_url) or "").strip()
        if not url:
            logger.error("Webhook URL为空")
            return NoticeErrorCode.PARAM_EMPTY

        if not re.match(self.correct_url, url):
            logger.error("Webhook URL不正确")
            return NoticeErrorCode.PARAM_INVALID

        auth_headers = {}
        encrypted_token = cfg.get(cfg.Notice_Webhook_token)
        if encrypted_token:
            token = decode_key("webhook")
            if token:
                auth_headers["Authorization"] = f"Bearer {token}"

        msg = self.msg(msg_dict)
        try:
            response = requests.post(
                url=url,
                json=msg,
                headers={
                    **auth_headers,
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            if 200 <= response.status_code < 300:
                return NoticeErrorCode.SUCCESS

            multipart = self._multipart_payload(msg_dict)
            if response.status_code in {400, 413, 415, 422} and multipart is not None:
                data, files = multipart
                logger.debug(
                    "Webhook JSON 图片请求返回 %s，改用 multipart/form-data 重试",
                    response.status_code,
                )
                response = requests.post(
                    url=url,
                    data=data,
                    files=files,
                    headers=auth_headers,
                    timeout=15,
                )
                if 200 <= response.status_code < 300:
                    return NoticeErrorCode.SUCCESS

            logger.error(
                f"Webhook 发送失败，状态码: {response.status_code}，响应: {response.text}"
            )
            return NoticeErrorCode.RESPONSE_ERROR
        except Exception as e:
            info = normalize_network_error(e, source="webhook")
            set_notice_error_context("webhook", info)
            logger.error(info.log_message)
            return NoticeErrorCode.NETWORK_ERROR


dingtalk = DingTalk()
lark = Lark()
smtp = SMTP()
wxpusher = WxPusher()
qywx = QYWX()
gotify = Gotify()
webhook = Webhook()


class NoticeSendThread(QThread):
    """通用通知发送线程类"""

    def __init__(self):
        super().__init__()
        self.setObjectName("NoticeSendThread")
        self._stop_flag = False
        self.queue = Queue()  # 创建消息队列
        self._active_tasks = 0
        self._lock = threading.Lock()
        # 内置映射表，将通知类型映射到对应的发送函数
        self.notice_mapping = {
            "dingtalk": dingtalk_send,
            "lark": lark_send,
            "smtp": SMTP_send,
            "wxpusher": WxPusher_send,
            "qywx": QYWX_send,
            "gotify": gotify_send,
            "webhook": webhook_send,
        }

    def add_task(self, notice_type, msg_dict, status):
        """向队列添加任务，通过通知类型查找对应的发送函数"""
        send_func = self.notice_mapping.get(notice_type)
        if send_func:
            msg_dict = _normalize_message_dict(msg_dict)
            self.queue.put((send_func, msg_dict, status))
            if not self.isRunning():
                self.start()
        else:
            logger.error(f"未找到 {notice_type} 对应的通知发送函数")

    def run(self):
        """线程执行逻辑"""
        while not self._stop_flag:
            if not self.queue.empty():
                send_func, msg_dict, status = self.queue.get()
                with self._lock:
                    self._active_tasks += 1
                try:
                    result = send_func(msg_dict, status)
                    signalBus.notice_finished.emit(int(result), send_func.__name__)
                    message = format_notice_result_message(
                        send_func.__name__, int(result)
                    )
                    level = "success" if result == NoticeErrorCode.SUCCESS else "warning"
                    signalBus.info_bar_requested.emit(level, message)
                except Exception as e:
                    logger.error(f"通知线程 {send_func.__name__} 执行异常: {str(e)}")
                    signalBus.notice_finished.emit(
                        int(NoticeErrorCode.UNKNOWN_ERROR), send_func.__name__
                    )
                finally:
                    with self._lock:
                        self._active_tasks -= 1
                    self.queue.task_done()
            else:
                self.msleep(100)

    def stop(self, timeout_ms: int = 5000):
        """主动停止线程（带超时，避免退出时卡死）"""
        self._stop_flag = True
        try:
            # run() 不是事件循环，quit() 不一定生效，但调用也无害
            self.quit()
        except Exception:
            pass
        try:
            if hasattr(self, "wait"):
                if not self.wait(timeout_ms):
                    # 最后兜底：强制终止，避免 'Destroyed while thread is still running'
                    try:
                        self.terminate()
                    except Exception:
                        pass
        except Exception:
            # 极端情况下忽略停止异常，避免影响主流程退出
            pass

    def __del__(self):
        """析构函数，确保线程在对象销毁前停止"""
        self.stop()

    def is_idle(self) -> bool:
        """判断当前队列和执行状态是否空闲"""
        with self._lock:
            active = self._active_tasks
        return self.queue.empty() and active == 0

    def wait_until_idle(self, timeout: float = 5.0) -> bool:
        """等待队列处理完所有任务，最多等待 timeout 秒"""
        deadline = time.time() + timeout
        check_interval = 0.05  # 50ms 检查一次
        
        # 等待直到队列为空且没有活跃任务，或超时
        while True:
            # 检查是否空闲
            is_currently_idle = self.is_idle()
            
            if is_currently_idle:
                # 为了确保没有竞态条件，再等待一小段时间后再次检查
                # 这样可以确保在检查间隙添加的任务也能被检测到
                time.sleep(check_interval)
                if self.is_idle():
                    return True
            
            # 检查是否超时
            if time.time() >= deadline:
                # 超时后返回当前状态
                return self.is_idle()
            
            # 等待一小段时间后再次检查
            time.sleep(check_interval)


def dingtalk_send(
    msg_dict: dict | None = None,
    status: bool = False,
) -> NoticeErrorCode:
    if not status:
        logger.info(f"DingTalk 未启用")
        return NoticeErrorCode.DISABLED

    msg_dict = _normalize_message_dict(msg_dict or {"title": "Test", "text": "Test"})
    if msg_dict.get("image_bytes"):
        logger.debug("钉钉自定义机器人不支持直传截图，本次仅发送 Markdown 正文")

    APP = dingtalk
    url = APP.sign()[0]
    msg = APP.msg(msg_dict)
    headers = APP.headers

    if not url:
        logger.error("DingTalk Url空")
        return NoticeErrorCode.PARAM_EMPTY

    if not re.match(APP.correct_url, url):
        logger.error(f"dingtalk Url不正确")
        return NoticeErrorCode.PARAM_INVALID

    response = None
    try:
        response = requests.post(url=url, headers=headers, json=msg)
        status_code = response.json()[APP.codename]
    except Exception as e:
        info = normalize_network_error(e, source="dingtalk")
        set_notice_error_context("dingtalk", info)
        logger.error(
            "%s%s",
            info.log_message,
            response.json() if response is not None else "",
        )
        return NoticeErrorCode.NETWORK_ERROR

    if status_code != APP.code:
        logger.error(f"DingTalk 发送失败: {response.json()}")
        return NoticeErrorCode.RESPONSE_ERROR

    logger.info(f"DingTalk 发送成功")
    return NoticeErrorCode.SUCCESS


def lark_send(
    msg_dict: dict | None = None,
    status: bool = False,
) -> NoticeErrorCode:
    if not status:
        logger.info(f"Lark 未启用")
        return NoticeErrorCode.DISABLED

    msg_dict = _normalize_message_dict(msg_dict or {"title": "Test", "text": "Test"})
    if msg_dict.get("image_bytes"):
        logger.debug("飞书自定义机器人缺少 image_key，本次仅发送富文本正文")

    APP = lark
    url = APP.sign()[0]
    msg = APP.msg(msg_dict)
    headers = APP.headers
    if not url:
        logger.error("Lark Url空")
        return NoticeErrorCode.PARAM_EMPTY

    if not re.match(APP.correct_url, url):
        logger.error(f"Lark Url不正确")
        return NoticeErrorCode.PARAM_INVALID

    response = None
    try:
        response = requests.post(url=url, headers=headers, json=msg)
        status_code = response.json()[APP.codename]
    except Exception as e:
        info = normalize_network_error(e, source="lark")
        set_notice_error_context("lark", info)
        logger.error(
            "%s%s",
            info.log_message,
            response.json() if response is not None else "",
        )
        return NoticeErrorCode.NETWORK_ERROR

    if status_code != APP.code:
        logger.error(f"Lark 发送失败: {response.json()}")
        return NoticeErrorCode.RESPONSE_ERROR

    logger.info(f"Lark 发送成功")
    return NoticeErrorCode.SUCCESS


def SMTP_send(
    msg_dict: dict | None = None,
    status: bool = False,
) -> NoticeErrorCode:
    if not status:
        logger.info(f"SMTP 未启用")
        return NoticeErrorCode.DISABLED

    msg_dict = _normalize_message_dict(msg_dict or {"title": "Test", "text": "Test"})
    app = smtp
    result = app.send(msg_dict)  # 获取枚举结果

    if result == NoticeErrorCode.SUCCESS:
        logger.info(f"SMTP 发送成功")
    else:
        logger.error(f"SMTP 发送失败 (Error: {result.name})")

    return result


def WxPusher_send(
    msg_dict: dict | None = None,
    status: bool = False,
) -> NoticeErrorCode:
    if not status:
        logger.info(f"WxPusher 未启用")
        return NoticeErrorCode.DISABLED

    msg_dict = _normalize_message_dict(msg_dict or {"title": "Test", "text": "Test"})
    app = wxpusher
    try:
        response = requests.post(
            url="https://wxpusher.zjiecode.com/api/send/message/simple-push",
            json=app.msg(msg_dict),
        )
        status_code = response.json()["code"]
    except Exception as e:
        info = normalize_network_error(e, source="wxpusher")
        set_notice_error_context("wxpusher", info)
        logger.error(info.log_message)
        return NoticeErrorCode.NETWORK_ERROR

    if status_code != 1000:
        logger.error(f"WxPusher 发送失败: {response.json()}")
        return NoticeErrorCode.RESPONSE_ERROR

    logger.info(f"WxPusher 发送成功")
    return NoticeErrorCode.SUCCESS


def QYWX_send(
    msg_dict: dict | None = None,
    status: bool = False,
) -> NoticeErrorCode:
    if not status:
        logger.info(f"企业微信机器人消息 未启用")
        return NoticeErrorCode.DISABLED

    msg_dict = _normalize_message_dict(msg_dict or {"title": "Test", "text": "Test"})
    app = qywx
    result = app.send(msg_dict)
    return result


def gotify_send(
    msg_dict: dict | None = None,
    status: bool = False,
) -> NoticeErrorCode:
    if not status:
        logger.info(f"Gotify 未启用")
        return NoticeErrorCode.DISABLED

    msg_dict = _normalize_message_dict(msg_dict or {"title": "Test", "text": "Test"})
    app = gotify
    result = app.send(msg_dict)
    return result


def webhook_send(
    msg_dict: dict | None = None,
    status: bool = False,
) -> NoticeErrorCode:
    if not status:
        logger.info("Webhook 未启用")
        return NoticeErrorCode.DISABLED

    msg_dict = _normalize_message_dict(msg_dict or {"title": "Test", "text": "Test"})
    result = webhook.send(msg_dict)
    if result == NoticeErrorCode.SUCCESS:
        logger.info("Webhook 发送成功")
    return result


NOTICE_CHANNEL_STATUS = {
    "dingtalk": cfg.Notice_DingTalk_status,
    "lark": cfg.Notice_Lark_status,
    "smtp": cfg.Notice_SMTP_status,
    "wxpusher": cfg.Notice_WxPusher_status,
    "qywx": cfg.Notice_QYWX_status,
    "gotify": cfg.Notice_Gotify_status,
    "webhook": cfg.Notice_Webhook_status,
}

NOTICE_EVENT_CONFIG = {
    NoticeTiming.WHEN_FLOW_STARTED: cfg.when_flow_started,
    NoticeTiming.WHEN_CONNECT_SUCCESS: cfg.when_connect_success,
    NoticeTiming.WHEN_CONNECT_FAILED: cfg.when_connect_failed,
    NoticeTiming.WHEN_TASK_SUCCESS: cfg.when_task_success,
    NoticeTiming.WHEN_TASK_FAILED: cfg.when_task_failed,
    NoticeTiming.WHEN_POST_TASK: cfg.when_post_task,
    NoticeTiming.WHEN_TASK_TIMEOUT: cfg.when_task_timeout,
}


def should_send_notice(event: NoticeTiming) -> bool:
    """是否发送通知

    根据配置项判断是否应该发送通知。
    """
    config_item = NOTICE_EVENT_CONFIG.get(event)
    if config_item is None:
        logger.debug(f"未找到事件 {event.name} 对应的配置项")
        return False
    return cfg.get(config_item)


def broadcast_enabled_notices(
    title: str,
    text: str,
    image_bytes: bytes | None = None,
    *,
    content_kind: str = "simple",
) -> None:
    if content_kind == "logs":
        payload = build_log_summary(title, text, image_bytes=image_bytes)
    elif content_kind == "custom":
        payload = build_custom_message(title, text, image_bytes=image_bytes)
    else:
        payload = build_simple_message(title, text, image_bytes=image_bytes)
    msg = payload.as_message_dict()

    for channel, status_cfg in NOTICE_CHANNEL_STATUS.items():
        if cfg.get(status_cfg):
            send_thread.add_task(channel, msg, True)
            logger.debug(f"{channel}发送通知")


def send_notice(
    event: NoticeTiming,
    title: str,
    text: str,
    image_bytes: bytes | None = None,
) -> None:
    if not should_send_notice(event):
        logger.debug("跳过通知 %s (%s)，未启用对应的发送时机", event.name, int(event))
        return
    logger.debug(f"发送通知 {event.name} ({int(event)}): {title} - {text}")
    content_kind = (
        "logs"
        if event in {NoticeTiming.WHEN_POST_TASK, NoticeTiming.WHEN_TASK_TIMEOUT}
        else "simple"
    )
    broadcast_enabled_notices(
        title,
        text,
        image_bytes,
        content_kind=content_kind,
    )


def send_all_enabled_channels(
    title: str,
    text: str,
    image_bytes: bytes | None = None,
) -> None:
    """直接发送给所有已启用的外部渠道（无条件判断时机）"""
    broadcast_enabled_notices(
        title,
        text,
        image_bytes,
        content_kind="custom",
    )


send_thread = NoticeSendThread()
