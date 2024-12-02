# coding:utf-8
import os
import sys
from qasync import QEventLoop

from PyQt6.QtCore import Qt, QTranslator
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.view.main_window import MainWindow
from app.common.config import Language
from app.common.signal_bus import signalBus


# 检查资源文件是否存在
maa_config_name = cfg.get(cfg.maa_config_name)
maa_config_path = cfg.get(cfg.maa_config_path)
maa_resource_name = cfg.get(cfg.maa_resource_name)
maa_resource_path = cfg.get(cfg.maa_resource_path)
maa_config_list = cfg.get(cfg.maa_config_list)
maa_resource_list = cfg.get(cfg.maa_resource_list)
if (
    maa_config_name == ""
    or maa_config_path == ""
    or maa_resource_name == ""
    or maa_resource_path == ""
    or maa_config_list == {}
    or maa_resource_list == {}
):
    cfg.set(cfg.resource_exist, False)
    maa_config_name = ""
    maa_config_path = ""
    maa_resource_name = ""
    maa_resource_path = ""
    maa_config_list = {}
    maa_resource_list = {}
else:
    cfg.set(cfg.resource_exist, True)
    signalBus.resource_exist.emit(True)


# enable dpi scale
if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

# create application
app = QApplication(sys.argv)
app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

# internationalization
locale = cfg.get(cfg.language)
translator = FluentTranslator(locale.value)
galleryTranslator = QTranslator()
if locale == Language.CHINESE_SIMPLIFIED:
    galleryTranslator.load(os.path.join(os.getcwd(), "i18n", "i18n.zh_CN.qm"))
    print("load chinese simplified")

elif locale == Language.CHINESE_TRADITIONAL:
    galleryTranslator.load(os.path.join(os.getcwd(), "i18n", "i18n.zh_HK.qm"))
    print("load chinese traditional")
elif locale == Language.ENGLISH:
    galleryTranslator.load()
    print("load english")
app.installTranslator(translator)
app.installTranslator(galleryTranslator)

# create main window
w = MainWindow()
w.show()

loop = QEventLoop(app)
loop.run_forever()
