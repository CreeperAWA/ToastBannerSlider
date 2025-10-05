"""系统托盘管理模块

该模块负责创建和管理系统托盘图标，处理托盘菜单事件。
"""

import sys
import os
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, Qt, QAction
from PySide6.QtCore import QObject
from logger_config import logger
from config import load_config
from icon_manager import load_icon, get_resource_path
from license_manager import LicenseManager  # 导入许可证管理器
from typing import Optional, Callable, Dict, Union


class TrayManager(QObject):
    """系统托盘管理器"""
    
    def __init__(self, notification_callback: Optional[Callable[[], None]] = None, 
                 show_last_notification_callback: Optional[Callable[[], None]] = None,
                 show_send_notification_callback: Optional[Callable[[], None]] = None, 
                 show_config_dialog_callback: Optional[Callable[[], None]] = None) -> None:
        """初始化系统托盘管理器
        
        Args:
            notification_callback (callable): 退出通知回调函数
            show_last_notification_callback (callable): 显示最后通知回调函数
            show_send_notification_callback (callable): 显示发送通知对话框回调函数
            show_config_dialog_callback (callable): 显示配置对话框回调函数
        """
        super().__init__()
        logger.debug("初始化系统托盘管理器")
        
        # 回调函数
        self.notification_callback = notification_callback
        self.show_last_notification_callback = show_last_notification_callback
        self.show_send_notification_callback = show_send_notification_callback
        self.show_config_dialog_callback = show_config_dialog_callback
        
        # 托盘图标和菜单
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self.tray_menu: Optional[QMenu] = None
        
        # 菜单项
        self.dnd_action: Optional[QAction] = None
        
        # 许可证管理器
        self.license_manager = LicenseManager()
        
        # 加载配置
        self.config: Dict[str, Union[str, float, int, bool, None]] = load_config()
        self.notification_title: str = str(self.config.get("notification_title", "911 呼唤群"))
        
        logger.debug("系统托盘管理器初始化完成")
        
    def create_tray_icon(self) -> bool:
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
            
    def _set_tray_icon(self) -> None:
        """设置托盘图标"""
        try:
            logger.debug("设置托盘图标")
            
            # 加载图标，传递当前配置以确保正确加载自定义图标
            icon = load_icon(self.config)
            if icon and not icon.isNull() and self.tray_icon:
                self.tray_icon.setIcon(icon)
                logger.debug("托盘图标设置成功")
            else:
                # 使用默认图标
                if self.tray_icon:
                    self.tray_icon.setIcon(QIcon("notification_icon.png"))
                logger.warning("使用默认托盘图标")
        except Exception as e:
            logger.error(f"设置托盘图标时出错: {e}")
            
    def _set_tooltip(self) -> None:
        """设置托盘图标工具提示"""
        try:
            logger.debug("设置托盘图标工具提示")
            tooltip = f"ToastBannerSlider - 监听: {self.notification_title}"
            if self.tray_icon:
                self.tray_icon.setToolTip(tooltip)
            logger.debug(f"托盘图标工具提示设置为: {tooltip}")
        except Exception as e:
            logger.error(f"设置托盘图标工具提示时出错: {e}")
            
    def update_tooltip(self, notification_title: str) -> None:
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
            
    def _create_tray_menu(self) -> None:
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
            
            # 许可证信息
            license_info_action = QAction("许可证信息", self.tray_menu)
            license_info_action.triggered.connect(self._on_show_license_info)
            self.tray_menu.addAction(license_info_action)
            
            # 免打扰模式切换
            self.dnd_action = QAction("免打扰", self.tray_menu)
            self.dnd_action.setCheckable(True)
            self.dnd_action.setChecked(bool(self.config.get("do_not_disturb", False)))
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
            if self.tray_icon:
                self.tray_icon.setContextMenu(self.tray_menu)
            
            logger.debug("托盘菜单创建成功")
        except Exception as e:
            logger.error(f"创建托盘菜单时出错: {e}")
            
    def _on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
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
            
    def _on_show_license_info(self) -> None:
        """显示许可证信息"""
        try:
            logger.debug("显示许可证信息")
            dialog = self.license_manager.create_license_info_dialog()
            dialog.exec()
        except Exception as e:
            logger.error(f"显示许可证信息时出错: {e}")
            
    def _on_show_last_notification(self) -> None:
        """显示最后通知"""
        try:
            logger.debug("触发显示最后通知")
            if self.show_last_notification_callback:
                self.show_last_notification_callback()
        except Exception as e:
            logger.error(f"显示最后通知时出错: {e}")
            
    def _on_send_notification(self) -> None:
        """发送通知"""
        try:
            logger.debug("触发发送通知")
            if self.show_send_notification_callback:
                self.show_send_notification_callback()
        except Exception as e:
            logger.error(f"发送通知时出错: {e}")
            
    def _on_show_config_dialog(self) -> None:
        """显示配置对话框"""
        try:
            logger.debug("触发显示配置对话框")
            if self.show_config_dialog_callback:
                self.show_config_dialog_callback()
        except Exception as e:
            logger.error(f"显示配置对话框时出错: {e}")
            
    def _on_toggle_dnd(self, checked: bool) -> None:
        """切换免打扰模式
        
        Args:
            checked (bool): 是否启用免打扰模式
        """
        try:
            logger.debug(f"切换免打扰模式: {checked}")
            self.config["do_not_disturb"] = checked
            self._save_config()
            
            # 更新托盘图标
            self._set_tray_icon()
        except Exception as e:
            logger.error(f"切换免打扰模式时出错: {e}")
            
    def _on_toggle_startup(self, checked: bool) -> None:
        """切换开机自启
        
        Args:
            checked (bool): 是否启用开机自启
        """
        try:
            logger.debug(f"切换开机自启: {checked}")
            if checked:
                self._enable_startup()
            else:
                self._disable_startup()
        except Exception as e:
            logger.error(f"切换开机自启时出错: {e}")
            
    def _on_exit(self) -> None:
        """退出程序"""
        try:
            logger.debug("触发退出程序")
            if self.notification_callback:
                self.notification_callback()
        except Exception as e:
            logger.error(f"退出程序时出错: {e}")
            
    def _save_config(self) -> None:
        """保存配置到文件"""
        try:
            logger.debug("保存配置到文件")
            import json
            config_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            logger.debug("配置保存成功")
        except Exception as e:
            logger.error(f"保存配置时出错: {e}")
            
    def _is_startup_enabled(self) -> bool:
        """检查是否已启用开机自启
        
        Returns:
            bool: 是否已启用开机自启
        """
        try:
            if sys.platform == "win32":
                import winreg
                try:
                    # 打开启动项注册表
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0,
                        winreg.KEY_READ
                    )
                    # 尝试读取值
                    winreg.QueryValueEx(key, "ToastBannerSlider")
                    winreg.CloseKey(key)
                    return True
                except FileNotFoundError:
                    # 键不存在
                    return False
                except Exception as e:
                    logger.error(f"检查开机自启时出错: {e}")
                    return False
            return False
        except Exception as e:
            logger.error(f"检查开机自启时出错: {e}")
            return False
            
    def _enable_startup(self) -> None:
        """启用开机自启"""
        try:
            if sys.platform == "win32":
                import winreg
                # 获取当前可执行文件路径
                exe_path = os.path.abspath(sys.argv[0])
                # 打开或创建启动项注册表
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE
                )
                # 设置值
                winreg.SetValueEx(key, "ToastBannerSlider", 0, winreg.REG_SZ, exe_path)
                winreg.CloseKey(key)
                logger.debug("开机自启已启用")
        except Exception as e:
            logger.error(f"启用开机自启时出错: {e}")
            
    def _disable_startup(self) -> None:
        """禁用开机自启"""
        try:
            if sys.platform == "win32":
                import winreg
                try:
                    # 打开启动项注册表
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0,
                        winreg.KEY_SET_VALUE
                    )
                    # 删除值
                    winreg.DeleteValue(key, "ToastBannerSlider")
                    winreg.CloseKey(key)
                    logger.debug("开机自启已禁用")
                except FileNotFoundError:
                    # 键不存在，无需操作
                    pass
                except Exception as e:
                    logger.error(f"禁用开机自启时出错: {e}")
        except Exception as e:
            logger.error(f"禁用开机自启时出错: {e}")
            
    def show_message(self, title: str, message: str, icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information, timeout: int = 3000) -> None:
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
                # 计算基于系统DPI的图标尺寸
                # 基础尺寸为32像素，根据设备像素比率进行缩放
                base_size = 32
                device_pixel_ratio = 1.0
                
                # 使用安全的方法获取设备像素比率
                try:
                    from PySide6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app is not None:
                        # 使用getattr安全地获取devicePixelRatio方法
                        device_pixel_ratio_func = getattr(app, 'devicePixelRatio', None)
                        if device_pixel_ratio_func is not None:
                            ratio = device_pixel_ratio_func()
                            # 确保返回值是数字类型
                            if isinstance(ratio, (int, float)) and ratio > 0:
                                device_pixel_ratio = float(ratio)
                except Exception:
                    # 如果出现任何异常，使用默认值
                    pass
                    
                icon_size = int(base_size * device_pixel_ratio)
                
                # 使用自定义图标，传递当前配置以确保正确加载自定义图标
                custom_icon = load_icon(self.config)
                if custom_icon and not custom_icon.isNull():
                    # 根据系统DPI缩放比例设置图标尺寸，避免在高分辨率屏幕上模糊
                    if custom_icon.availableSizes():
                        scaled_icon = QIcon(custom_icon.pixmap(icon_size, icon_size))
                        self.tray_icon.showMessage(title, message, scaled_icon, timeout)
                    else:
                        self.tray_icon.showMessage(title, message, custom_icon, timeout)
                else:
                    # 如果没有自定义图标，尝试使用默认资源图标
                    try:
                        resource_icon_path = get_resource_path("notification_icon.ico")
                        if os.path.exists(resource_icon_path):
                            resource_icon = QIcon(resource_icon_path)
                            if not resource_icon.isNull():
                                # 根据系统DPI缩放比例设置图标尺寸，避免在高分辨率屏幕上模糊
                                if resource_icon.availableSizes():
                                    scaled_icon = QIcon(resource_icon.pixmap(icon_size, icon_size))
                                    self.tray_icon.showMessage(title, message, scaled_icon, timeout)
                                else:
                                    self.tray_icon.showMessage(title, message, resource_icon, timeout)
                            else:
                                self.tray_icon.showMessage(title, message, icon, timeout)
                        else:
                            # 尝试使用notification_icon.png
                            resource_icon_path = get_resource_path("notification_icon.png")
                            if os.path.exists(resource_icon_path):
                                resource_icon = QIcon(resource_icon_path)
                                if not resource_icon.isNull():
                                    # 根据系统DPI缩放比例设置图标尺寸，避免在高分辨率屏幕上模糊
                                    if resource_icon.availableSizes():
                                        scaled_icon = QIcon(resource_icon.pixmap(icon_size, icon_size))
                                        self.tray_icon.showMessage(title, message, scaled_icon, timeout)
                                    else:
                                        self.tray_icon.showMessage(title, message, resource_icon, timeout)
                                else:
                                    self.tray_icon.showMessage(title, message, icon, timeout)
                            else:
                                self.tray_icon.showMessage(title, message, icon, timeout)
                    except Exception:
                        self.tray_icon.showMessage(title, message, icon, timeout)
        except Exception as e:
            logger.error(f"显示托盘消息时出错: {e}")
            
    def hide_tray_icon(self) -> None:
        """隐藏托盘图标"""
        try:
            logger.debug("隐藏托盘图标")
            if self.tray_icon:
                self.tray_icon.hide()
        except Exception as e:
            logger.error(f"隐藏托盘图标时出错: {e}")
            
    def update_config(self) -> None:
        """更新配置"""
        try:
            logger.debug("更新托盘管理器配置")
            
            # 保存旧标题和图标设置
            old_title = self.notification_title
            old_icon_setting = self.config.get("custom_icon") if "custom_icon" in self.config else None
            
            # 重新加载配置
            self.config = load_config()
            self.notification_title = str(self.config.get("notification_title", "911 呼唤群"))
            
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
            
    def _update_tray_icon(self) -> None:
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