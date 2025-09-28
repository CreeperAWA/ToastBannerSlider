"""系统托盘管理模块

该模块负责创建和管理系统托盘图标及相关操作。
"""

import os
import sys
from win32com.client import Dispatch
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QAction, QIcon
from loguru import logger
from icon_manager import load_icon
from config import load_config, save_config, get_config_path


class TrayManager:
    """系统托盘管理器 - 负责创建和管理系统托盘图标"""
    
    def __init__(self, notification_callback, show_last_notification_callback, 
                 show_send_notification_callback, show_config_dialog_callback):
        """初始化系统托盘管理器
        
        Args:
            notification_callback (function): 通知回调函数
            show_last_notification_callback (function): 显示最后通知回调函数
            show_send_notification_callback (function): 显示发送通知回调函数
            show_config_dialog_callback (function): 显示配置对话框回调函数
        """
        self.notification_callback = notification_callback
        self.show_last_notification_callback = show_last_notification_callback
        self.show_send_notification_callback = show_send_notification_callback
        self.show_config_dialog_callback = show_config_dialog_callback
        
        self.tray_icon = None
        self.show_action = None
        self.send_action = None
        self.config_action = None
        self.dnd_action = None
        self.startup_action = None
        self.exit_action = None
        
        # 加载初始配置
        self.config = load_config()
        
    def create_tray_icon(self):
        """创建系统托盘图标
        
        Returns:
            bool: 创建成功返回True，否则返回False
        """
        # 检查系统托盘是否可用
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("系统托盘不可用")
            return False
            
        # 创建托盘菜单项
        self._create_menu_actions()
        
        # 创建托盘菜单
        tray_menu = QMenu()
        tray_menu.addAction(self.show_action)
        tray_menu.addAction(self.send_action)
        tray_menu.addAction(self.config_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.dnd_action)
        tray_menu.addAction(self.startup_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.exit_action)
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(load_icon("notification_icon.png"))
            
        # 设置悬停提示
        target_title = self.config.get("notification_title", "911 呼唤群")
        self.tray_icon.setToolTip(f"正在监听：{target_title}")
        logger.info(f"创建系统托盘图标，正在监听：{target_title}")
            
        # 设置上下文菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 连接托盘图标激活信号
        self.tray_icon.activated.connect(self._icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
        
        # 检查托盘图标是否成功显示
        if self.tray_icon.isVisible():
            logger.info("系统托盘图标已成功显示")
            return True
        else:
            logger.error("系统托盘图标显示失败")
            return False
            
    def _create_menu_actions(self):
        """创建托盘菜单动作项"""
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
        
        # 连接信号和槽
        self.show_action.triggered.connect(self.show_last_notification_callback)
        self.send_action.triggered.connect(self.show_send_notification_callback)
        self.config_action.triggered.connect(self.show_config_dialog_callback)
        self.dnd_action.triggered.connect(self._toggle_do_not_disturb)
        self.startup_action.triggered.connect(self._toggle_auto_startup)
        self.exit_action.triggered.connect(self._exit_application)
        
    def _icon_activated(self, reason):
        """处理托盘图标激活事件
        
        Args:
            reason (QSystemTrayIcon.ActivationReason): 激活原因
        """
        # 只有双击托盘图标才显示最后通知
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_last_notification_callback()
    
    def _toggle_do_not_disturb(self, checked):
        """切换免打扰模式
        
        Args:
            checked (bool): 是否启用免打扰模式
        """
        # 更新配置
        self.config["do_not_disturb"] = checked
        save_config(self.config)
        logger.info(f"免打扰模式已{'启用' if checked else '禁用'}")
        
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
            
    def _toggle_auto_startup(self, checked):
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
            
    def _exit_application(self):
        """退出应用程序"""
        logger.info("正在退出应用程序...")
        self.hide_tray_icon()
        # 调用通知回调函数退出应用
        if self.notification_callback:
            self.notification_callback()
            
    def hide_tray_icon(self):
        """隐藏托盘图标"""
        logger.debug("开始隐藏托盘图标")
        if self.tray_icon:
            self.tray_icon.hide()
            logger.debug("托盘图标已隐藏")
            
    def show_message(self, title, message, icon=None, timeout=3000):
        """显示托盘消息
        
        Args:
            title (str): 消息标题
            message (str): 消息内容
            icon (QIcon, optional): 消息图标
            timeout (int): 显示时间（毫秒）
        """
        if self.tray_icon:
            if icon is None:
                icon = load_icon("notification_icon.png")
            self.tray_icon.showMessage(title, message, icon, timeout)
            logger.info(f"已显示托盘图标提示: {title} - {message}")
            
    def update_tooltip(self, title=None):
        """更新托盘图标提示文本
        
        Args:
            title (str, optional): 新的标题，如果未提供则从配置中获取
        """
        if not title:
            config = load_config()
            title = config.get("notification_title", "911 呼唤群")
            
        if self.tray_icon:
            self.tray_icon.setToolTip(f"正在监听：{title}")
            logger.debug(f"托盘图标提示已更新: 正在监听 {title}")
            
    def update_config(self):
        """更新配置"""
        logger.debug("正在更新托盘管理器配置")
        try:
            # 重新加载配置
            self.config = load_config()
            logger.info("托盘管理器配置已更新")
            
            # 更新托盘图标
            if self.tray_icon:
                self.tray_icon.setIcon(load_icon())
                self.tray_icon.setToolTip("ToastBannerSlider")
        except Exception as e:
            logger.error(f"更新托盘管理器配置时出错：{e}")