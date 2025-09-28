"""通知监听器模块

该模块负责监听Windows系统通知并处理相关事件。
"""

from PySide6.QtCore import QThread, Signal
from listener import listen_for_notifications, set_notification_callback
from loguru import logger


class NotificationListenerThread(QThread):
    """通知监听线程 - 在后台监听Windows通知数据库"""
    notification_received = Signal(str)
    
    def __init__(self):
        """初始化通知监听线程"""
        super().__init__()
        self._running = True
        set_notification_callback(self.notification_received.emit)
    
    def run(self):
        """运行监听器 - 启动通知监听循环"""
        try:
            # 启动监听器并传递停止检查函数
            listen_for_notifications(stop_check=lambda: not self._running)
        except Exception as e:
            if self._running:
                logger.error(f"监听通知时出错：{e}")
    
    def stop(self):
        """停止线程"""
        if self._running:
            self._running = False
            self.quit()  # 请求线程事件循环退出
    
    def is_running(self):
        """检查线程是否正在运行"""
        return self._running