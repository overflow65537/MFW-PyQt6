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
        self._stop_flag = False  # 添加退出标志

    def run(self):
        startupinfo = None
        if sys.platform.startswith('win'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            self.process = subprocess.Popen(
                [self.command, *self.args],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='gbk',
                errors='replace',
                startupinfo=startupinfo
            )

            while self.process.poll() is None and not self._stop_flag:
                assert self.process.stdout is not None, "stdout 应为 PIPE，不可能为 None"
                output = self.process.stdout.readline()
                # 过滤ANSI码和时间戳
                clean_output = re.sub(
                    r'(\x1B\[[0-?]*[ -/]*[@-~])|(^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}[ \t]*)', 
                    '', 
                    output.strip()
                )
                self.output_signal.emit(clean_output.strip())
        except Exception as e:
            print(f"线程运行出错: {e}")
        finally:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait()

    def stop(self):
        self._stop_flag = True  # 设置退出标志
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        self.quit()  # 请求线程退出
        self.wait()  # 等待线程退出