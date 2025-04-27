# 外部通知实现
import re
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import smtplib
from email.mime.text import MIMEText

from ..common.signal_bus import signalBus
from ..common.config import cfg
from ..utils.logger import logger


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
                "title": msg_dict["Title"],
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
            return None
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

        self.Open_SSL = True  # TODO
        self.Open_Login = True  # TODO

    def msg(self, msg_dict: dict) -> MIMEText:
        msg_text = f"{self.sendtime}: " + msg_dict["text"]
        msg = MIMEText(msg_text, "html", "utf-8")
        msg["Subject"] = msg_dict["title"]
        msg["From"] = self.send_mail
        msg["To"] = self.receive_mail

        return msg

    def send(self, msg_dict: dict) -> bool:
        msg = self.msg(msg_dict)
        if self.Open_SSL and self.sever_port == 443:
            smtp = smtplib.SMTP_SSL(self.sever_address, self.sever_port)
        else:
            smtp = smtplib.SMTP(self.sever_address, self.sever_port)

        if self.Open_Login:
            smtp.login(self.uesr_name, self.password)

        try:
            smtp.sendmail(self.send_mail, self.receive_mail, msg.as_string())
        finally:
            smtp.quit()


class WxPusher:
    def msg(self, msg_dict: dict) -> dict:
        sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        msg_text = f"{sendtime}: {msg_dict["text"]}"
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
        msg_text = f"{sendtime}: {msg_dict["text"]}"
        msg = {
            "msgtype": "text",
            "text": {
                "content": msg_dict["title"] + msg_text
            }
        }
        return msg

    def send(self, msg_type: dict) -> bool:
        QYWX_KEY = cfg.get(cfg.Notice_QYWX_key)
        url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}"
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


def dingtalk_send(
    msg_text: dict = {"title": "Test", "text": "Test"}, status: bool = False
) -> bool:
    if not status:
        logger.info(f"DingTalk 未启用")
        return False
    APP = DingTalk()

    url = APP.sign()[0]
    msg = APP.msg(msg_text)
    headers = APP.headers
    if url is None:
        logger.error("dingtalk Url空")
        cfg.set(cfg.Notice_DingTalk_status, False)
        return False
    if not re.match(APP.correct_url, url):
        logger.error(f"dingtalk Url不正确")
        cfg.set(cfg.Notice_DingTalk_status, False)
        return False

    try:
        response = requests.post(url=url, headers=headers, json=msg)
        status_code = response.json()[APP.codename]
    except Exception:
        logger.error(f"DingTalk 发送失败 {response.json()}")
        cfg.set(cfg.Notice_DingTalk_status, False)
        signalBus.Notice_msg.emit(f"DingTalk Failed")
        return False

    if status_code != APP.code:
        logger.error(f"DingTalk 发送失败 {response.json()}")
        cfg.set(cfg.Notice_DingTalk_status, False)
        signalBus.Notice_msg.emit(f"DingTalk Failed")
        return False
    else:
        logger.info(f"DingTalk 发送成功")
        signalBus.Notice_msg.emit(f"DingTalk success")
        return True


def lark_send(
    msg_dict: dict = {"title": "Test", "text": "Test"}, status: bool = False
) -> bool:
    if not status:
        logger.info(f"Lark 未启用")
        return False
    APP = Lark()

    url = APP.sign()[0]
    msg = APP.msg(msg_dict)
    headers = APP.headers
    if url is None:
        logger.error("Lark Url空")
        cfg.set(cfg.Notice_Lark_status, False)
        signalBus.Notice_msg.emit("Lark Failed")
        return False
    if not re.match(APP.correct_url, url):
        logger.error(f"Lark Url不正确")
        cfg.set(cfg.Notice_Lark_status, False)
        signalBus.Notice_msg.emit("Lark Failed")
        return False

    try:
        response = requests.post(url=url, headers=headers, json=msg)
        status_code = response.json()[APP.codename]
    except Exception:
        logger.error(f"Lark 发送失败 {response.json()}")
        signalBus.Notice_msg.emit(f"Lark failed")
        return False

    if status_code != APP.code:
        logger.error(f"Lark 发送失败 {response.json()}")
        signalBus.Notice_msg.emit(f"Lark failed")
        return False
    else:
        logger.info(f"Lark 发送成功")
        signalBus.Notice_msg.emit(f"Lark success")
        return True


def SMTP_send(
    msg_dict: dict = {"title": "Test", "text": "Test"}, status: bool = False
) -> bool:
    if status:
        app = SMTP()
        status = app.send(msg_dict=msg_dict)
        if status:  # 发送正常情况下，返回值应为 {}
            logger.error(f"SMTP 发送失败 {status}")
            cfg.set(cfg.Notice_SMTP_status, False)
            signalBus.Notice_msg.emit(f"SMTP failed")
            return False
        else:
            logger.info(f"SMTP 发送成功")
            signalBus.Notice_msg.emit(f"SMTP success")
            return True
    else:
        logger.info(f"SMTP 未启用")
        return False


def WxPusher_send(
    msg_dict: str = {"title": "Test", "text": "Test"}, status: bool = False
) -> bool:
    if status:
        status = WxPusher().send(msg_dict)
        if status:
            logger.info(f"WxPusher 发送成功")
            signalBus.Notice_msg.emit(f"WxPusher success")
            return True
        else:
            cfg.set(cfg.Notice_WxPusher_status, False)
            signalBus.Notice_msg.emit(f"WxPusher failed")
            return False

    else:
        logger.info(f"WxPusher 未启用")
        return False

def QYWX_send(
    msg_dict: str = {"title": "Test", "text": "Test"}, status: bool = False
) -> bool:
    if status:
        status = QYWX().send(msg_dict)
        if status:
            logger.info(f"企业微信机器人消息 发送成功")
            signalBus.Notice_msg.emit(f"QYWX success")
            return True
        else:
            cfg.set(cfg.Notice_QYWX_status, False)
            signalBus.Notice_msg.emit(f"QYWX failed")
            return False

    else:
        logger.info(f"企业微信机器人消息 未启用")
        return False
