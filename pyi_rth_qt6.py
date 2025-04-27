import os
import sys

def _qtdialog_path_fix():
    if sys.platform == 'darwin':
        # 修正Qt插件路径
        plugin_path = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6', 'plugins')
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

_qtdialog_path_fix()
