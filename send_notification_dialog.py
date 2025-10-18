"""发送通知对话框模块

该模块提供手动发送测试通知的界面。
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                               QPushButton, QMessageBox, QGroupBox, QFormLayout,
                               QSpinBox, QWidget)
from PySide6.QtCore import Qt
from logger_config import logger
from config import load_config
from icon_manager import load_icon
from typing import Optional, Callable, Any


class SendNotificationDialog(QDialog):
    """发送通知对话框"""
    
    def __init__(self, send_callback: Optional[Callable[..., Any]] = None, parent: Optional[QWidget] = None) -> None:
        """初始化发送通知对话框
        
        Args:
            send_callback (callable): 发送通知回调函数
            parent (QWidget, optional): 父级窗口
        """
        super().__init__(parent)
        logger.debug("初始化发送通知对话框")
        
        # 设置窗口属性
        self.setWindowTitle("发送通知")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(400, 300)
        
        # 回调函数
        self.send_callback: Optional[Callable[..., Any]] = send_callback
        
        # 加载配置
        self.config = load_config()
        
        # 设置窗口图标
        self._set_window_icon()
        
        # 创建UI
        self._create_ui()
        
        # 连接信号
        self._connect_signals()
        
        logger.debug("发送通知对话框初始化完成")
        
    def _set_window_icon(self) -> None:
        """设置发送通知对话框窗口图标"""
        try:
            logger.debug("设置发送通知对话框窗口图标")
            
            # 先确保配置已加载
            if not hasattr(self, 'config'):
                self.config = load_config()
                
            # 加载图标
            icon = load_icon(self.config)
            if not icon.isNull():
                self.setWindowIcon(icon)
                logger.debug("发送通知对话框窗口图标设置成功")
            else:
                logger.warning("发送通知对话框窗口图标为空")
        except Exception as e:
            logger.error(f"设置发送通知对话框窗口图标时出错: {e}")
            
    def _create_ui(self) -> None:
        """创建用户界面"""
        try:
            logger.debug("创建发送通知对话框UI")
            
            # 创建主布局
            main_layout = QVBoxLayout(self)
            
            # 创建通知内容组
            content_group = QGroupBox("通知内容")
            content_layout = QVBoxLayout(content_group)
            
            # 通知文本编辑器
            self.text_edit = QTextEdit()
            self.text_edit.setPlaceholderText("请输入要发送的通知内容...")
            self.text_edit.setMaximumHeight(150)
            # 设置为纯文本模式，禁止富文本输入
            self.text_edit.setAcceptRichText(False)
            content_layout.addWidget(self.text_edit)
            
            main_layout.addWidget(content_group)
            
            # 创建设置组
            settings_group = QGroupBox("发送设置")
            settings_layout = QFormLayout(settings_group)
            
            # 滚动次数
            self.scroll_count_spinbox = QSpinBox()
            self.scroll_count_spinbox.setRange(1, 10)
            self.scroll_count_spinbox.setValue(3)
            # 设置滚动次数输入框宽度与之前间隔时间输入框宽度一致
            self.scroll_count_spinbox.setFixedWidth(100)
            settings_layout.addRow("滚动次数:", self.scroll_count_spinbox)
            
            main_layout.addWidget(settings_group)
            
            # 创建按钮布局
            button_layout = QHBoxLayout()
            
            # 添加伸展
            button_layout.addStretch()
            
            # 发送和取消按钮
            send_button = QPushButton("发送")
            send_button.clicked.connect(self._on_send)
            cancel_button = QPushButton("取消")
            cancel_button.clicked.connect(self._on_cancel)
            
            button_layout.addWidget(send_button)
            button_layout.addWidget(cancel_button)
            
            main_layout.addLayout(button_layout)
            
            logger.debug("发送通知对话框UI创建完成")
        except Exception as e:
            logger.error(f"创建发送通知对话框UI时出错: {e}")
            
    def _connect_signals(self) -> None:
        """连接信号"""
        try:
            logger.debug("连接发送通知对话框信号")
        except Exception as e:
            logger.error(f"连接发送通知对话框信号时出错: {e}")
            
    def _on_send(self) -> None:
        """处理发送事件"""
        try:
            logger.debug("处理发送事件")
            
            # 获取通知内容
            message = self.text_edit.toPlainText().strip()
            if not message:
                QMessageBox.warning(self, "警告", "请输入通知内容")
                return
                
            # 获取设置
            scroll_count = self.scroll_count_spinbox.value()  # 获取滚动次数
            
            # 发送通知，传递自定义滚动次数
            if self.send_callback:
                # 只发送一次通知，但设置自定义滚动次数
                self.send_callback(message, skip_restrictions=True, max_scrolls=scroll_count)
                    
            # 直接关闭对话框（移除成功提示）
            self.accept()
            
            logger.debug(f"已发送通知，滚动次数: {scroll_count}")
        except Exception as e:
            logger.error(f"处理发送事件时出错: {e}")
            QMessageBox.critical(self, "错误", f"发送通知时出错: {e}")
            
    def _on_cancel(self) -> None:
        """处理取消事件"""
        try:
            logger.debug("处理取消事件")
            self.reject()
        except Exception as e:
            logger.error(f"处理取消事件时出错: {e}")