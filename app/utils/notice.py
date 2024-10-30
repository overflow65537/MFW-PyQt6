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
        self.sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.correct_url = r"^https://oapi.dingtalk.com/robot/.*$"
        self.url = str(data["url"])
        self.secret = str(data["secret"])
        self.headers = {"Content-Type": "application/json"}
        self.codename = "errcode"
        self.code = 0

    def msg(self, msg_type: str) -> dict:
        if msg_type == "Test":
            msg_text = "# 信息发送测试\n\n这是一段具有十六个汉字的文本测试"
        elif msg_type == "Completed":
            msg_text = "# 任务完成通知\n\n任务已完成。"
        elif msg_type == "Timeout":
            msg_text = "# 任务失败通知\n\n任务因超时而未能完成，请检查运行状态。"

        msg_text = msg_text + f"\n\n{self.sendtime}"
        msg = {
            "msgtype": "markdown",
            "markdown": {
                "title": "Title",
                "text": msg_text,
            },
        }

        return msg


    def sign(self) -> list[str]:
        # 钉钉的签名校验方法为将 sign 与 timestamp 组合进 url 中
        url = self.url
        secret = self.secret

        if url == "":
            return None
        if secret == "":
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
        data = cfg.get(cfg.Notice_Webhook)["Lark"]
        self.sendtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.correct_url = r"^https://open.feishu.cn/open-apis/bot/.*$"
        self.url = str(data["url"])
        self.secret = str(data["secret"])
        self.headers = {"Content-Type": "application/json"}
        self.codename = "code"
        self.code = 0

    def msg(self, msg_type: str) -> dict:
        if msg_type == "Test":
            msg_title = "信息发送测试"
            msg_text = "这是一段具有十六个汉字的文本测试"
        elif msg_type == "Completed":
            msg_title = "任务完成通知"
            msg_text = "任务已完成。"
        elif msg_type == "Timeout":
            msg_title = "任务失败通知"
            msg_text = "任务因超时而未能完成，请检查运行状态。"

        msg_text = msg_text + f"\n{self.sendtime}"

        sign_cache = self.sign()
        msg = {
            "timestamp": sign_cache[1],
            "sign": sign_cache[2],
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": msg_title,
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
        data = cfg.get(cfg.Notice_SMTP)
        self.sever_address = data["sever_address"]
        self.sever_port = data["sever_port"]
        self.uesr_name = data["user_name"]
        self.password = data["password"]
        self.send_mail = data["send_mail"]
        self.receive_mail = data["receive_mail"]

        self.Open_SSL = True  # TODO
        self.Open_Login = True  # TODO

    def msg(self, msg_type: str) -> MIMEText:
        if msg_type == "Test":
            msg_text = "这是一段具有十六个汉字的文本测试"
            msg = MIMEText(msg_text, "html", "utf-8")
            msg["Subject"] = "信息发送测试"
        elif msg_type == "Completed":
            msg_text = "任务已完成。"
            msg = MIMEText(msg_text, "html", "utf-8")
            msg["Subject"] = "任务完成通知"
        elif msg_type == "Timeout":
            msg_text = "任务因超时而未能完成，请检查运行状态。"
            msg = MIMEText(msg_text, "html", "utf-8")
            msg["Subject"] = "任务失败通知"

        msg["From"] = self.send_mail
        msg["To"] = self.receive_mail

        return msg

    def send(self, msg_type: str) -> bool:
        msg = self.msg(msg_type)
        if self.Open_SSL:
            smtp = smtplib.SMTP_SSL(self.sever_address, self.sever_port)
        else:
            smtp = smtplib.SMTP(self.sever_address, self.sever_port)

        if self.Open_Login:
            smtp.login(self.uesr_name, self.password)

        try:
            smtp.sendmail(self.send_mail, self.receive_mail, msg.as_string())
        finally:
            smtp.quit()


def webhook_send(appname: str, msg_type: str = "Test") -> bool:
    # appname: "DingTalk" | "Lark"
    # msg_type: "Test" | "Completed" | "Timeout"
    # 当发送成功时，返回 True ，其余情况均返回 False

    if appname == "DingTalk":
        APP = DingTalk()
    elif appname == "Lark":
        APP = Lark()
    else:
        signalBus.Notice_msg.emit("不支持的发送方式")
        return False

    url = APP.sign()[0]
    msg = APP.msg(msg_type)
    headers = APP.headers
    if url is None:
        print("Url is None")
        signalBus.Notice_msg.emit("Url 不能为空")
        return False
    if not re.match(APP.correct_url, url):
        signalBus.Notice_msg.emit("Url 格式不正确")
        return False

    try:
        response = requests.post(url=url, headers=headers, json=msg)
        status_code = response.json()[APP.codename]
    except Exception:
        print("response failed")
        signalBus.Notice_msg.emit(f"{appname} 发送失败")
        return False

    if status_code != APP.code:
        print("send failed")
        signalBus.Notice_msg.emit(f"{appname} 发送失败 (Error:{status_code})")
        return False
    else:
        print("send success")
        signalBus.Notice_msg.emit(f"{appname} 发送成功")
        return True


def SMTP_send(msg_type: str = "Test") -> bool:
    status = SMTP.send(msg_type)
    if status:  # 发送正常情况下，返回值应为 {}
        signalBus.Notice_msg.emit(f"SMTP 发送失败")
        return False
    else:
        signalBus.Notice_msg.emit(f"SMTP 发送成功")
        return True

    if status_code != APP.code:
        print("send failed")
        signalBus.Notice_msg.emit(f"{appname} 发送失败 (Error:{status_code})")
        return False
    else:
        print("send success")
        signalBus.Notice_msg.emit(f"{appname} 发送成功")
        return True
