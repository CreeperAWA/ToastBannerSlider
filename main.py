"""Toast横幅通知系统主程序

该模块整合了通知监听和显示功能，提供系统托盘图标和用户交互界面。
负责管理整个应用程序的生命周期，包括配置管理、通知监听和显示等核心功能。
"""

import sys
import winreg
import os
import time
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QCheckBox, QDoubleSpinBox
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QObject
from PyQt5.QtGui import QIcon
from listener import listen_for_notifications, set_notification_callback, update_target_title
from notice_slider import NotificationWindow
from config import load_config, save_config, get_config_path
from loguru import logger

# 配置loguru日志格式
logger.remove()
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
logger.add("toast_banner_slider.log", rotation="10 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="DEBUG")


def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容打包后的程序
    
    Args:
        relative_path (str): 相对路径
        
    Returns:
        str: 资源文件的绝对路径
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller打包后的路径
        return os.path.join(sys._MEIPASS, relative_path)
    elif getattr(sys, 'frozen', False):
        # Nuitka打包后的路径
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    else:
        # 开发环境中的路径
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


class ConfigWatcher(QObject):
    """配置文件观察者"""
    config_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.config_path = get_config_path()
        self.last_mtime = self._get_mtime()
        
    def _get_mtime(self):
        """获取配置文件的修改时间"""
        try:
            if os.path.exists(self.config_path):
                return os.path.getmtime(self.config_path)
        except Exception as e:
            logger.warning(f"获取配置文件修改时间时出错：{e}")
        return 0
        
    def check_config_change(self):
        """检查配置文件是否发生变化"""
        current_mtime = self._get_mtime()
        if current_mtime > self.last_mtime:
            self.last_mtime = current_mtime
            self.config_changed.emit()
            return True
        return False


class ConfigDialog(QDialog):
    """配置对话框"""
    
    def __init__(self, parent=None):
        """初始化配置对话框
        
        Args:
            parent (QWidget, optional): 父级窗口
        """
        super().__init__(parent)
        self.config = load_config()
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("配置设置")
        self.setModal(True)
        
        # 设置窗口图标，与托盘图标一致
        icon_path = get_resource_path("notification_icon.png")
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
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(1, 50000)
        self.speed_spin.setValue(self.config.get("scroll_speed", 200.0))
        self.speed_spin.setDecimals(1)
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
        
        # 字体大小设置
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("字体大小 (px)："))
        self.font_size_spin = QDoubleSpinBox()
        self.font_size_spin.setRange(1, 200)
        self.font_size_spin.setValue(self.config.get("font_size", 48.0))
        self.font_size_spin.setDecimals(1)
        font_size_layout.addWidget(self.font_size_spin)
        layout.addLayout(font_size_layout)
        
        # 左边距设置
        left_margin_layout = QHBoxLayout()
        left_margin_layout.addWidget(QLabel("左边距 (px)："))
        self.left_margin_spin = QSpinBox()
        self.left_margin_spin.setRange(0, 5000)
        self.left_margin_spin.setValue(self.config.get("left_margin", 93))
        left_margin_layout.addWidget(self.left_margin_spin)
        layout.addLayout(left_margin_layout)
        
        # 右边距设置
        right_margin_layout = QHBoxLayout()
        right_margin_layout.addWidget(QLabel("右边距 (px)："))
        self.right_margin_spin = QSpinBox()
        self.right_margin_spin.setRange(0, 5000)
        self.right_margin_spin.setValue(self.config.get("right_margin", 93))
        right_margin_layout.addWidget(self.right_margin_spin)
        layout.addLayout(right_margin_layout)
        
        # 图标缩放倍数设置
        icon_scale_layout = QHBoxLayout()
        icon_scale_layout.addWidget(QLabel("图标缩放倍数："))
        self.icon_scale_spin = QDoubleSpinBox()
        self.icon_scale_spin.setRange(0.1, 10)
        self.icon_scale_spin.setValue(self.config.get("icon_scale", 1.0))
        self.icon_scale_spin.setDecimals(1)
        icon_scale_layout.addWidget(self.icon_scale_spin)
        layout.addLayout(icon_scale_layout)
        
        # 标签文本X轴偏移设置
        label_offset_layout = QHBoxLayout()
        label_offset_layout.addWidget(QLabel("标签文本X轴偏移 (px)："))
        self.label_offset_spin = QSpinBox()
        self.label_offset_spin.setRange(-500, 500)
        self.label_offset_spin.setValue(self.config.get("label_offset_x", 0))
        label_offset_layout.addWidget(self.label_offset_spin)
        layout.addLayout(label_offset_layout)
        
        # 窗口高度设置
        window_height_layout = QHBoxLayout()
        window_height_layout.addWidget(QLabel("窗口高度 (px)："))
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(50, 500)
        self.window_height_spin.setValue(self.config.get("window_height", 128))
        window_height_layout.addWidget(self.window_height_spin)
        layout.addLayout(window_height_layout)
        
        # 标签遮罩宽度设置
        label_mask_width_layout = QHBoxLayout()
        label_mask_width_layout.addWidget(QLabel("标签遮罩宽度 (px)："))
        self.label_mask_width_spin = QSpinBox()
        self.label_mask_width_spin.setRange(100, 1000)
        self.label_mask_width_spin.setValue(self.config.get("label_mask_width", 305))
        label_mask_width_layout.addWidget(self.label_mask_width_spin)
        layout.addLayout(label_mask_width_layout)
        
        # 横幅间隔设置
        banner_spacing_layout = QHBoxLayout()
        banner_spacing_layout.addWidget(QLabel("横幅间隔 (px)："))
        self.banner_spacing_spin = QSpinBox()
        self.banner_spacing_spin.setRange(0, 100)
        self.banner_spacing_spin.setValue(self.config.get("banner_spacing", 10))
        banner_spacing_layout.addWidget(self.banner_spacing_spin)
        layout.addLayout(banner_spacing_layout)
        
        # 上移动画持续时间设置
        shift_animation_layout = QHBoxLayout()
        shift_animation_layout.addWidget(QLabel("上移动画时间 (ms)："))
        self.shift_animation_spin = QSpinBox()
        self.shift_animation_spin.setRange(50, 1000)
        self.shift_animation_spin.setValue(self.config.get("shift_animation_duration", 100))
        shift_animation_layout.addWidget(self.shift_animation_spin)
        layout.addLayout(shift_animation_layout)
        
        # 忽略重复通知设置
        ignore_duplicate_layout = QHBoxLayout()
        ignore_duplicate_layout.addWidget(QLabel("忽略重复通知："))
        self.ignore_duplicate_checkbox = QCheckBox("启用")
        self.ignore_duplicate_checkbox.setChecked(self.config.get("ignore_duplicate", False))
        ignore_duplicate_layout.addWidget(self.ignore_duplicate_checkbox)
        layout.addLayout(ignore_duplicate_layout)
        
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
        self.config["font_size"] = self.font_size_spin.value()
        self.config["left_margin"] = self.left_margin_spin.value()
        self.config["right_margin"] = self.right_margin_spin.value()
        self.config["icon_scale"] = self.icon_scale_spin.value()
        self.config["label_offset_x"] = self.label_offset_spin.value()
        self.config["window_height"] = self.window_height_spin.value()
        self.config["label_mask_width"] = self.label_mask_width_spin.value()
        self.config["banner_spacing"] = self.banner_spacing_spin.value()
        self.config["shift_animation_duration"] = self.shift_animation_spin.value()
        self.config["ignore_duplicate"] = self.ignore_duplicate_checkbox.isChecked()
        
        if save_config(self.config):
            self.accept()
        else:
            # 如果保存失败，显示错误或采取其他措施
            pass


