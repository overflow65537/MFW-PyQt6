
import traceback
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIcon
from app.utils.logger import logger


def show_error_message():
    logger.exception("发生了一个异常：")
    traceback_info = traceback.format_exc()
    
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)  
    msg_box.setWindowTitle("错误")
    msg_box.setText(f"发生了一个异常：\n{str(traceback_info)}") 

 
    msg_box.setWindowIcon(QIcon("./icon/ERROR.png"))  

    msg_box.exec() 
