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


class DingTalk:
    def __init__(self) -> None:
        data = cfg.get(cfg.Notice_Webhook)["DingTalk"]

        self.appname = str(self.__class__.__name__)
        self.url = str(data["url"])
        self.secret = str(data["secret"])
        self.correct_url = r"^https://oapi.dingtalk.com/robot/.*$"
        self.headers = {"Content-Type": "application/json"}

    def sign(self) -> str:
        # 钉钉的签名校验方法为将 sign 与 timestamp 写进 url 中
        url = self.url
        secret = self.secret

        if url == "":
            return None
        if secret == "":
            return url

        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode("utf-8")
        string_to_sign = "{}\n{}".format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        final_url = f"{url}&timestamp={timestamp}&sign={sign}"

        return final_url

    def send(self) -> None:
        url = self.sign()
        headers = self.headers
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": "PyQt-MAA 运行状态提醒",  # 对于钉钉， title 实际上不会显示在信息中
                "text": f"# Test\n\n ## Something\n\nto be continued ",  # TODO: 填充文本
            },
        }

        # 校验参数合法值
        if url is None:
            signalBus.Notice_msg.emit(
                f"{self.appname} Webhook URL 不能为空"
            )  # TODO:i18n
            return None
        if not re.match(self.correct_url, url):
            signalBus.Notice_msg.emit(
                f"{self.appname} Webhook URL 格式不正确"
            )  # TODO:i18n
            return None

        try:
            response = requests.post(
                url, headers=headers, json=message
            )  # 发送 post 请求
            status_code = response.json()["errcode"]  # 尝试获取返回码
        except Exception:
            signalBus.Notice_msg.emit(f"{self.appname} 发送失败")  # TODO:i18n
            return None

        if status_code != 0:  # 发送正常时应返回 0
            signalBus.Notice_msg.emit(
                f"{self.appname} 发送失败(Error:{status_code})"
            )  # TODO:i18n
        else:
            signalBus.Notice_msg.emit(f"{self.appname} 发送成功)")


class Lark:
    def __init__(self) -> None:
        data = cfg.get(cfg.Notice_Webhook)["Lark"]

        self.appname = str(self.__class__.__name__)
        self.url = str(data["url"])
        self.secret = str(data["secret"])
        self.correct_url = r"^https://open.feishu.cn/open-apis/bot/.*$"
        self.headers = {"Content-Type": "application/json"}

    def sign(self) -> list[str]:
        # 飞书的签名校验方法为将 sign 与 timestamp 写进 message 中
        url = self.url
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

        return [timestamp, sign]

    def send(self) -> None:
        sign_data = self.sign()
        timestamp = sign_data[0]
        sign = sign_data[1]

        url = self.url
        headers = self.headers
        message = {
            "timestamp": timestamp,
            "sign": sign,
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": "Tesr",
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": f"to be continued",
                                },
                            ]
                        ],
                    }
                }
            },
        }

        # 校验参数合法值
        if url == "":
            signalBus.Notice_msg.emit(
                f"{self.appname} Webhook URL 不能为空"
            )  # TODO:i18n
            return None
        if not re.match(self.correct_url, url):
            signalBus.Notice_msg.emit(
                f"{self.appname} Webhook URL 格式不正确"
            )  # TODO:i18n
            return None

        try:
            response = requests.post(
                url, headers=headers, json=message
            )  # 发送 post 请求
            status_code = response.json()["code"]  # 尝试获取返回码
        except Exception:
            signalBus.Notice_msg.emit(f"{self.appname} 发送失败")  # TODO:i18n
            return None

        if status_code != 0:  # 发送正常时应返回 0
            signalBus.Notice_msg.emit(
                f"{self.appname} 发送失败(Error:{status_code})"
            )  # TODO:i18n
        else:
            signalBus.Notice_msg.emit(f"{self.appname} 发送成功)")


class SMTP:
    def __init__(self) -> None:
        pass  # TODO
