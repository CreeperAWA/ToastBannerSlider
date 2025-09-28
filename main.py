"""Toast横幅通知系统主程序

该模块整合了通知监听和显示功能，提供系统托盘图标和用户交互界面。
负责管理整个应用程序的生命周期，包括配置管理、通知监听和显示等核心功能。
"""

import sys
import os
import time
from win32com.client import Dispatch
from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, 
                           QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                           QPushButton, QSpinBox, QCheckBox, QDoubleSpinBox, QMessageBox,
                           QComboBox)
from PySide6.QtGui import QAction
from PySide6.QtCore import QThread, Signal, QTimer, QObject, Qt
from listener import listen_for_notifications, set_notification_callback, update_target_title, get_listener
from notice_slider import NotificationWindow
from config import load_config, save_config, get_config_path
from icon_manager import load_icon
from loguru import logger

# 配置loguru日志格式
logger.remove()
# 初始化日志设置
from config import load_config, save_config, get_config_path, setup_logger
config = load_config()
log_level = setup_logger(config)
if log_level is None:
    log_level = "INFO"  # 设置默认日志级别
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level=log_level)
logger.add("toast_banner_slider.log", rotation="5 MB", 
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level=log_level)


class ConfigWatcher(QObject):
    """配置文件观察者 - 监听配置文件变化并发出信号"""
    config_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self.config_path = get_config_path()
        self.last_mtime = self._get_mtime()
        
    def _get_mtime(self):
        """获取配置文件的修改时间
        
        Returns:
            float: 配置文件的修改时间戳，出错时返回0
        """
        try:
            if os.path.exists(self.config_path):
                return os.path.getmtime(self.config_path)
        except Exception as e:
            logger.warning(f"获取配置文件修改时间时出错：{e}")
        return 0
        
    def check_config_change(self):
        """检查配置文件是否发生变化，如果变化则发出信号"""
        current_mtime = self._get_mtime()
        if current_mtime > self.last_mtime:
            self.last_mtime = current_mtime
            self.config_changed.emit()


