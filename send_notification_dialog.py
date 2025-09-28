"""发送通知对话框模块

该模块提供图形界面用于手动发送测试通知。
"""

import sys
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QMessageBox)
from PySide6.QtGui import QAction
from loguru import logger
from icon_manager import load_icon


class SendNotificationDialog(QDialog):
    """手动发送通知对话框 - 允许用户手动发送通知"""
    
    def __init__(self, notification_callback=None, parent=None):
        """初始化发送通知对话框
        
        Args:
            notification_callback (function, optional): 通知回调函数
            parent (QWidget, optional): 父级窗口
        """
        super().__init__(parent)
        self.notification_callback = notification_callback
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("发送通知")
        self.setModal(True)  # 恢复为模态对话框
        
        # 设置窗口图标，与托盘图标一致
        self.setWindowIcon(load_icon("notification_icon.png"))
        
        layout = QVBoxLayout()
        
        # 通知内容输入
        message_layout = QHBoxLayout()
        message_layout.addWidget(QLabel("通知内容："))
        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("请输入要发送的通知内容")
        message_layout.addWidget(self.message_edit)
        layout.addLayout(message_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        send_btn = QPushButton("发送")
        cancel_btn = QPushButton("取消")
        send_btn.clicked.connect(self.send_notification)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(send_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def send_notification(self):
        """发送通知"""
        logger.debug("SendNotificationDialog send_notification方法被调用")
        message = self.message_edit.text().strip()
        logger.debug(f"输入的消息: {message}")
        if message:
            # 将多行文本替换为单行文本，用空格连接
            message = " ".join(message.splitlines())
            # 发送通知
            if self.notification_callback:
                logger.debug(f"调用通知回调函数，消息: {message}")
                self.notification_callback(message)
                logger.debug("通知回调函数调用完成")
            else:
                logger.warning("通知回调函数未设置")
            # 正确关闭对话框
            logger.debug("发送通知完成，调用super().accept()关闭对话框")
            super().accept()  # 使用accept方法关闭对话框
            logger.debug("SendNotificationDialog对话框已关闭")
        else:
            # 如果消息为空，提示用户
            logger.warning("用户输入了空消息")
            QMessageBox.warning(self, "警告", "请输入通知内容")
            
    def closeEvent(self, event):
        """处理对话框关闭事件，防止关闭对话框时影响主程序"""
        logger.debug("SendNotificationDialog closeEvent被调用")
        event.accept()  # 接受关闭事件
        logger.debug("SendNotificationDialog closeEvent执行完成")