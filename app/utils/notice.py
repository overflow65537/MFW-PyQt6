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
MFW-ChainFlow Assistant 外部通知单元
作者:weinibuliu，overflow65537,FDrag0n
"""

import re
import time
import hmac
import hashlib
import base64
import urllib.parse
from enum import IntEnum

import requests
import smtplib
from email.mime.text import MIMEText
from queue import Queue
from PySide6.QtCore import QThread

from app.common.signal_bus import signalBus
from app.common.config import cfg
from app.utils.logger import logger
from app.utils.crypto import crypto_manager


# 解码密钥
def decode_key(key_name) -> str:
    mapping = {
        "dingtalk": cfg.Notice_DingTalk_secret,
        "lark": cfg.Notice_Lark_secret,
        "smtp": cfg.Notice_SMTP_password,
        "wxpusher": cfg.Notice_WxPusher_SPT_token,
        "QYWX": cfg.Notice_QYWX_key,
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
        sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        msg_text = f"{sendtime}: " + msg_dict["text"]
        msg = {
            "msgtype": "markdown",
            "markdown": {
                "title": msg_dict["title"],
                "text": msg_text,
            },
        }

        return msg

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
        sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

        msg_text = f"{sendtime}: " + msg_dict["text"]

        sign_cache = self.sign()
        msg = {
            "timestamp": sign_cache[1],
            "sign": sign_cache[2],
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": msg_dict["title"],
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": msg_text,
                                },
                            ]
                        ],
                    }
                }
            },
        }
        return msg

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
    def msg(self, msg_dict: dict) -> MIMEText:
        sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        msg_text = f"{sendtime}: " + msg_dict["text"]
        msg = MIMEText(msg_text, "plain", "utf-8")
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
            logger.error(f"SMTP 连接失败: {e}")
            return NoticeErrorCode.SMTP_CONNECT_FAILED

        try:
            smtp.sendmail(
                cfg.get(cfg.Notice_SMTP_user_name),
                cfg.get(cfg.Notice_SMTP_receive_mail),
                msg.as_string(),
            )
            return NoticeErrorCode.SUCCESS
        except Exception as e:
            logger.error(f"SMTP 发送邮件失败: {e}")
            return NoticeErrorCode.NETWORK_ERROR
        finally:
            smtp.quit()


class WxPusher:
    def msg(self, msg_dict: dict) -> dict:
        sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        msg_text = f"{sendtime}: {msg_dict['text']}"
        msg = {
            "content": msg_text,
            "summary": msg_dict["title"],
            "contentType": 1,
            "spt": decode_key("wxpusher"),
            "sptList": [cfg.get(cfg.Notice_WxPusher_SPT_token)],
        }
        return msg

    def send(self, msg_type: dict) -> bool:

        url = "https://wxpusher.zjiecode.com/api/send/message/simple-push"
        msg = self.msg(msg_type)
        try:
            response = requests.post(url=url, json=msg)
            status_code = response.json()["code"]
        except Exception as e:
            logger.error(f"WxPusher 发送失败 {e}")
            return False

        if status_code != 1000:
            logger.error(f"WxPusher 发送失败 {response.json()}")
            return False

        else:
            return True


class QYWX:
    def msg(self, msg_dict: dict) -> dict:
        sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        msg_text = f"{sendtime}: {msg_dict['text']}"
        msg = {"msgtype": "text", "text": {"content": msg_dict["title"] + msg_text}}
        return msg

    def send(self, msg_dict: dict) -> NoticeErrorCode:
        QYWX_KEY = decode_key("QYWX")
        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}"
        msg = self.msg(msg_dict)
        try:
            response = requests.post(url=url, json=msg)
            status_code = response.json()["errcode"]
        except Exception as e:
            logger.error(f"企业微信机器人消息 发送失败 {e}")
            return NoticeErrorCode.NETWORK_ERROR

        if status_code != 0:
            logger.error(f"企业微信机器人消息 发送失败 {response.json()}")
            return NoticeErrorCode.RESPONSE_ERROR
        else:
            return NoticeErrorCode.SUCCESS


dingtalk = DingTalk()
lark = Lark()
smtp = SMTP()
wxpusher = WxPusher()
qywx = QYWX()


class NoticeSendThread(QThread):
    """通用通知发送线程类"""

    def __init__(self):
        super().__init__()
        self.setObjectName("NoticeSendThread")
        self._stop_flag = False
        self.queue = Queue()  # 创建消息队列
        # 内置映射表，将通知类型映射到对应的发送函数
        self.notice_mapping = {
            "dingtalk": dingtalk_send,
            "lark": lark_send,
            "smtp": SMTP_send,
            "wxpusher": WxPusher_send,
            "qywx": QYWX_send,
        }

    def add_task(self, notice_type, msg_dict, status):
        """向队列添加任务，通过通知类型查找对应的发送函数"""
        send_func = self.notice_mapping.get(notice_type)
        if send_func:
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
                try:
                    result = send_func(msg_dict, status)
                    signalBus.notice_finished.emit(int(result), send_func.__name__)
                    # 根据枚举类型显示不同的提示
                    match result:
                        case NoticeErrorCode.SUCCESS:
                            signalBus.info_bar_requested.emit(
                                "success",
                                send_func.__name__
                                + self.tr(" sent successfully."),
                            )
                        case NoticeErrorCode.DISABLED:
                            signalBus.info_bar_requested.emit(
                                "warning",
                                send_func.__name__
                                + self.tr(" disabled."),
                            )
                        case NoticeErrorCode.PARAM_EMPTY:
                            signalBus.info_bar_requested.emit(
                                "warning",
                                send_func.__name__
                                + self.tr(" param empty."),
                            )
                        case NoticeErrorCode.PARAM_INVALID:
                            signalBus.info_bar_requested.emit(
                                "warning",
                                send_func.__name__
                                + self.tr(" param invalid."),
                            )
                        case NoticeErrorCode.NETWORK_ERROR:
                            signalBus.info_bar_requested.emit(
                                "warning",
                                send_func.__name__
                                + self.tr(" network error."),
                            )
                        case NoticeErrorCode.RESPONSE_ERROR:
                            signalBus.info_bar_requested.emit(
                                "warning",
                                send_func.__name__
                                + self.tr(" response error."),
                            )
                        case NoticeErrorCode.UNKNOWN_ERROR:
                            signalBus.info_bar_requested.emit(
                                "warning",
                                send_func.__name__
                                + self.tr(" unknown error."),
                            )
                        case NoticeErrorCode.SMTP_PORT_INVALID:
                            signalBus.info_bar_requested.emit(
                                "warning",
                                send_func.__name__
                                + self.tr(" smtp port invalid."),
                            )
                        case NoticeErrorCode.SMTP_CONNECT_FAILED:
                            signalBus.info_bar_requested.emit(
                                "warning",
                                send_func.__name__
                                + self.tr(" smtp connect failed."),
                            )
                        case _:
                            signalBus.info_bar_requested.emit(
                                "warning",
                                send_func.__name__
                                + self.tr(" unknown error."),
                            )
                except Exception as e:
                    logger.error(f"通知线程 {send_func.__name__} 执行异常: {str(e)}")
                    signalBus.notice_finished.emit(
                        int(NoticeErrorCode.UNKNOWN_ERROR), send_func.__name__
                    )
            else:
                self.msleep(100)

    def stop(self):
        """主动停止线程"""
        self._stop_flag = True
        self.wait()

    def __del__(self):
        """析构函数，确保线程在对象销毁前停止"""
        self.stop()


def dingtalk_send(
    msg_dict: dict = {"title": "Test", "text": "Test"}, status: bool = False
) -> NoticeErrorCode:
    if not status:
        logger.info(f"DingTalk 未启用")
        return NoticeErrorCode.DISABLED

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
        logger.error(f"DingTalk 发送失败: {e}{response.json() if response else ''}")
        return NoticeErrorCode.NETWORK_ERROR

    if status_code != APP.code:
        logger.error(f"DingTalk 发送失败: {response.json()}")
        return NoticeErrorCode.RESPONSE_ERROR

    logger.info(f"DingTalk 发送成功")
    return NoticeErrorCode.SUCCESS


def lark_send(
    msg_dict: dict = {"title": "Test", "text": "Test"}, status: bool = False
) -> NoticeErrorCode:
    if not status:
        logger.info(f"Lark 未启用")
        return NoticeErrorCode.DISABLED

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
        logger.error(f"Lark 发送失败: {e}{response.json() if response else ''}")
        return NoticeErrorCode.NETWORK_ERROR

    if status_code != APP.code:
        logger.error(f"Lark 发送失败: {response.json()}")
        return NoticeErrorCode.RESPONSE_ERROR

    logger.info(f"Lark 发送成功")
    return NoticeErrorCode.SUCCESS


def SMTP_send(
    msg_dict: dict = {"title": "Test", "text": "Test"}, status: bool = False
) -> NoticeErrorCode:
    if not status:
        logger.info(f"SMTP 未启用")
        return NoticeErrorCode.DISABLED

    app = smtp
    result = app.send(msg_dict)  # 获取枚举结果

    if result == NoticeErrorCode.SUCCESS:
        logger.info(f"SMTP 发送成功")
    else:
        logger.error(f"SMTP 发送失败 (Error: {result.name})")

    return result


def WxPusher_send(
    msg_dict: dict[str, str] = {"title": "Test", "text": "Test"}, status: bool = False
) -> NoticeErrorCode:
    if not status:
        logger.info(f"WxPusher 未启用")
        return NoticeErrorCode.DISABLED

    app = wxpusher
    try:
        response = requests.post(
            url="https://wxpusher.zjiecode.com/api/send/message/simple-push",
            json=app.msg(msg_dict),
        )
        status_code = response.json()["code"]
    except Exception as e:
        logger.error(f"WxPusher 发送失败: {e}")
        return NoticeErrorCode.NETWORK_ERROR

    if status_code != 1000:
        logger.error(f"WxPusher 发送失败: {response.json()}")
        return NoticeErrorCode.RESPONSE_ERROR

    logger.info(f"WxPusher 发送成功")
    return NoticeErrorCode.SUCCESS


def QYWX_send(
    msg_dict: dict[str, str] = {"title": "Test", "text": "Test"}, status: bool = False
) -> NoticeErrorCode:
    if not status:
        logger.info(f"企业微信机器人消息 未启用")
        return NoticeErrorCode.DISABLED

    app = qywx
    result = app.send(msg_dict)
    return result


NOTICE_CHANNEL_STATUS = {
    "dingtalk": cfg.Notice_DingTalk_status,
    "lark": cfg.Notice_Lark_status,
    "smtp": cfg.Notice_SMTP_status,
    "wxpusher": cfg.Notice_WxPusher_status,
    "qywx": cfg.Notice_QYWX_status,
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


def broadcast_enabled_notices(title: str, text: str) -> None:
    msg = {"title": title, "text": text}
    for channel, status_cfg in NOTICE_CHANNEL_STATUS.items():
        if cfg.get(status_cfg):
            send_thread.add_task(channel, msg, True)
            logger.debug(f"{channel}发送通知")


def send_notice(event: NoticeTiming, title: str, text: str) -> None:
    if not should_send_notice(event):
        logger.debug("跳过通知 %s (%s)，未启用对应的发送时机", event.name, int(event))
        return
    logger.debug(f"发送通知 {event.name} ({int(event)}): {title} - {text}")
    broadcast_enabled_notices(title, text)


def send_all_enabled_channels(title: str, text: str) -> None:
    """直接发送给所有已启用的外部渠道（无条件判断时机）"""
    broadcast_enabled_notices(title, text)


send_thread = NoticeSendThread()