class ConfigDialog(QDialog):
    """配置对话框 - 允许用户修改应用程序配置"""
    
    def __init__(self, parent=None):
        """初始化配置对话框
        
        Args:
            parent (QWidget, optional): 父级窗口
        """
        super().__init__(parent)
        # 加载配置用于界面显示
        self.config = load_config()
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("配置设置")
        self.setModal(True)  # 恢复为模态对话框
        
        # 设置窗口图标，与托盘图标一致
        self.setWindowIcon(load_icon("notification_icon.png"))
        
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
        self.speed_spin.setRange(1, 2000)
        self.speed_spin.setValue(self.config.get("scroll_speed", 200))
        speed_layout.addWidget(self.speed_spin)
        layout.addLayout(speed_layout)
        
        # 滚动次数设置
        scroll_layout = QHBoxLayout()
        scroll_layout.addWidget(QLabel("滚动次数："))
        self.scroll_spin = QSpinBox()
        self.scroll_spin.setRange(0, 20)
        self.scroll_spin.setValue(self.config.get("scroll_count", 3))
        scroll_layout.addWidget(self.scroll_spin)
        layout.addLayout(scroll_layout)
        
        # 点击关闭次数设置
        click_layout = QHBoxLayout()
        click_layout.addWidget(QLabel("点击关闭次数："))
        self.click_spin = QSpinBox()
        self.click_spin.setRange(1, 10)
        self.click_spin.setValue(self.config.get("click_to_close", 3))
        click_layout.addWidget(self.click_spin)
        layout.addLayout(click_layout)
        
        # 右侧间隔距离设置
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("右侧间隔距离 (px)："))
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 1000)
        self.spacing_spin.setValue(self.config.get("right_spacing", 150))
        spacing_layout.addWidget(self.spacing_spin)
        layout.addLayout(spacing_layout)
        
        # 字体大小设置
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体大小 (px)："))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 100)
        self.font_spin.setValue(self.config.get("font_size", 48))
        font_layout.addWidget(self.font_spin)
        layout.addLayout(font_layout)
        
        # 左边距设置
        left_margin_layout = QHBoxLayout()
        left_margin_layout.addWidget(QLabel("左侧边距 (px)："))
        self.left_margin_spin = QSpinBox()
        self.left_margin_spin.setRange(0, 500)
        self.left_margin_spin.setValue(self.config.get("left_margin", 93))
        left_margin_layout.addWidget(self.left_margin_spin)
        layout.addLayout(left_margin_layout)
        
        # 右边距设置
        right_margin_layout = QHBoxLayout()
        right_margin_layout.addWidget(QLabel("右侧边距 (px)："))
        self.right_margin_spin = QSpinBox()
        self.right_margin_spin.setRange(0, 500)
        self.right_margin_spin.setValue(self.config.get("right_margin", 93))
        right_margin_layout.addWidget(self.right_margin_spin)
        layout.addLayout(right_margin_layout)
        
        # 图标缩放设置
        icon_scale_layout = QHBoxLayout()
        icon_scale_layout.addWidget(QLabel("图标缩放倍数："))
        self.icon_scale_spin = QDoubleSpinBox()
        self.icon_scale_spin.setRange(0.1, 5.0)
        self.icon_scale_spin.setSingleStep(0.1)
        self.icon_scale_spin.setValue(self.config.get("icon_scale", 1.0))
        self.icon_scale_spin.setDecimals(2)
        icon_scale_layout.addWidget(self.icon_scale_spin)
        layout.addLayout(icon_scale_layout)
        
        # 标签偏移设置
        label_offset_layout = QHBoxLayout()
        label_offset_layout.addWidget(QLabel("标签文本x轴偏移 (px)："))
        self.label_offset_spin = QSpinBox()
        self.label_offset_spin.setRange(-500, 500)
        self.label_offset_spin.setValue(self.config.get("label_offset_x", 0))
        label_offset_layout.addWidget(self.label_offset_spin)
        layout.addLayout(label_offset_layout)
        
        # 窗口高度设置
        window_height_layout = QHBoxLayout()
        window_height_layout.addWidget(QLabel("窗口高度 (px)："))
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(20, 500)
        self.window_height_spin.setValue(self.config.get("window_height", 128))
        window_height_layout.addWidget(self.window_height_spin)
        layout.addLayout(window_height_layout)
        
        # 标签遮罩宽度设置
        mask_width_layout = QHBoxLayout()
        mask_width_layout.addWidget(QLabel("标签遮罩宽度 (px)："))
        self.mask_width_spin = QSpinBox()
        self.mask_width_spin.setRange(0, 1000)
        self.mask_width_spin.setValue(self.config.get("label_mask_width", 305))
        mask_width_layout.addWidget(self.mask_width_spin)
        layout.addLayout(mask_width_layout)
        
        # 横幅间隔设置
        banner_spacing_layout = QHBoxLayout()
        banner_spacing_layout.addWidget(QLabel("横幅间隔 (px)："))
        self.banner_spacing_spin = QSpinBox()
        self.banner_spacing_spin.setRange(0, 100)
        self.banner_spacing_spin.setValue(self.config.get("banner_spacing", 10))
        banner_spacing_layout.addWidget(self.banner_spacing_spin)
        layout.addLayout(banner_spacing_layout)
        
        # 上移动画持续时间设置
        shift_duration_layout = QHBoxLayout()
        shift_duration_layout.addWidget(QLabel("上移动画持续时间 (ms)："))
        self.shift_duration_spin = QSpinBox()
        self.shift_duration_spin.setRange(0, 5000)
        self.shift_duration_spin.setValue(self.config.get("shift_animation_duration", 100))
        shift_duration_layout.addWidget(self.shift_duration_spin)
        layout.addLayout(shift_duration_layout)
        
        # 淡入淡出动画时间设置
        fade_duration_layout = QHBoxLayout()
        fade_duration_layout.addWidget(QLabel("淡入淡出动画时间 (ms)："))
        self.fade_duration_spin = QSpinBox()
        self.fade_duration_spin.setRange(100, 10000)
        self.fade_duration_spin.setValue(self.config.get("fade_animation_duration", 1500))
        fade_duration_layout.addWidget(self.fade_duration_spin)
        layout.addLayout(fade_duration_layout)
        
        # 基础垂直偏移设置
        base_vertical_offset_layout = QHBoxLayout()
        base_vertical_offset_layout.addWidget(QLabel("基础垂直偏移 (px)："))
        self.base_vertical_offset_spin = QSpinBox()
        self.base_vertical_offset_spin.setRange(0, 1000)
        self.base_vertical_offset_spin.setValue(self.config.get("base_vertical_offset", 0))
        base_vertical_offset_layout.addWidget(self.base_vertical_offset_spin)
        layout.addLayout(base_vertical_offset_layout)
        
        # 滚动模式
        scroll_mode_layout = QHBoxLayout()
        scroll_mode_layout.addWidget(QLabel("滚动模式："))
        self.scroll_mode_combo = QComboBox()
        self.scroll_mode_combo.addItem("不论如何都滚动", "always")
        self.scroll_mode_combo.addItem("可以展示完全的不滚动", "auto")
        current_scroll_mode = self.config.get("scroll_mode", "always")
        index = self.scroll_mode_combo.findData(current_scroll_mode)
        if index >= 0:
            self.scroll_mode_combo.setCurrentIndex(index)
        scroll_mode_layout.addWidget(self.scroll_mode_combo)
        layout.addLayout(scroll_mode_layout)
        
        # 日志等级设置
        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(QLabel("日志等级："))
        self.log_level_combo = QComboBox()
        log_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
        self.log_level_combo.addItems(log_levels)
        current_log_level = self.config.get("log_level", "INFO")
        index = self.log_level_combo.findText(current_log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        log_level_layout.addWidget(self.log_level_combo)
        layout.addLayout(log_level_layout)
        
        # 忽略重复通知设置
        self.ignore_duplicate_checkbox = QCheckBox("忽略重复通知")
        self.ignore_duplicate_checkbox.setChecked(self.config.get("ignore_duplicate", False))
        layout.addWidget(self.ignore_duplicate_checkbox)
        
        # 免打扰模式
        self.do_not_disturb_checkbox = QCheckBox("免打扰模式")
        self.do_not_disturb_checkbox.setChecked(self.config.get("do_not_disturb", False))
        layout.addWidget(self.do_not_disturb_checkbox)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        self.apply_button = QPushButton("应用")
        
        # 连接按钮信号
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self.apply_config)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def accept(self):
        """接受对话框（点击确定按钮）"""
        logger.debug("ConfigDialog accept方法被调用")
        self.apply_config()
        logger.debug("配置已应用，调用super().accept()")
        super().accept()  # 使用标准的accept方法关闭对话框
        logger.debug("ConfigDialog accept方法执行完成")

    def reject(self):
        """拒绝对话框（点击取消按钮或关闭按钮）"""
        logger.debug("ConfigDialog reject方法被调用")
        logger.debug("用户取消配置更改，不保存任何配置")
        logger.debug("调用super().reject()")
        super().reject()  # 使用标准的reject方法关闭对话框
        logger.debug("ConfigDialog reject方法执行完成")
        
    def closeEvent(self, event):
        """处理对话框关闭事件，防止关闭对话框时影响主程序"""
        logger.debug("ConfigDialog closeEvent被调用")
        # 点击关闭按钮时，不保存配置，直接拒绝对话框
        self.reject()
        event.accept()  # 接受关闭事件
        logger.debug("ConfigDialog closeEvent执行完成")

    def apply_config(self):
        """应用配置更改"""
        # 构建新的配置字典
        new_config = {
            "notification_title": self.title_edit.text(),
            "scroll_speed": self.speed_spin.value(),
            "scroll_count": self.scroll_spin.value(),
            "click_to_close": self.click_spin.value(),
            "right_spacing": self.spacing_spin.value(),
            "font_size": self.font_spin.value(),
            "left_margin": self.left_margin_spin.value(),
            "right_margin": self.right_margin_spin.value(),
            "icon_scale": self.icon_scale_spin.value(),
            "label_offset_x": self.label_offset_spin.value(),
            "window_height": self.window_height_spin.value(),
            "label_mask_width": self.mask_width_spin.value(),
            "banner_spacing": self.banner_spacing_spin.value(),
            "shift_animation_duration": self.shift_duration_spin.value(),
            "ignore_duplicate": self.ignore_duplicate_checkbox.isChecked(),
            "do_not_disturb": self.do_not_disturb_checkbox.isChecked(),
            "scroll_mode": self.scroll_mode_combo.currentData(),  # 添加滚动模式配置
            "fade_animation_duration": self.fade_duration_spin.value(),  # 添加淡入淡出动画时间配置
            "base_vertical_offset": self.base_vertical_offset_spin.value(),  # 添加基础垂直偏移配置
            "log_level": self.log_level_combo.currentText()  # 添加日志等级配置
        }
        
        # 只有配置发生变化时才保存
        if new_config != self.config:
            # 保存配置
            save_config(new_config)
            logger.info("配置已保存")
            
            # 更新内部配置
            self.config = new_config
            
            # 更新监听器的目标标题
            listener = get_listener()
            if listener:
                listener.set_target_title(new_config["notification_title"])
                
            # 更新日志等级
            log_level = new_config.get("log_level", "INFO")
            if log_level:
                logger.remove()
                logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level=log_level)
                logger.add("toast_banner_slider.log", rotation="5 MB", 
                          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level=log_level)
        else:
            logger.debug("配置未发生变化，无需保存")


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


