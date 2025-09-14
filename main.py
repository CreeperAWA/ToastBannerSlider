import sys
import threading
import winreg
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
from listener import listen_for_notifications, set_notification_callback
from notice_slider import NotificationWindow
from config import load_config, save_config
import os
from loguru import logger

# 配置loguru日志格式
logger.remove()
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
logger.add("toast_banner_slider.log", rotation="10 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="DEBUG")

class ConfigDialog(QDialog):
    """配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("配置设置")
        self.setModal(True)
        
        # 设置窗口图标，与托盘图标一致
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notification_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        layout = QVBoxLayout()
        
        # 通知标题设置
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("通知标题："))
        self.title_edit = QLineEdit()
        self.title_edit.setText(self.config.get("notification_title", "911 呼唤群"))
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # 滚动速度设置
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("滚动速度 (px/s)："))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 50000)
        self.speed_spin.setValue(self.config.get("scroll_speed", 200))
        speed_layout.addWidget(self.speed_spin)
        layout.addLayout(speed_layout)
        
        # 滚动次数设置
        scroll_layout = QHBoxLayout()
        scroll_layout.addWidget(QLabel("滚动次数："))
        self.scroll_spin = QSpinBox()
        self.scroll_spin.setRange(1, 1000)
        self.scroll_spin.setValue(self.config.get("scroll_count", 3))
        scroll_layout.addWidget(self.scroll_spin)
        layout.addLayout(scroll_layout)
        
        # 点击关闭次数设置
        click_layout = QHBoxLayout()
        click_layout.addWidget(QLabel("点击关闭次数："))
        self.click_spin = QSpinBox()
        self.click_spin.setRange(1, 20)
        self.click_spin.setValue(self.config.get("click_to_close", 3))
        click_layout.addWidget(self.click_spin)
        layout.addLayout(click_layout)
        
        # 右侧间隔设置
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("右侧间隔 (px)："))
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 5000)
        self.spacing_spin.setValue(self.config.get("right_spacing", 150))
        spacing_layout.addWidget(self.spacing_spin)
        layout.addLayout(spacing_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        save_btn.clicked.connect(self.save_config)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def save_config(self):
        """保存配置"""
        self.config["notification_title"] = self.title_edit.text()
        self.config["scroll_speed"] = self.speed_spin.value()
        self.config["scroll_count"] = self.scroll_spin.value()
        self.config["click_to_close"] = self.click_spin.value()
        self.config["right_spacing"] = self.spacing_spin.value()
        
        if save_config(self.config):
            self.accept()
        else:
            # 如果保存失败，显示错误或采取其他措施
            pass

class SendNotificationDialog(QDialog):
    """手动发送通知对话框"""
    
    def __init__(self, notification_callback=None, parent=None):
        super().__init__(parent)
        self.notification_callback = notification_callback
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("发送通知")
        self.setModal(True)
        
        # 设置窗口图标，与托盘图标一致
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notification_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
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
        message = self.message_edit.text().strip()
        if message:
            # 发送通知
            if self.notification_callback:
                self.notification_callback(message)
            self.accept()
        else:
            # 如果消息为空，提示用户
            pass

class NotificationListenerThread(QThread):
    """通知监听线程"""
    notification_received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        set_notification_callback(self.notification_received.emit)
    
    def run(self):
        """运行监听器"""
        try:
            # 启动监听器
            listen_for_notifications()
        except Exception as e:
            logger.error(f"监听通知时出错：{e}")

class ToastBannerManager:
    """Toast 横幅通知管理器 - 整合监听和显示功能"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.notification_window = None
        self.listener_thread = None
        self.last_message = None
        self.has_notifications = False
        self.tray_icon = None
        self.config = load_config()
        
    def show_notification(self, message):
        """显示通知横幅"""
        # 保存最后一条消息
        self.last_message = message
        self.has_notifications = True
        
        # 如果已有通知窗口，先关闭它
        if self.notification_window:
            self.notification_window.close()
            
        # 创建并显示新的通知窗口
        self.notification_window = NotificationWindow(message)
        self.notification_window.show()
        
        # 记录日志
        logger.info(f"显示通知：{message}")
        
    def show_last_notification(self):
        """显示最后一条通知"""
        if self.has_notifications and self.last_message:
            # 如果已有通知窗口，先关闭它
            if self.notification_window:
                self.notification_window.close()
                
            # 创建并显示新的通知窗口
            self.notification_window = NotificationWindow(self.last_message)
            self.notification_window.show()
            logger.info(f"显示最后一条通知：{self.last_message}")
        else:
            logger.warning("没有可显示的通知")
    
    def show_send_notification_dialog(self):
        """显示发送通知对话框"""
        dialog = SendNotificationDialog(self.show_notification)
        dialog.exec_()
    
    def show_config_dialog(self):
        """显示配置对话框"""
        old_title = self.config.get("notification_title", "911 呼唤群")
        dialog = ConfigDialog()
        dialog.exec_()
        # 更新配置并刷新托盘图标提示
        self.update_config()
        new_title = self.config.get("notification_title", "911 呼唤群")
        if old_title != new_title:
            logger.info(f"配置已更新，监听标题从 '{old_title}' 更改为 '{new_title}'")
    
    def update_config(self):
        """更新配置并刷新托盘图标提示"""
        self.config = load_config()
        if self.tray_icon:
            target_title = self.config.get("notification_title", "911 呼唤群")
            self.tray_icon.setToolTip(f"正在监听：{target_title}")
    
    def create_tray_icon(self):
        """创建系统托盘图标"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("系统托盘不可用")
            return
            
        # 获取图标文件路径
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notification_icon.png")
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon()
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            logger.warning(f"未找到图标文件：{icon_path}")
            
        # 设置悬停提示
        target_title = self.config.get("notification_title", "911 呼唤群")
        self.tray_icon.setToolTip(f"正在监听：{target_title}")
        logger.info(f"创建系统托盘图标，正在监听：{target_title}")
            
        # 创建托盘菜单
        self.tray_menu = QMenu()
        
        # 显示最后通知动作
        self.show_action = QAction("显示最后通知")
        self.show_action.triggered.connect(self.show_last_notification)
        self.tray_menu.addAction(self.show_action)
        
        # 手动发送通知动作
        self.send_action = QAction("发送通知")
        self.send_action.triggered.connect(self.show_send_notification_dialog)
        self.tray_menu.addAction(self.send_action)
        
        # 配置设置动作
        self.config_action = QAction("配置设置")
        self.config_action.triggered.connect(self.show_config_dialog)
        self.tray_menu.addAction(self.config_action)
        
        # 开机自启动作
        self.startup_action = QAction("开机自启")
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self.is_auto_startup_enabled())
        self.startup_action.triggered.connect(self.toggle_auto_startup)
        self.tray_menu.addAction(self.startup_action)
        
        # 退出动作
        self.quit_action = QAction("退出")
        self.quit_action.triggered.connect(self.quit_application)
        self.tray_menu.addAction(self.quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.icon_activated)
        self.tray_icon.show()
        
    def icon_activated(self, reason):
        """托盘图标被激活"""
        # 只有双击托盘图标才显示最后通知
        # QSystemTrayIcon.DoubleClick 的值为 2
        if reason == 2:
            self.show_last_notification()
        # 单击不执行任何操作
    
    def is_auto_startup_enabled(self):
        """检查是否已设置开机自启"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            winreg.QueryValueEx(key, "ToastBannerSlider")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"检查开机自启设置时出错：{e}")
            return False
    
    def toggle_auto_startup(self, checked):
        """切换开机自启状态"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            
            if checked:
                # 获取当前程序路径
                app_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, "ToastBannerSlider", 0, winreg.REG_SZ, app_path)
                logger.info("已启用开机自启")
            else:
                try:
                    winreg.DeleteValue(key, "ToastBannerSlider")
                    logger.info("已禁用开机自启")
                except FileNotFoundError:
                    pass  # 值不存在，无需删除
                    
            winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"设置开机自启时出错：{e}")
    
    def quit_application(self):
        """退出应用程序"""
        logger.info("正在退出应用程序")
        # 快速退出，不等待线程完全结束
        if self.listener_thread and self.listener_thread.isRunning():
            self.listener_thread.quit()
            # 减少等待时间以提高退出速度
            self.listener_thread.wait(500)  # 只等待 0.5 秒
            logger.info("通知监听线程已停止")
            
        if self.notification_window:
            self.notification_window.close()
            logger.info("通知窗口已关闭")
            
        if self.tray_icon:
            self.tray_icon.hide()
            logger.info("托盘图标已隐藏")
            
        # 直接退出应用
        self.app.quit()
        logger.info("应用程序已退出")
        
    def run(self):
        """运行主程序"""
        # 设置应用程序属性
        self.app.setQuitOnLastWindowClosed(False)
        
        # 创建并启动监听线程
        self.listener_thread = NotificationListenerThread()
        self.listener_thread.notification_received.connect(self.show_notification)
        self.listener_thread.start()
        logger.info("通知监听线程已启动")
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
        # 运行 Qt 事件循环
        logger.info("Toast 横幅通知系统已启动")
        exit_code = self.app.exec_()
        sys.exit(exit_code)

def main():
    print("=" * 30)
    print("Toast 横幅通知系统")
    print("=" * 30)
    print("正在启动...")
    
    manager = ToastBannerManager()
    manager.run()

if __name__ == "__main__":
    main()