class SendNotificationDialog(QDialog):
    """手动发送通知对话框"""
    
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
        self.setModal(True)
        
        # 设置窗口图标，与托盘图标一致
        icon_path = get_resource_path("notification_icon.png")
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
            # 将多行文本替换为单行文本，用空格连接
            message = " ".join(message.splitlines())
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
        """初始化通知监听线程"""
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
        """初始化Toast横幅通知管理器"""
        # 确保应用程序有一个唯一的标识符
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
            
        # 设置应用程序属性
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("ToastBannerSlider")
        self.app.setApplicationDisplayName("Toast Banner Slider")
        
        self.notification_windows = []  # 用于存储多个通知窗口
        self.listener_thread = None
        self.message_history = []  # 存储消息历史记录（消息内容和时间戳）
        self.has_notifications = False
        self.tray_icon = None
        self.config = load_config()
        
        # 用于延时创建托盘图标的定时器
        self.tray_timer = None
        
        # 配置观察者
        self.config_watcher = ConfigWatcher()
        self.config_watcher.config_changed.connect(self.update_config)
        
        # 添加配置文件监控定时器
        self.config_check_timer = QTimer()
        self.config_check_timer.timeout.connect(self.config_watcher.check_config_change)
        self.config_check_timer.start(1000)  # 每秒检查一次配置更新
        
    def show_notification(self, message):
        """显示通知横幅
        
        Args:
            message (str): 要显示的通知消息
        """
        # 保存消息到历史记录
        current_time = time.time()
        self.message_history.append((message, current_time))
        
        # 清理5分钟前的历史记录
        self.cleanup_message_history()
        
        self.has_notifications = True
        
        # 检查是否启用了免打扰模式
        if self.config.get("do_not_disturb", False):
            logger.info(f"免打扰模式已启用，通知被拦截：{message}")
            return
            
        # 检查是否启用了忽略重复通知（5分钟内）
        if self.config.get("ignore_duplicate", False):
            # 检查是否在5分钟内有相同消息
            if self.is_duplicate_message(message, current_time):
                logger.info(f"忽略5分钟内的重复通知：{message}")
                return
        
        # 计算新窗口的垂直位置
        base_height = self.config.get("window_height", 128)
        banner_spacing = self.config.get("banner_spacing", 10)
        
        # 计算已有窗口的总高度和间隔数
        total_existing_height = len(self.notification_windows) * base_height
        total_spacing = len(self.notification_windows) * banner_spacing
        
        # 创建并显示新的通知窗口
        window = NotificationWindow(message, vertical_offset=total_existing_height + total_spacing)
        window.show()
        self.notification_windows.append(window)
        
        # 连接窗口关闭信号，以便从列表中移除
        window.window_closed.connect(self.remove_notification_window)
        
        # 记录日志
        logger.info(f"显示通知：{message}")
        
    def cleanup_message_history(self):
        """清理5分钟前的消息历史记录"""
        current_time = time.time()
        # 保留5分钟内的消息记录
        self.message_history = [
            (msg, timestamp) for msg, timestamp in self.message_history
            if (current_time - timestamp) <= 300
        ]
        
    def is_duplicate_message(self, message, current_time):
        """检查是否为5分钟内的重复消息
        
        Args:
            message (str): 要检查的消息
            current_time (float): 当前时间戳
            
        Returns:
            bool: 如果是5分钟内的重复消息返回True，否则返回False
        """
        # 检查历史记录中是否有相同的消息
        for msg, timestamp in self.message_history[:-1]:  # 不包括当前消息
            if (current_time - timestamp) <= 300 and msg == message:
                return True
        return False
        
    def remove_notification_window(self, window):
        """从通知窗口列表中移除已关闭的窗口，并更新其他窗口的位置
        
        Args:
            window (NotificationWindow): 已关闭的通知窗口
        """
        if window in self.notification_windows:
            self.notification_windows.remove(window)
            
            # 更新剩余窗口的位置
            base_height = self.config.get("window_height", 128)
            banner_spacing = self.config.get("banner_spacing", 10)
            animation_duration = self.config.get("shift_animation_duration", 100)
            
            for i, win in enumerate(self.notification_windows):
                total_existing_height = i * base_height
                total_spacing = i * banner_spacing
                win.update_vertical_offset(total_existing_height + total_spacing, animation_duration)
        
    def show_last_notification(self):
        """显示最后一条通知"""
        if not self.message_history:
            logger.warning("没有可显示的通知")
            return
            
        # 获取最后一条消息
        last_message, _ = self.message_history[-1] if self.message_history else ("", 0)
        
        if self.has_notifications and last_message:
            # 检查是否启用了免打扰模式
            if self.config.get("do_not_disturb", False):
                logger.info("免打扰模式已启用，无法显示最后通知")
                return
                
            # 创建并显示新的通知窗口
            window = NotificationWindow(last_message)
            window.show()
            self.notification_windows.append(window)
            
            # 连接窗口关闭信号，以便从列表中移除
            window.window_closed.connect(self.remove_notification_window)
            
            logger.info(f"显示最后一条通知：{last_message}")
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
            # 通知监听器更新监听标题
            update_target_title(new_title)
    
    def update_config(self):
        """更新配置并刷新托盘图标提示"""
        logger.info("检测到配置文件更新，重新加载配置")
        self.config = load_config()
        if self.tray_icon:
            target_title = self.config.get("notification_title", "911 呼唤群")
            self.tray_icon.setToolTip(f"正在监听：{target_title}")
            
            # 更新免打扰菜单项状态
            if hasattr(self, 'dnd_action'):
                self.dnd_action.setChecked(self.config.get("do_not_disturb", False))
    
    def _load_icon(self, icon_name="notification_icon.png"):
        """加载图标资源
        
        Args:
            icon_name (str): 图标文件名
            
        Returns:
            QIcon: 加载的图标对象，加载失败返回None
        """
        icon_path = get_resource_path(icon_name)
        logger.debug(f"尝试加载图标：{icon_name}，路径：{icon_path}")
        
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                return icon
            logger.warning(f"图标文件无效：{icon_path}")
        
        # 如果指定图标加载失败，尝试加载默认图标
        default_icon_path = get_resource_path("default_icon.png")
        if os.path.exists(default_icon_path):
            default_icon = QIcon(default_icon_path)
            if not default_icon.isNull():
                logger.info(f"使用默认图标替代：{default_icon_path}")
                return default_icon
        
        logger.error("无法加载任何图标资源")
        return QIcon()  # 返回空图标

    def create_tray_icon(self):
        """创建系统托盘图标
        
        Returns:
            bool: 创建成功返回True，否则返回False
        """
        # 检查系统托盘是否可用
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("系统托盘不可用")
            return False
            
        # 获取图标文件路径
        icon_path = get_resource_path("notification_icon.png")
        
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
        
        # 免打扰模式开关
        self.dnd_action = QAction("免打扰")
        self.dnd_action.setCheckable(True)
        self.dnd_action.setChecked(self.config.get("do_not_disturb", False))
        self.dnd_action.triggered.connect(self.toggle_do_not_disturb)
        self.tray_menu.addAction(self.dnd_action)
        
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
        
        # 显示托盘图标
        self.tray_icon.show()
        
        # 检查托盘图标是否成功显示
        if self.tray_icon.isVisible():
            logger.info("系统托盘图标已成功显示")
            return True
        else:
            logger.error("系统托盘图标显示失败")
            return False
            
    def toggle_do_not_disturb(self, checked):
        """切换免打扰模式
        
        Args:
            checked (bool): 是否启用免打扰模式
        """
        # 更新配置
        self.config["do_not_disturb"] = checked
        save_config(self.config)
        logger.info(f"免打扰模式已{'启用' if checked else '禁用'}")
        
    def icon_activated(self, reason):
        """托盘图标被激活
        
        Args:
            reason (QSystemTrayIcon.ActivationReason): 激活原因
        """
        # 只有双击托盘图标才显示最后通知
        # QSystemTrayIcon.DoubleClick 的值为 2
        if reason == 2:  # 使用数值而不是属性以避免类型检查问题
            self.show_last_notification()
        # 单击不执行任何操作
    
    def is_auto_startup_enabled(self):
        """检查是否已设置开机自启
        
        Returns:
            bool: 已设置开机自启返回True，否则返回False
        """
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
        """切换开机自启状态
        
        Args:
            checked (bool): 是否启用开机自启
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            
            if checked:
                # 获取当前程序路径，使用与config.py相同的路径获取方式
                # 确保在Nuitka打包后也能正确获取程序位置
                if getattr(sys, 'frozen', False):
                    # 打包后的程序，使用可执行文件所在目录
                    app_path = sys.argv[0]
                else:
                    # 开发环境，使用脚本所在目录
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
            
        # 关闭所有通知窗口
        for window in self.notification_windows[:]:  # 使用副本避免在迭代时修改列表
            try:
                window.close()
            except Exception as e:
                logger.warning(f"关闭通知窗口时出错：{e}")
        logger.info(f"已关闭 {len(self.notification_windows)} 个通知窗口")
        
        # 清空通知窗口列表
        self.notification_windows.clear()
            
        if self.tray_icon:
            self.tray_icon.hide()
            logger.info("托盘图标已隐藏")
            
        # 停止配置检查定时器
        if self.config_check_timer:
            self.config_check_timer.stop()
            logger.info("配置检查定时器已停止")
            
        # 退出应用程序
        self.app.quit()
        logger.info("应用程序已退出")

    def run(self):
        """运行主程序"""
        # 创建并启动监听线程
        self.listener_thread = NotificationListenerThread()
        self.listener_thread.notification_received.connect(self.show_notification)
        self.listener_thread.start()
        logger.info("通知监听线程已启动")
        
        # 延迟创建系统托盘图标，确保GUI完全初始化
        QTimer.singleShot(1000, self._delayed_create_tray_icon)
        
        # 运行 Qt 事件循环
        logger.info("Toast 横幅通知系统已启动")
        exit_code = self.app.exec_()
        sys.exit(exit_code)
        
    def _delayed_create_tray_icon(self):
        """延时创建系统托盘图标"""
        # 创建系统托盘图标
        if not self.create_tray_icon():
            logger.error("无法创建系统托盘图标，程序将退出")
            self.app.quit()


def main():
    """主函数 - 程序入口点"""
    print("=" * 30)
    print("Toast 横幅通知系统")
    print("=" * 30)
    print("正在启动...")
    
    # 确保即使在无控制台模式下也能正确创建 QApplication
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    
    # 设置应用程序属性
    app.setQuitOnLastWindowClosed(False)
    
    manager = ToastBannerManager()
    manager.run()


if __name__ == "__main__":
    main()