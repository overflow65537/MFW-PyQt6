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
作者:overflow65537
"""

import re
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import smtplib
from email.mime.text import MIMEText
from PySide6.QtCore import QThread

from ..common.signal_bus import signalBus
from ..common.config import cfg
from ..utils.logger import logger
from ..utils.notice_enum import NoticeErrorCode


class DingTalk:
    def __init__(self) -> None:
        self.sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.correct_url = r"^https://oapi.dingtalk.com/robot/.*$"
        self.url = cfg.get(cfg.Notice_DingTalk_url)
        self.secret = cfg.get(cfg.Notice_DingTalk_secret)
        self.headers = {"Content-Type": "application/json"}
        self.codename = "errcode"
        self.code = 0

    def msg(self, msg_dict: dict) -> dict:

        msg_text = f"{self.sendtime}: " + msg_dict["text"]
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
        url = self.url
        secret = self.secret

        if url == "":
            logger.error("DingTalk 通知地址为空")
            cfg.set(cfg.Notice_DingTalk_status, False)
            return [url]
        if secret == "":
            logger.error("DingTalk 密钥为空")
            cfg.set(cfg.Notice_DingTalk_status, False)
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
        self.sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.correct_url = r"^https://open.feishu.cn/open-apis/bot/.*$"
        self.url = cfg.get(cfg.Notice_Lark_url)
        self.secret = cfg.get(cfg.Notice_Lark_secret)
        self.headers = {"Content-Type": "application/json"}
        self.codename = "code"
        self.code = 0

    def msg(self, msg_dict: dict) -> dict:

        msg_text = f"{self.sendtime}: " + msg_dict["text"]

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
        secret = self.secret
        timestamp = str(round(time.time()))
        # 拼接timestamp和secret
        string_to_sign = "{}\n{}".format(timestamp, secret)
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        # 对结果进行base64处理
        sign = base64.b64encode(hmac_code).decode("utf-8")

        return [self.url, timestamp, sign]


class SMTP:
    def __init__(self) -> None:
        self.sever_address = cfg.get(cfg.Notice_SMTP_sever_address)
        self.sever_port = cfg.get(cfg.Notice_SMTP_sever_port)
        self.uesr_name = cfg.get(cfg.Notice_SMTP_user_name)
        self.password = cfg.get(cfg.Notice_SMTP_password)
        self.send_mail = cfg.get(cfg.Notice_SMTP_user_name)
        self.receive_mail = cfg.get(cfg.Notice_SMTP_receive_mail)
        self.sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.used_ssl = cfg.get(cfg.Notice_SMTP_used_ssl)

    def msg(self, msg_dict: dict) -> MIMEText:
        msg_text = f"{self.sendtime}: " + msg_dict["text"]
        msg = MIMEText(msg_text, "html", "utf-8")
        msg["Subject"] = msg_dict["title"]
        msg["From"] = self.send_mail
        msg["To"] = self.receive_mail

        return msg

    def send(self, msg_dict: dict) -> NoticeErrorCode:  
        msg = self.msg(msg_dict)
        try:
            port = int(self.sever_port)
        except ValueError:
            logger.error(f"SMTP 端口号 {self.sever_port} 不是有效的整数")
            return NoticeErrorCode.SMTP_PORT_INVALID  

        try:
            if self.used_ssl:
                smtp = smtplib.SMTP_SSL(self.sever_address, port)
                smtp.login(self.uesr_name, self.password)
            else:
                smtp = smtplib.SMTP(self.sever_address, port, timeout=1)
        except Exception as e:
            logger.error(f"SMTP 连接失败: {e}")
            return NoticeErrorCode.SMTP_CONNECT_FAILED  

        try:
            smtp.sendmail(self.send_mail, self.receive_mail, msg.as_string())
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
            "spt": cfg.get(cfg.Notice_WxPusher_SPT_token),
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

    def send(self, msg_type: dict) -> bool:
        QYWX_KEY = cfg.get(cfg.Notice_QYWX_key)
        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}"
        msg = self.msg(msg_type)
        try:
            response = requests.post(url=url, json=msg)
            status_code = response.json()["errcode"]
        except Exception as e:
            logger.error(f"企业微信机器人消息 发送失败 {e}")
            return False

        if status_code != 0:
            logger.error(f"企业微信机器人消息 发送失败 {response.json()}")
            return False

        else:
            return True

class NoticeSendThread(QThread):
    """通用通知发送线程类"""
    def __init__(self, send_func, msg_dict: dict, status: bool) -> None:
        super().__init__()
        self.send_func = send_func
        self.msg_dict = msg_dict
        self.status = status

    def run(self):
        result = self.send_func(self.msg_dict, self.status)
        #返回方法的string值
        signalBus.notice_finished.emit(result,self.send_func.__name__)

def dingtalk_send(
    msg_dict: dict = {"title": "Test", "text": "Test"}, status: bool = False
) -> NoticeErrorCode:  
    if not status:
        logger.info(f"DingTalk 未启用")
        return NoticeErrorCode.DISABLED

    APP = DingTalk()
    url = APP.sign()[0]
    msg = APP.msg(msg_dict)
    headers = APP.headers

    if not url:
        logger.error("DingTalk Url空")
        cfg.set(cfg.Notice_DingTalk_status, False)
        return NoticeErrorCode.PARAM_EMPTY

    if not re.match(APP.correct_url, url):
        logger.error(f"dingtalk Url不正确")
        cfg.set(cfg.Notice_DingTalk_status, False)
        return NoticeErrorCode.PARAM_INVALID

    response = None
    try:
        response = requests.post(url=url, headers=headers, json=msg)
        status_code = response.json()[APP.codename]
    except Exception as e:
        logger.error(f"DingTalk 发送失败: {e}{response.json() if response else ''}")
        cfg.set(cfg.Notice_DingTalk_status, False)
        return NoticeErrorCode.NETWORK_ERROR

    if status_code != APP.code:
        logger.error(f"DingTalk 发送失败: {response.json()}")
        cfg.set(cfg.Notice_DingTalk_status, False)
        return NoticeErrorCode.RESPONSE_ERROR

    logger.info(f"DingTalk 发送成功")
    return NoticeErrorCode.SUCCESS


def lark_send(
    msg_dict: dict = {"title": "Test", "text": "Test"}, status: bool = False
) -> NoticeErrorCode:  
    if not status:
        logger.info(f"Lark 未启用")
        return NoticeErrorCode.DISABLED  

    APP = Lark()
    url = APP.sign()[0]
    msg = APP.msg(msg_dict)
    headers = APP.headers

    if not url:
        logger.error("Lark Url空")
        cfg.set(cfg.Notice_Lark_status, False)
        return NoticeErrorCode.PARAM_EMPTY  

    if not re.match(APP.correct_url, url):
        logger.error(f"Lark Url不正确")
        cfg.set(cfg.Notice_Lark_status, False)
        return NoticeErrorCode.PARAM_INVALID  

    response = None
    try:
        response = requests.post(url=url, headers=headers, json=msg)
        status_code = response.json()[APP.codename]
    except Exception as e:
        logger.error(f"Lark 发送失败: {e}{response.json() if response else ''}")
        cfg.set(cfg.Notice_Lark_status, False)
        return NoticeErrorCode.NETWORK_ERROR  

    if status_code != APP.code:
        logger.error(f"Lark 发送失败: {response.json()}")
        cfg.set(cfg.Notice_Lark_status, False)
        return NoticeErrorCode.RESPONSE_ERROR 

    logger.info(f"Lark 发送成功")
    return NoticeErrorCode.SUCCESS  


def SMTP_send(
    msg_dict: dict = {"title": "Test", "text": "Test"}, status: bool = False
) -> NoticeErrorCode:  
    if not status:
        logger.info(f"SMTP 未启用")
        return NoticeErrorCode.DISABLED  

    app = SMTP()
    result = app.send(msg_dict)  # 获取枚举结果

    if result == NoticeErrorCode.SUCCESS:
        logger.info(f"SMTP 发送成功")
    else:
        logger.error(f"SMTP 发送失败 (Error: {result.name})")
        cfg.set(cfg.Notice_SMTP_status, False)

    return result

def WxPusher_send(
    msg_dict: dict[str, str] = {"title": "Test", "text": "Test"}, status: bool = False
) -> NoticeErrorCode:  
    if not status:
        logger.info(f"WxPusher 未启用")
        return NoticeErrorCode.DISABLED  

    app = WxPusher()
    try:
        response = requests.post(
            url="https://wxpusher.zjiecode.com/api/send/message/simple-push",
            json=app.msg(msg_dict)
        )
        status_code = response.json()["code"]
    except Exception as e:
        logger.error(f"WxPusher 发送失败: {e}")
        cfg.set(cfg.Notice_WxPusher_status, False)
        return NoticeErrorCode.NETWORK_ERROR  

    if status_code != 1000:
        logger.error(f"WxPusher 发送失败: {response.json()}")
        cfg.set(cfg.Notice_WxPusher_status, False)
        return NoticeErrorCode.RESPONSE_ERROR 

    logger.info(f"WxPusher 发送成功")
    return NoticeErrorCode.SUCCESS  


def QYWX_send(
    msg_dict: dict[str, str] = {"title": "Test", "text": "Test"}, status: bool = False
) -> NoticeErrorCode:  
    if not status:
        logger.info(f"企业微信机器人消息 未启用")
        return NoticeErrorCode.DISABLED  

    app = QYWX()
    QYWX_KEY = cfg.get(cfg.Notice_QYWX_key)
    if not QYWX_KEY:
        logger.error("企业微信机器人Key为空")
        cfg.set(cfg.Notice_QYWX_status, False)
        return NoticeErrorCode.PARAM_EMPTY  

    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}"
    msg = app.msg(msg_dict)

    try:
        response = requests.post(url=url, json=msg)
        status_code = response.json()["errcode"]
    except Exception as e:
        logger.error(f"企业微信机器人消息 发送失败: {e}")
        cfg.set(cfg.Notice_QYWX_status, False)
        return NoticeErrorCode.NETWORK_ERROR  

    if status_code != 0:
        logger.error(f"企业微信机器人消息 发送失败: {response.json()}")
        cfg.set(cfg.Notice_QYWX_status, False)
        return NoticeErrorCode.RESPONSE_ERROR 

    logger.info(f"企业微信机器人消息 发送成功")
    return NoticeErrorCode.SUCCESS  