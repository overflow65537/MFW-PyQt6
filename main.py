# coding:utf-8
import os
import sys

from PyQt6.QtCore import Qt, QTranslator
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.view.main_window import MainWindow
from app.common.config import Language


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
    galleryTranslator.load(
        os.path.join(os.getcwd(), "app", "resource", "i18n", "i18n.zh_CN.qm")
    )
    print("load chinese simplified")

elif locale == Language.CHINESE_TRADITIONAL:
    galleryTranslator.load(
        os.path.join(os.getcwd(), "app", "resource", "i18n", "i18n.zh_HK.qm")
    )
    print("load chinese traditiona")
elif locale == Language.ENGLISH:
    galleryTranslator.load()
    print("load english")
app.installTranslator(translator)
app.installTranslator(galleryTranslator)

# create main window
w = MainWindow()
w.show()

app.exec()