class ToastBannerManager(QObject):
    """Toast横幅通知管理器 - 控制整个应用程序的生命周期和核心功能"""
    
    def __init__(self, parent=None):
        """初始化Toast横幅管理器"""
        super().__init__(parent)
        logger.info("正在启动Toast横幅通知系统...")
        
        # 创建Qt应用程序实例
        self.app = QApplication.instance() or QApplication(sys.argv)
        
        # 初始化成员变量
        self.tray_icon = None
        self.notification_windows = []  # 存储当前显示的通知窗口
        self.last_notification = None   # 存储最后一条通知内容
        self.config_watcher = None
        self.config_timer = None
        self.listener_thread = None
        self._send_dialog = None  # 用于保持发送通知对话框的引用
        
        # 初始化UI
        self.init_ui()
        
        logger.info("Toast横幅通知系统初始化完成")
        
    def init_ui(self):
        """初始化用户界面"""
        # 初始化消息历史记录和通知状态
        self.message_history = []
        self.has_notifications = False
        
        # 创建并启动配置文件观察者
        self.config_watcher = ConfigWatcher()
        self.config_timer = QTimer()
        self.config_timer.timeout.connect(self.config_watcher.check_config_change)
        self.config_timer.start(1000)  # 每秒检查一次配置文件变化
        self.config_watcher.config_changed.connect(self.update_config)
        
        # 启动通知监听线程
        self.listener_thread = NotificationListenerThread()
        self.listener_thread.notification_received.connect(self.show_notification)
        self.listener_thread.start()
        
        # 延迟创建托盘图标，确保GUI环境完全初始化
        QTimer.singleShot(1000, self._delayed_create_tray_icon)  # 减少延迟时间
        
        # 加载初始配置
        self.config = load_config()
        
        logger.info("主程序UI初始化完成")
        
    def show_notification(self, message, skip_duplicate_check=False):
        """显示通知横幅
        
        Args:
            message (str): 要显示的通知消息
            skip_duplicate_check (bool): 是否跳过重复消息检查，默认为False
        """
        logger.debug(f"show_notification 开始处理消息: {message}")
        
        try:
            # 保存最后一条通知
            self.last_notification = message
            logger.debug("已保存最后一条通知")
            
            if not hasattr(self, 'message_history'):
                self.message_history = []
            if not hasattr(self, 'has_notifications'):
                self.has_notifications = False
                
            # 保存消息到历史记录
            current_time = time.time()
            self.message_history.append((message, current_time))
            logger.debug("消息已添加到历史记录")
            
            # 清理5分钟前的历史记录
            self.cleanup_message_history()
            
            # 检查是否启用了免打扰模式
            if self.config.get("do_not_disturb", False):
                logger.info("免打扰模式已启用，忽略通知")
                return
                
            # 检查是否启用了忽略重复通知（5分钟内）
            # 如果skip_duplicate_check为True，则跳过重复消息检查
            if not skip_duplicate_check and self.config.get("ignore_duplicate", False):
                # 检查是否在5分钟内有相同消息
                if self.is_duplicate_message(message, current_time):
                    logger.info(f"忽略5分钟内的重复通知：{message}")
                    return
            
            # 加载配置
            logger.debug("加载配置")
            self.config = load_config()
            
            # 计算新窗口的垂直位置
            logger.debug("计算窗口位置参数")
            base_height = self.config.get("window_height", 128)
            banner_spacing = self.config.get("banner_spacing", 10)
            
            # 计算已有窗口的总高度和间隔数
            total_existing_height = len(self.notification_windows) * base_height
            total_spacing = len(self.notification_windows) * banner_spacing
            
            # 创建并显示新的通知窗口
            logger.debug("创建NotificationWindow实例")
            window = NotificationWindow(message, vertical_offset=total_existing_height + total_spacing)
            logger.debug("NotificationWindow实例创建完成")
            
            # 防止程序因最后一个窗口关闭而退出
            self.app.setQuitOnLastWindowClosed(False)
            
            logger.debug("显示窗口")
            window.show()
            logger.debug("窗口显示完成")
            
            logger.debug("将窗口添加到通知窗口列表")
            self.notification_windows.append(window)
            
            logger.debug("连接窗口关闭信号")
            # 连接窗口关闭信号，以便从列表中移除
            window.window_closed.connect(self.remove_notification_window)
            
            # 记录日志
            logger.info(f"显示通知：{message}")
        except Exception as e:
            logger.error(f"显示通知时出错：{e}", exc_info=True)
        
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
            window (NotificationWindow): 要移除的通知窗口
        """
        if window in self.notification_windows:
            # 从列表中移除窗口
            self.notification_windows.remove(window)
            logger.debug(f"通知窗口已移除，剩余窗口数：{len(self.notification_windows)}")
            
            # 更新其他窗口的位置
            self.update_window_positions()
            
    def update_window_positions(self):
        """更新所有通知窗口的位置"""
        # 加载配置
        config = load_config()
        base_height = config.get("window_height", 128)
        banner_spacing = config.get("banner_spacing", 10)
        
        # 更新每个窗口的垂直位置
        for i, window in enumerate(self.notification_windows):
            new_offset = i * (base_height + banner_spacing)
            window.update_vertical_offset(new_offset)
        
    def show_last_notification(self):
        """显示最后一条通知，将其添加到现有通知队列中"""
        # 检查是否有历史消息
        if not hasattr(self, 'message_history') or not self.message_history:
            logger.warning("没有可显示的通知")
            return
            
        # 获取最后一条消息
        last_message, _ = self.message_history[-1] if self.message_history else ("", 0)
        
        # 检查是否有有效的最后消息
        if last_message:
            # 检查是否启用了免打扰模式
            if self.config.get("do_not_disturb", False):
                logger.info("免打扰模式已启用，无法显示最后通知")
                return
                
            # 将最后一条消息作为新通知显示，添加到现有通知队列中
            # 传递skip_duplicate_check=True参数以跳过重复消息检查
            self.show_notification(last_message, skip_duplicate_check=True)
        else:
            logger.warning("没有可显示的通知")
    
    def show_send_notification_dialog(self):
        """显示发送通知对话框"""
        logger.debug("准备显示发送通知对话框")
        # 确保不会因为对话框关闭而退出主程序
        self.app.setQuitOnLastWindowClosed(False)
        dialog = SendNotificationDialog(self.show_notification)
        logger.debug("SendNotificationDialog实例已创建")
        try:
            logger.debug("尝试显示对话框")
            result = dialog.exec()  # 使用exec()显示模态对话框
            logger.debug(f"对话框已关闭，返回值: {result}")
        except AttributeError:
            # 兼容旧版本PySide/PyQt
            logger.debug("使用旧版本exec_方法显示对话框")
            result = dialog.exec_()
            logger.debug(f"对话框已关闭，返回值: {result}")
        except Exception as e:
            logger.error(f"显示发送通知对话框时出错: {e}")
    
    def show_config_dialog(self):
        """显示配置对话框"""
        logger.debug("准备显示配置对话框")
        # 确保不会因为对话框关闭而退出主程序
        self.app.setQuitOnLastWindowClosed(False)
        old_title = self.config.get("notification_title", "911 呼唤群")
        dialog = ConfigDialog()
        logger.debug("ConfigDialog实例已创建")
        try:
            logger.debug("尝试显示配置对话框")
            result = dialog.exec()  # 使用exec()显示模态对话框
            logger.debug(f"配置对话框已关闭，返回值: {result}")
        except AttributeError:
            # 兼容旧版本PySide/PyQt
            logger.debug("使用旧版本exec_方法显示配置对话框")
            result = dialog.exec_()
            logger.debug(f"配置对话框已关闭，返回值: {result}")
        except Exception as e:
            logger.error(f"显示配置对话框时出错: {e}")
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
        new_config = load_config()
        # 只有在配置真正变化时才更新
        if not hasattr(self, 'config') or new_config != self.config:
            self.config = new_config
            if self.tray_icon:
                target_title = self.config.get("notification_title", "911 呼唤群")
                self.tray_icon.setToolTip(f"正在监听：{target_title}")
                
                # 更新免打扰菜单项状态
                if hasattr(self, 'dnd_action'):
                    self.dnd_action.setChecked(self.config.get("do_not_disturb", False))
    
    def create_tray_icon(self):
        """创建系统托盘图标
        
        Returns:
            bool: 创建成功返回True，否则返回False
        """
        # 检查系统托盘是否可用
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("系统托盘不可用")
            return False
            
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 创建菜单项
        self.show_action = QAction("显示最后通知(&L)")
        self.send_action = QAction("发送通知(&S)")
        self.config_action = QAction("配置设置(&C)")
        
        # 免打扰模式开关
        self.dnd_action = QAction("免打扰(&D)")
        self.dnd_action.setCheckable(True)
        self.dnd_action.setChecked(self.config.get("do_not_disturb", False))
        
        # 开机自启动作
        self.startup_action = QAction("开机自启(&A)")
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self.is_auto_startup_enabled())
        
        # 退出动作
        self.exit_action = QAction("退出(&Q)")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 添加菜单项
        tray_menu.addAction(self.show_action)
        tray_menu.addAction(self.send_action)
        tray_menu.addAction(self.config_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.dnd_action)
        tray_menu.addAction(self.startup_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.exit_action)
        
        # 连接信号和槽
        self.show_action.triggered.connect(self.show_last_notification)
        self.send_action.triggered.connect(self.show_send_notification_dialog)
        self.config_action.triggered.connect(self.show_config_dialog)
        self.dnd_action.triggered.connect(self.toggle_do_not_disturb)
        self.startup_action.triggered.connect(self.toggle_auto_startup)
        self.exit_action.triggered.connect(self.exit_application)
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(load_icon("notification_icon.png"))
            
        # 设置悬停提示
        target_title = self.config.get("notification_title", "911 呼唤群")
        self.tray_icon.setToolTip(f"正在监听：{target_title}")
        logger.info(f"创建系统托盘图标，正在监听：{target_title}")
            
        # 设置上下文菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 连接托盘图标激活信号
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
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_last_notification()
        # 单击不执行任何操作
    
    def on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件
        
        Args:
            reason (QSystemTrayIcon.ActivationReason): 激活原因
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # 双击托盘图标，重播最后一条通知
            if self.last_notification:
                self.show_notification(self.last_notification)
            else:
                # 如果没有最后一条通知，则显示测试通知
                self.show_notification("这是一条测试通知，用于验证双击托盘图标功能是否正常工作。")
    
    def toggle_auto_startup(self, checked):
        """切换开机自启状态 - 使用Windows启动文件夹方式实现
        
        Args:
            checked (bool): 是否启用开机自启
        """
        try:
            # 使用启动文件夹方式实现开机自启
            startup_folder = os.path.join(os.environ["APPDATA"], 
                                        r"Microsoft\Windows\Start Menu\Programs\Startup")
            shortcut_path = os.path.join(startup_folder, "ToastBannerSlider.lnk")
            
            if checked:
                # 创建快捷方式
                if getattr(sys, 'frozen', False):
                    # 打包后的程序
                    target_path = sys.argv[0]
                else:
                    # 开发环境
                    target_path = os.path.abspath(sys.argv[0])
                
                # 使用Windows COM接口创建快捷方式
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = target_path
                shortcut.WorkingDirectory = os.path.dirname(target_path)
                shortcut.IconLocation = target_path
                shortcut.save()
                
                logger.info(f"已启用开机自启，快捷方式路径: {shortcut_path}")
            else:
                # 删除快捷方式
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    logger.info("已禁用开机自启")
        except Exception as e:
            logger.error(f"设置开机自启时出错：{e}")
    
    def check_startup_status(self):
        """检查当前是否设置了开机自启"""
        try:
            # 使用启动文件夹方式检查
            startup_folder = os.path.join(os.environ["APPDATA"], 
                                        r"Microsoft\Windows\Start Menu\Programs\Startup")
            shortcut_path = os.path.join(startup_folder, "ToastBannerSlider.lnk")
            is_enabled = os.path.exists(shortcut_path)
            self.startup_action.setChecked(is_enabled)
            logger.debug(f"开机自启状态：{is_enabled}")
        except Exception as e:
            logger.error(f"检查开机自启状态时出错：{e}")
            self.startup_action.setChecked(False)
    
    def toggle_startup(self, checked):
        """切换开机自启状态
        
        Args:
            checked (bool): 是否启用开机自启
        """
        try:
            import winreg
            
            # 获取当前可执行文件路径
            executable_path = f'"{sys.executable}" --startup'
            
            # 打开注册表项
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 
                                0, winreg.KEY_SET_VALUE)
            
            if checked:
                # 设置开机自启
                winreg.SetValueEx(key, "ToastBannerSlider", 0, winreg.REG_SZ, executable_path)
                logger.info("已设置开机自启")
            else:
                # 取消开机自启
                try:
                    winreg.DeleteValue(key, "ToastBannerSlider")
                    logger.info("已取消开机自启")
                except FileNotFoundError:
                    # 如果键值不存在，忽略错误
                    pass
                    
            winreg.CloseKey(key)
            
        except Exception as e:
            logger.error(f"设置开机自启时出错：{e}")
            # 显示错误信息
            QMessageBox.critical(None, "错误", f"设置开机自启失败：{e}")
    
    def is_auto_startup_enabled(self):
        """检查是否已设置开机自启
        
        Returns:
            bool: 已设置开机自启返回True，否则返回False
        """
        try:
            startup_folder = os.path.join(os.environ["APPDATA"], 
                                        r"Microsoft\Windows\Start Menu\Programs\Startup")
            shortcut_path = os.path.join(startup_folder, "ToastBannerSlider.lnk")
            return os.path.exists(shortcut_path)
        except Exception as e:
            logger.error(f"检查开机自启设置时出错：{e}")
            return False
    
    def exit_application(self):
        """退出应用程序"""
        logger.info("正在退出应用程序...")
        logger.debug("开始隐藏托盘图标")
        
        # 隐藏托盘图标
        if self.tray_icon:
            self.tray_icon.hide()
            logger.debug("托盘图标已隐藏")
            
        # 清理所有通知窗口
        logger.debug(f"开始清理通知窗口，当前窗口数: {len(self.notification_windows)}")
        for window in self.notification_windows[:]:  # 使用副本避免迭代时修改列表
            try:
                # 确保窗口正确关闭并清理资源
                logger.debug("关闭通知窗口")
                if hasattr(window, 'close_with_animation'):
                    window.close_with_animation()
                else:
                    window.close()
            except Exception as e:
                logger.error(f"关闭通知窗口时出错: {e}")
                
        self.notification_windows.clear()
        logger.debug("通知窗口列表已清空")
        
        # 退出应用程序
        logger.debug("计划退出应用程序")
        QTimer.singleShot(100, self._quit_application)
        
    def _quit_application(self):
        """实际退出应用程序"""
        logger.debug("开始实际退出应用程序")
        try:
            self.app.quit()
            logger.debug("应用程序已退出")
        except Exception as e:
            logger.error(f"退出应用程序时出错: {e}")
    
    def run(self):
        """运行应用程序主循环"""
        logger.debug("进入run方法")
        # 启动Qt事件循环
        try:
            logger.debug("尝试启动Qt事件循环")
            exit_code = self.app.exec()
            logger.debug(f"Qt事件循环结束，退出码: {exit_code}")
        except AttributeError:
            # 兼容旧版本PySide/PyQt
            logger.debug("使用旧版本exec_方法启动Qt事件循环")
            exit_code = self.app.exec_()
            logger.debug(f"Qt事件循环结束，退出码: {exit_code}")
        except Exception as e:
            logger.error(f"运行应用程序主循环时出错: {e}", exc_info=True)
            exit_code = 1
            
        logger.info("应用程序主循环已结束")
        
        # 清理资源
        logger.debug("开始清理资源")
        self.cleanup()
        logger.debug("资源清理完成")
        
        return exit_code
        
    def cleanup(self):
        """清理应用程序资源"""
        logger.info("正在清理应用程序资源...")
        logger.debug(f"当前通知窗口数量: {len(self.notification_windows)}")
        
        # 清理所有通知窗口
        for i, window in enumerate(self.notification_windows[:]):
            try:
                logger.debug(f"清理通知窗口 {i+1}")
                if hasattr(window, '_cleanup_and_close'):
                    window._cleanup_and_close()
                else:
                    window.close()
            except Exception as e:
                logger.error(f"清理通知窗口时出错: {e}")
        
        # 停止监听线程
        if self.listener_thread and self.listener_thread.is_running():
            logger.info("正在停止通知监听线程...")
            self.listener_thread.stop()
            self.listener_thread.quit()
            if not self.listener_thread.wait(3000):  # 等待最多3秒
                logger.warning("监听线程未能正常退出，正在强制终止...")
                self.listener_thread.terminate()
                self.listener_thread.wait(1000)
            
        logger.info("应用程序资源清理完成")
        
    def _delayed_create_tray_icon(self):
        """延迟创建托盘图标，确保GUI环境完全初始化"""
        try:
            if not self.create_tray_icon():
                logger.error("创建托盘图标失败")
                # 不要退出程序，只是记录错误
                # self.app.quit()
            else:
                logger.info("托盘图标创建成功")
                
                # 如果是开机自启模式，隐藏托盘图标提示
                if "--startup" in sys.argv:
                    logger.info("以开机自启模式运行，不显示托盘图标提示")
                else:
                    # 显示托盘图标提示
                    if self.tray_icon:
                        self.tray_icon.showMessage(
                            "ToastBannerSlider", 
                            "程序已在系统托盘运行，双击可重播最后一条通知",
                            load_icon("notification_icon.png"),  # 使用notification_icon.png作为图标
                            3000  # 显示3秒
                        )
                        logger.info("已显示托盘图标提示")
                    
                # 更新监听器的目标标题
                listener = get_listener()
                if listener:
                    config = load_config()
                    listener.set_target_title(config.get("notification_title", "911 呼唤群"))
                
        except Exception as e:
            logger.error(f"创建托盘图标时出错：{e}")
            # 不要退出程序，只是记录错误
            # QMessageBox.critical(None, "错误", f"创建托盘图标失败：{e}")
            # self.app.quit()
            
    def on_config_changed(self):
        """配置文件变化时的处理方法"""
        logger.info("检测到配置文件变化，重新加载配置")
        # 重新加载配置
        config = load_config()
        
        # 更新监听器的目标标题
        listener = get_listener()
        if listener:
            listener.set_target_title(config.get("notification_title", "911 呼唤群"))


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
    # 启用高DPI支持
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # 设置应用程序元信息
    app.setApplicationName("ToastBannerSlider")
    app.setApplicationDisplayName("Toast Banner Slider")
    app.setOrganizationName("CreeperAWA")
    app.setOrganizationDomain("github.com/CreeperAWA")
    
    # 设置Windows应用程序User Model ID，确保Toast通知显示正确的应用程序名称
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("ToastBannerSlider")
    except Exception as e:
        logger.warning(f"设置应用程序User Model ID失败: {e}")
    
    manager = ToastBannerManager()
    manager.run()


if __name__ == "__main__":
    main()