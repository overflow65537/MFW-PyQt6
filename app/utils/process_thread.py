import re
import subprocess
import sys
from PySide6.QtCore import QThread

from ..common.signal_bus import signalBus

class ProcessThread(QThread):
    output_signal = signalBus.agent_info

    def __init__(self, command, args):
        super().__init__()
        self.command = command
        self.args = args
        self.process = None

    def run(self):
        # 新增代码，用于设置不显示窗口
        startupinfo = None
        if sys.platform.startswith('win'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        self.process = subprocess.Popen(
            [self.command, *self.args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,  # 替代 universal_newlines
            encoding='gbk',  # 明确指定编码
            errors='replace',  # 替换无法解码的字符
            startupinfo=startupinfo  # 使用设置好的 startupinfo
        )

        while self.process.poll() is None:
            output = self.process.stdout.readline()
            # 同时过滤ANSI码和时间戳
            clean_output = re.sub(
                r'(\x1B\[[0-?]*[ -/]*[@-~])|(^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}[ \t]*)', 
                '', 
                output.strip()
            )
            self.output_signal.emit(clean_output.strip())

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()