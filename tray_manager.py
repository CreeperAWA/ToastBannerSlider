"""系统托盘管理模块

该模块负责创建和管理系统托盘图标，处理托盘菜单事件。
"""

import sys
import os
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, Qt, QAction
from logger_config import logger
from config import load_config
from icon_manager import load_icon, get_resource_path


class TrayManager:
    """系统托盘管理器"""
    
    def __init__(self, notification_callback=None, show_last_notification_callback=None,
                 show_send_notification_callback=None, show_config_dialog_callback=None):
        """初始化系统托盘管理器
        
        Args:
            notification_callback (callable): 退出通知回调函数
            show_last_notification_callback (callable): 显示最后通知回调函数
            show_send_notification_callback (callable): 显示发送通知对话框回调函数
            show_config_dialog_callback (callable): 显示配置对话框回调函数
        """
        logger.debug("初始化系统托盘管理器")
        
        # 回调函数
        self.notification_callback = notification_callback
        self.show_last_notification_callback = show_last_notification_callback
        self.show_send_notification_callback = show_send_notification_callback
        self.show_config_dialog_callback = show_config_dialog_callback
        
        # 托盘图标和菜单
        self.tray_icon = None
        self.tray_menu = None
        
        # 菜单项
        self.dnd_action = None
        
        # 加载配置
        self.config = load_config()
        self.notification_title = self.config.get("notification_title", "911 呼唤群")
        
        logger.debug("系统托盘管理器初始化完成")
        
    def create_tray_icon(self):
        """创建系统托盘图标
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        try:
            logger.debug("开始创建系统托盘图标")
            
            # 检查系统是否支持托盘图标
            if not QSystemTrayIcon.isSystemTrayAvailable():
                logger.error("系统不支持托盘图标")
                return False
                
            # 创建托盘图标
            self.tray_icon = QSystemTrayIcon()
            
            # 设置图标
            self._set_tray_icon()
            
            # 设置工具提示
            self._set_tooltip()
            
            # 创建托盘菜单
            self._create_tray_menu()
            
            # 连接信号
            self.tray_icon.activated.connect(self._on_tray_icon_activated)
            
            # 显示托盘图标
            self.tray_icon.show()
            
            if not self.tray_icon.isVisible():
                logger.error("托盘图标创建失败")
                return False
                
            logger.debug("系统托盘图标创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建系统托盘图标时出错: {e}")
            return False
            
    def _set_tray_icon(self):
        """设置托盘图标"""
        try:
            logger.debug("设置托盘图标")
            
            # 加载图标，传递当前配置以确保正确加载自定义图标
            icon = load_icon(self.config)
            if icon and not icon.isNull():
                self.tray_icon.setIcon(icon)
                logger.debug("托盘图标设置成功")
            else:
                # 使用默认图标
                self.tray_icon.setIcon(QIcon("notification_icon.png"))
                logger.warning("使用默认托盘图标")
        except Exception as e:
            logger.error(f"设置托盘图标时出错: {e}")
            
    def _set_tooltip(self):
        """设置托盘图标工具提示"""
        try:
            logger.debug("设置托盘图标工具提示")
            tooltip = f"ToastBannerSlider - 监听: {self.notification_title}"
            self.tray_icon.setToolTip(tooltip)
            logger.debug(f"托盘图标工具提示设置为: {tooltip}")
        except Exception as e:
            logger.error(f"设置托盘图标工具提示时出错: {e}")
            
    def update_tooltip(self, notification_title):
        """更新托盘图标提示
        
        Args:
            notification_title (str): 新的通知标题
        """
        try:
            logger.debug(f"更新托盘图标提示: {notification_title}")
            if self.tray_icon:
                tooltip = f"ToastBannerSlider - 监听: {notification_title}"
                self.tray_icon.setToolTip(tooltip)
                logger.debug("托盘图标提示已更新")
        except Exception as e:
            logger.error(f"更新托盘图标提示时出错: {e}")
            
    def _create_tray_menu(self):
        """创建托盘菜单"""
        try:
            logger.debug("创建托盘菜单")
            
            # 创建菜单
            self.tray_menu = QMenu()
            
            # 添加菜单项
            show_last_action = QAction("显示最后通知", self.tray_menu)
            show_last_action.triggered.connect(self._on_show_last_notification)
            self.tray_menu.addAction(show_last_action)
            
            send_notification_action = QAction("发送通知", self.tray_menu)
            send_notification_action.triggered.connect(self._on_send_notification)
            self.tray_menu.addAction(send_notification_action)
            
            self.tray_menu.addSeparator()
            
            config_action = QAction("配置设置", self.tray_menu)
            config_action.triggered.connect(self._on_show_config_dialog)
            self.tray_menu.addAction(config_action)
            
            # 免打扰模式切换
            self.dnd_action = QAction("免打扰", self.tray_menu)
            self.dnd_action.setCheckable(True)
            self.dnd_action.setChecked(self.config.get("do_not_disturb", False))
            self.dnd_action.triggered.connect(self._on_toggle_dnd)
            self.tray_menu.addAction(self.dnd_action)
            
            # 开机自启
            startup_action = QAction("开机自启", self.tray_menu)
            startup_action.setCheckable(True)
            startup_action.setChecked(self._is_startup_enabled())
            startup_action.triggered.connect(self._on_toggle_startup)
            self.tray_menu.addAction(startup_action)
            
            self.tray_menu.addSeparator()
            
            exit_action = QAction("退出", self.tray_menu)
            exit_action.triggered.connect(self._on_exit)
            self.tray_menu.addAction(exit_action)
            
            # 设置托盘图标菜单
            self.tray_icon.setContextMenu(self.tray_menu)
            
            logger.debug("托盘菜单创建成功")
        except Exception as e:
            logger.error(f"创建托盘菜单时出错: {e}")
            
    def _on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件
        
        Args:
            reason (QSystemTrayIcon.ActivationReason): 激活原因
        """
        try:
            logger.debug(f"托盘图标被激活，原因: {reason}")
            
            # 双击显示最后通知
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                self._on_show_last_notification()
        except Exception as e:
            logger.error(f"处理托盘图标激活事件时出错: {e}")
            
    def _on_show_last_notification(self):
        """处理显示最后通知事件"""
        try:
            logger.debug("处理显示最后通知事件")
            if self.show_last_notification_callback:
                self.show_last_notification_callback()
        except Exception as e:
            logger.error(f"处理显示最后通知事件时出错: {e}")
            
    def _on_send_notification(self):
        """处理发送通知事件"""
        try:
            logger.debug("处理发送通知事件")
            if self.show_send_notification_callback:
                self.show_send_notification_callback()
        except Exception as e:
            logger.error(f"处理发送通知事件时出错: {e}")
            
    def _on_show_config_dialog(self):
        """处理显示配置对话框事件"""
        try:
            logger.debug("处理显示配置对话框事件")
            if self.show_config_dialog_callback:
                self.show_config_dialog_callback()
        except Exception as e:
            logger.error(f"处理显示配置对话框事件时出错: {e}")
            
    def _on_toggle_dnd(self, checked):
        """处理免打扰模式切换事件
        
        Args:
            checked (bool): 是否启用免打扰模式
        """
        try:
            logger.debug(f"处理免打扰模式切换事件: {checked}")
            
            # 更新配置
            self.config["do_not_disturb"] = checked
            from config import save_config
            save_config(self.config)
            
            # 显示状态消息
            status = "已启用" if checked else "已禁用"
            self.show_message("ToastBannerSlider", f"免打扰模式{status}")
        except Exception as e:
            logger.error(f"处理免打扰模式切换事件时出错: {e}")
            
    def _is_startup_enabled(self):
        """检查是否已设置开机自启
        
        Returns:
            bool: 已设置返回True，否则返回False
        """
        try:
            if sys.platform == "win32":
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_READ
                )
                try:
                    winreg.QueryValueEx(key, "ToastBannerSlider")
                    return True
                except FileNotFoundError:
                    return False
                finally:
                    winreg.CloseKey(key)
            return False
        except Exception as e:
            logger.error(f"检查开机自启设置时出错: {e}")
            return False
            
    def _on_toggle_startup(self, checked):
        """处理开机自启切换事件
        
        Args:
            checked (bool): 是否启用开机自启
        """
        try:
            logger.debug(f"处理开机自启切换事件: {checked}")
            
            if sys.platform == "win32":
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_WRITE
                )
                
                try:
                    if checked:
                        # 启用开机自启
                        exe_path = sys.executable
                        if hasattr(sys, 'frozen'):
                            # 打包后的程序
                            winreg.SetValueEx(key, "ToastBannerSlider", 0, winreg.REG_SZ, f'"{exe_path}" --startup')
                        else:
                            # 开发环境
                            winreg.SetValueEx(key, "ToastBannerSlider", 0, winreg.REG_SZ, f'"{exe_path}" "{os.path.join(os.path.dirname(exe_path), "main.py")}" --startup')
                        self.show_message("ToastBannerSlider", "已设置开机自启")
                    else:
                        # 禁用开机自启
                        winreg.DeleteValue(key, "ToastBannerSlider")
                        self.show_message("ToastBannerSlider", "已取消开机自启")
                finally:
                    winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"处理开机自启切换事件时出错: {e}")
            error_msg = "设置开机自启失败" if checked else "取消开机自启失败"
            self.show_message("ToastBannerSlider", error_msg)
            
    def _on_exit(self):
        """处理退出事件"""
        try:
            logger.debug("处理退出事件")
            if self.notification_callback:
                self.notification_callback()
        except Exception as e:
            logger.error(f"处理退出事件时出错: {e}")
            
    def show_message(self, title, message, icon=QSystemTrayIcon.MessageIcon.Information, timeout=3000):
        """显示托盘消息
        
        Args:
            title (str): 消息标题
            message (str): 消息内容
            icon (QSystemTrayIcon.MessageIcon): 消息图标
            timeout (int): 超时时间（毫秒）
        """
        try:
            logger.debug(f"显示托盘消息: {title} - {message}")
            if self.tray_icon and self.tray_icon.isVisible():
                # 使用自定义图标，传递当前配置以确保正确加载自定义图标
                custom_icon = load_icon(self.config)
                if custom_icon and not custom_icon.isNull():
                    self.tray_icon.showMessage(title, message, custom_icon, timeout)
                else:
                    # 如果没有自定义图标，尝试使用默认资源图标
                    try:
                        resource_icon_path = get_resource_path("notification_icon.ico")
                        if os.path.exists(resource_icon_path):
                            resource_icon = QIcon(resource_icon_path)
                            if not resource_icon.isNull():
                                self.tray_icon.showMessage(title, message, resource_icon, timeout)
                            else:
                                self.tray_icon.showMessage(title, message, icon, timeout)
                        else:
                            # 尝试使用notification_icon.png
                            resource_icon_path = get_resource_path("notification_icon.png")
                            if os.path.exists(resource_icon_path):
                                resource_icon = QIcon(resource_icon_path)
                                if not resource_icon.isNull():
                                    self.tray_icon.showMessage(title, message, resource_icon, timeout)
                                else:
                                    self.tray_icon.showMessage(title, message, icon, timeout)
                            else:
                                self.tray_icon.showMessage(title, message, icon, timeout)
                    except Exception:
                        self.tray_icon.showMessage(title, message, icon, timeout)
        except Exception as e:
            logger.error(f"显示托盘消息时出错: {e}")
            
    def hide_tray_icon(self):
        """隐藏托盘图标"""
        try:
            logger.debug("隐藏托盘图标")
            if self.tray_icon:
                self.tray_icon.hide()
        except Exception as e:
            logger.error(f"隐藏托盘图标时出错: {e}")
            
    def update_config(self):
        """更新配置"""
        try:
            logger.debug("更新托盘管理器配置")
            
            # 保存旧标题和图标设置
            old_title = self.notification_title
            old_icon_setting = self.config.get("custom_icon") if "custom_icon" in self.config else None
            
            # 重新加载配置
            self.config = load_config()
            self.notification_title = self.config.get("notification_title", "911 呼唤群")
            
            # 如果通知标题发生变化，更新托盘提示
            if old_title != self.notification_title:
                self.update_tooltip(self.notification_title)
                
            # 检查图标设置是否发生变化
            new_icon_setting = self.config.get("custom_icon") if "custom_icon" in self.config else None
            if old_icon_setting != new_icon_setting:
                # 图标设置发生变化，更新托盘图标
                self._update_tray_icon()
            else:
                # 总是更新托盘图标（确保图标及时更新）
                self._update_tray_icon()
            
            logger.debug("托盘管理器配置更新完成")
        except Exception as e:
            logger.error(f"更新托盘管理器配置时出错: {e}")
            
    def _update_tray_icon(self):
        """更新托盘图标"""
        try:
            logger.debug("更新托盘图标")
            
            # 加载图标
            icon = load_icon(self.config)
            if icon and not icon.isNull():
                if self.tray_icon:
                    self.tray_icon.setIcon(icon)
                    logger.debug("托盘图标已更新")
                else:
                    logger.warning("托盘图标对象为空")
            else:
                # 使用系统默认图标作为最终后备
                default_icon = QIcon.fromTheme("application-x-executable")
                if default_icon.isNull():
                    # 创建一个简单的彩色图标作为后备
                    pixmap = QPixmap(32, 32)
                    pixmap.fill(Qt.GlobalColor.blue)
                    default_icon = QIcon(pixmap)
                    
                if self.tray_icon:
                    self.tray_icon.setIcon(default_icon)
                    logger.warning("使用默认图标")
                else:
                    logger.warning("托盘图标对象为空")
        except Exception as e:
            logger.error(f"更新托盘图标时出错: {e}")
            # 出错时设置一个默认图标
            try:
                if self.tray_icon:
                    default_icon = QIcon.fromTheme("application-x-executable")
                    if default_icon.isNull():
                        pixmap = QPixmap(32, 32)
                        pixmap.fill(Qt.GlobalColor.red)
                        default_icon = QIcon(pixmap)
                    self.tray_icon.setIcon(default_icon)
            except Exception as e2:
                logger.error(f"设置默认托盘图标时出错: {e2}")