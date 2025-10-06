"""ToastBannerSlider主程序

该模块整合了通知监听和显示功能，提供系统托盘图标和用户交互界面。
负责管理整个应用程序的生命周期，包括配置管理、通知监听和显示等核心功能。
"""

import sys
import time
import os
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from PySide6.QtCore import QTimer, QObject
from notice_slider import NotificationWindow
from warning_banner import WarningBanner  # 导入警告横幅
from config import load_config, get_config_path
from logger_config import logger, setup_logger
from tray_manager import TrayManager
from notification_listener import NotificationListenerThread
from config_dialog import ConfigDialog
from send_notification_dialog import SendNotificationDialog
from banner_factory import create_banner  # 导入横幅工厂
from license_manager import LicenseManager  # 导入许可证管理器
from typing import Optional, List, Tuple, Union, Callable, cast, Dict

def show_license_info_and_exit(license_manager: LicenseManager, hardware_info: Dict[str, str], hardware_key: str):
    """显示许可证错误信息并退出程序
    
    Args:
        license_manager: 许可证管理器实例
        hardware_info: 已获取的硬件信息
        hardware_key: 已生成的硬件标识
    """
    # 创建并显示错误消息框
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("许可证错误")
    
    # 构造机器码信息
    machine_code = f"""CPU序列号: {hardware_info['cpu']}
硬盘序列号: {hardware_info['disk']}
主板序列号: {hardware_info['motherboard']}

硬件标识: {hardware_key}"""
    
    # 在日志中输出机器码信息
    logger.info("许可证验证失败，机器码信息如下：")
    logger.info(f"CPU序列号: {hardware_info['cpu']}")
    logger.info(f"硬盘序列号: {hardware_info['disk']}")
    logger.info(f"主板序列号: {hardware_info['motherboard']}")
    logger.info(f"硬件标识: {hardware_key}")
    
    # 显示消息
    message = f"""许可证验证失败，程序无法启动！

请将以下机器码信息提供给开发者以获取有效许可证：

{machine_code}

点击"复制"按钮将机器码复制到剪贴板。
"""
    
    msg_box.setText(message)
    
    # 添加复制按钮
    copy_button = msg_box.addButton("复制机器码", QMessageBox.ButtonRole.ActionRole)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
    
    # 显示对话框并处理按钮点击事件
    msg_box.exec()
    
    if msg_box.clickedButton() == copy_button:
        # 复制机器码到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(f"CPU: {hardware_info['cpu']}\nDisk: {hardware_info['disk']}\nMotherboard: {hardware_info['motherboard']}\nHardware Key: {hardware_key}")
        
        # 显示复制成功的提示
        success_msg = QMessageBox()
        success_msg.setIcon(QMessageBox.Icon.Information)
        success_msg.setWindowTitle("复制成功")
        success_msg.setText("机器码已复制到剪贴板！")
        success_msg.exec()
        
        # 重新显示原始对话框
        msg_box.exec()
    
    sys.exit(1)


# 程序启动时先加载配置，再初始化日志系统
config = load_config()
setup_logger(config)

# 程序启动时进行许可证验证（仅检查，不处理UI）
license_manager = LicenseManager()
# 预先获取硬件信息，避免重复加载
hardware_info = license_manager.get_hardware_info()
hardware_key = license_manager.generate_hardware_key()

if not license_manager.verify_license():
    logger.error("许可证验证失败，程序无法启动。")
    # 初始化Qt应用程序以显示消息框
    app = QApplication(sys.argv)
    # 传递已获取的硬件信息，避免重复加载
    show_license_info_and_exit(license_manager, hardware_info, hardware_key)

# 许可证验证通过，继续执行主程序逻辑
class ConfigWatcher(QObject):
    """配置文件观察者 - 监听配置文件变化并发出信号"""
    
    def __init__(self, config_path: str) -> None:
        """初始化配置观察者
        
        Args:
            config_path: 配置文件路径
        """
        super().__init__()
        self.config_path = config_path
        self.last_mtime = self._get_mtime()
        self.config_changed_callback: Optional[Callable[[], None]] = None
        
    def _get_mtime(self) -> float:
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
        
    def check_config_change(self) -> None:
        """检查配置文件是否发生变化，如果变化则发出信号"""
        try:
            current_mtime = self._get_mtime()
            if current_mtime > self.last_mtime:
                self.last_mtime = current_mtime
                # 发出配置更改信号（通过调用回调函数实现）
                if hasattr(self, 'config_changed_callback') and self.config_changed_callback:
                    self.config_changed_callback()
        except KeyboardInterrupt:
            # 正常处理键盘中断信号（Ctrl+C）
            raise
        except Exception as e:
            logger.warning(f"检查配置文件变化时出错：{e}")


class ToastBannerManager(QObject):
    """Toast横幅通知管理器 - 控制整个应用程序的生命周期和核心功能"""
    
    def __init__(self, app: QApplication, config: Dict[str, Union[str, float, int, bool, None]], parent: Optional[QObject] = None) -> None:
        """初始化Toast横幅管理器
        
        Args:
            app: QApplication实例
            config: 配置字典
            parent: 父对象
        """

        # 使用传入的QApplication和配置字典
        self.app = app
        self.config = config
        self.config_path = get_config_path()
        
        # 初始化成员变量
        self.notification_windows: List[Union[NotificationWindow, WarningBanner]] = []
        self.last_notification: Optional[str] = None
        self.config_watcher: Optional[ConfigWatcher] = None
        self.config_timer: Optional[QTimer] = None
        self.listener_thread: Optional[NotificationListenerThread] = None
        self.tray_manager: Optional[TrayManager] = None
        self._send_dialog: Optional[SendNotificationDialog] = None
        self.message_history: List[Tuple[str, float]] = []
        self.has_notifications: bool = False
        self.is_initialized: bool = False
        
        try:
            # 初始化UI
            self.init_ui()
            
            self.is_initialized = True
            logger.info("ToastBannerSlider初始化完成")
            
        except Exception as e:
            logger.error(f"ToastBannerManager初始化失败: {e}", exc_info=True)
            raise
        
    def init_ui(self) -> None:
        """初始化用户界面"""
        self.message_history = []
        self.has_notifications = False
        
        # 创建并启动配置文件观察者
        self.config_watcher = ConfigWatcher(self.config_path)
        self.config_watcher.config_changed_callback = self.update_config
        self.config_timer = QTimer()
        self.config_timer.timeout.connect(self.config_watcher.check_config_change)
        self.config_timer.start(1000)
        
        # 创建系统托盘管理器
        self.tray_manager = TrayManager(
            notification_callback=self.exit_application,
            show_last_notification_callback=self.show_last_notification,
            show_send_notification_callback=self.show_send_notification_dialog,
            show_config_dialog_callback=self.show_config_dialog
        )
        
        # 启动通知监听线程
        self.listener_thread = NotificationListenerThread()
        self.listener_thread.notification_received.connect(self.show_notification)
        self.listener_thread.start()
        
        # 延迟创建托盘图标
        QTimer.singleShot(1000, self._delayed_create_tray_icon)
        
        logger.info("主程序UI初始化完成")
        
    def show_notification(self, message: str, skip_duplicate_check: bool = False, skip_restrictions: bool = False, max_scrolls: Optional[int] = None) -> None:
        """显示通知横幅
        
        Args:
            message: 要显示的通知消息
            skip_duplicate_check: 是否跳过重复消息检查，默认为False
            skip_restrictions: 是否跳过限制检查（免打扰和重复通知），默认为False
            max_scrolls: 自定义滚动次数，如果为None则使用配置文件中的设置
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
            
            # 检查是否启用了免打扰模式（除非跳过限制）
            if not skip_restrictions and self.config.get("do_not_disturb", False):
                logger.info("免打扰模式已启用，忽略通知")
                return
                
            # 检查是否启用了忽略重复通知（5分钟内）（除非跳过限制）
            # 如果skip_duplicate_check为True，则跳过重复消息检查
            if not skip_restrictions and not skip_duplicate_check and self.config.get("ignore_duplicate", False):
                # 检查是否在5分钟内有相同消息
                if self.is_duplicate_message(message, current_time):
                    logger.info(f"忽略5分钟内的重复通知：{message}")
                    return
            
            # 加载配置
            logger.debug("加载配置")
            self.config = load_config()
            
            # 计算新窗口的垂直位置
            logger.debug("计算窗口位置参数")
            base_height = int(self.config.get("window_height", 128) or 128)  # 确保转换为int
            banner_spacing = int(self.config.get("banner_spacing", 10) or 10)  # 确保转换为int
            
            # 计算已有窗口的总高度和间隔数
            total_existing_height = len(self.notification_windows) * base_height
            total_spacing = len(self.notification_windows) * banner_spacing
            
            # 创建并显示新的通知窗口，传递自定义滚动次数
            logger.debug("创建横幅实例")
            window = create_banner(message, vertical_offset=total_existing_height + total_spacing, max_scrolls=max_scrolls)
            logger.debug("横幅实例创建完成")
            
            # 防止程序因最后一个窗口关闭而退出
            # 使用类型注释忽略Pylance错误
            if hasattr(self.app, 'setQuitOnLastWindowClosed') and callable(getattr(self.app, 'setQuitOnLastWindowClosed', None)):
                self.app.setQuitOnLastWindowClosed(False)  # type: ignore
                
            logger.debug("显示窗口")
            window.show()
            logger.debug("窗口显示完成")
            
            logger.debug("将窗口添加到通知窗口列表")
            self.notification_windows.append(window)
            
            logger.debug("连接窗口关闭信号")
            # 连接窗口关闭信号，以便从列表中移除
            # 注意：WarningBanner可能没有window_closed信号，需要检查
            if hasattr(window, 'window_closed'):
                cast(NotificationWindow, window).window_closed.connect(self.remove_notification_window)
            
            # 记录日志
            logger.info(f"显示通知：{message}")
        except Exception as e:
            logger.error(f"显示通知时出错：{e}", exc_info=True)
        
    def cleanup_message_history(self) -> None:
        """清理5分钟前的消息历史记录"""
        current_time = time.time()
        # 保留5分钟内的消息记录
        self.message_history = [
            (msg, timestamp) for msg, timestamp in self.message_history
            if (current_time - timestamp) <= 300
        ]
        
    def is_duplicate_message(self, message: str, current_time: float) -> bool:
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
        
    def remove_notification_window(self, window: NotificationWindow) -> None:
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
            
    def update_window_positions(self) -> None:
        """更新所有通知窗口的位置"""
        # 加载配置
        config = load_config()
        base_height = int(config.get("window_height", 128) or 128)  # 确保转换为int
        banner_spacing = int(config.get("banner_spacing", 10) or 10)  # 确保转换为int
        
        # 更新每个窗口的垂直位置
        for i, window in enumerate(self.notification_windows):
            new_offset = i * (base_height + banner_spacing)
            # 使用类型安全的方法调用update_vertical_offset
            if hasattr(window, 'update_vertical_offset'):
                try:
                    window.update_vertical_offset(new_offset)  # type: ignore
                except Exception:
                    pass
            # 对于WarningBanner，可能需要不同的处理方式
            elif hasattr(window, 'move'):
                try:
                    # WarningBanner使用move方法调整位置
                    window.move(0, new_offset)
                except Exception:
                    pass
        
    def show_last_notification(self) -> None:
        """显示最后一条通知，将其添加到现有通知队列中"""
        # 检查是否有历史消息
        if not hasattr(self, 'message_history') or not self.message_history:
            logger.warning("没有可显示的通知")
            return
            
        # 获取最后一条消息
        last_message, _ = self.message_history[-1] if self.message_history else ("", 0)
        
        # 检查是否有有效的最后消息
        if last_message:
            # 将最后一条消息作为新通知显示，添加到现有通知队列中
            # 传递skip_duplicate_check=True和skip_restrictions=True参数以跳过所有限制
            self.show_notification(last_message, skip_duplicate_check=True, skip_restrictions=True)
        else:
            logger.warning("没有可显示的通知")
    
    def show_send_notification_dialog(self) -> None:
        """显示发送通知对话框"""
        logger.debug("准备显示发送通知对话框")
        # 确保不会因为对话框关闭而退出主程序
        # 使用类型注释忽略Pylance错误
        if hasattr(self.app, 'setQuitOnLastWindowClosed') and callable(getattr(self.app, 'setQuitOnLastWindowClosed', None)):
            self.app.setQuitOnLastWindowClosed(False)  # type: ignore
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
    
    def show_config_dialog(self) -> None:
        """显示配置对话框"""
        logger.debug("正在显示配置对话框...")
        try:
            dialog = ConfigDialog()
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 配置已在_on_ok中保存，重新加载配置
                self.config = load_config()
                logger.info("配置已更新")
        except Exception as e:
            logger.error(f"显示配置对话框时出错：{e}", exc_info=True)
    
    def update_config(self) -> None:
        """更新配置"""
        logger.info("检测到配置文件变更，正在重新加载配置...")
        try:
            # 重新加载配置
            self.config = load_config()
            
            # 更新日志等级
            setup_logger(self.config)
            
            # 更新所有现有窗口的配置
            for window in self.notification_windows:
                # 检查窗口类型并调用相应的方法
                if hasattr(window, 'update_config'):
                    try:
                        window.update_config(self.config)  # type: ignore
                    except Exception as e:
                        logger.error(f"更新窗口配置时出错：{e}")
            
            # 更新托盘图标提示文本
            if self.tray_manager:
                self.tray_manager.update_config()
                        
            logger.info("配置更新完成")
        except Exception as e:
            logger.error(f"更新配置时出错：{e}", exc_info=True)
    
    def _delayed_create_tray_icon(self) -> None:
        """延迟创建托盘图标"""
        try:
            logger.debug("延迟创建托盘图标")
            
            # 创建托盘图标
            if self.tray_manager and not self.tray_manager.create_tray_icon():
                logger.error("创建托盘图标失败")
                return
                
            # 显示托盘消息，使用自定义图标
            if self.tray_manager:
                self.tray_manager.show_message(
                    "ToastBannerSlider", 
                    "程序已运行，可在托盘菜单中进行操作"
                )
            
            logger.info("托盘图标创建成功")
        except Exception as e:
            logger.error(f"延迟创建托盘图标时出错: {e}")
            
    def exit_application(self) -> None:
        """退出应用程序"""
        logger.info("正在退出应用程序...")
        if self.tray_manager:
            self.tray_manager.hide_tray_icon()
        
        # 清理所有通知窗口
        logger.debug(f"开始清理通知窗口，当前窗口数: {len(self.notification_windows)}")
        for window in self.notification_windows[:]:  # 使用副本避免迭代时修改列表
            try:
                # 确保窗口正确关闭并清理资源
                logger.debug("关闭通知窗口")
                # 检查窗口类型并调用相应的关闭方法
                if isinstance(window, NotificationWindow) and hasattr(window, 'close_with_animation'):
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
        
    def _quit_application(self) -> None:
        """实际退出应用程序"""
        logger.debug("开始实际退出应用程序")
        try:
            self.app.quit()
            logger.debug("应用程序已退出")
        except Exception as e:
            logger.error(f"退出应用程序时出错: {e}")
    
    def run(self) -> int:
        """运行应用程序主循环"""
        logger.debug("进入run方法")
        # 启动Qt事件循环
        try:
            logger.debug("尝试启动Qt事件循环")
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
        
    def cleanup(self) -> None:
        """清理应用程序资源"""
        logger.info("正在清理应用程序资源...")
        logger.debug(f"当前通知窗口数量: {len(self.notification_windows)}")
        
        # 清理所有通知窗口
        for i, window in enumerate(self.notification_windows[:]):
            try:
                logger.debug(f"清理通知窗口 {i+1}")
                # 检查窗口类型并使用适当的方法关闭
                if isinstance(window, NotificationWindow) and hasattr(window, 'close_with_animation'):
                    window.close_with_animation()
                elif hasattr(window, 'close'):
                    window.close()
                else:
                    # 最后尝试直接删除
                    del window
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
        
        # 停止配置定时器
        if self.config_timer:
            self.config_timer.stop()
            self.config_timer = None
            
        # 清理配置观察者
        self.config_watcher = None
        
        # 清理托盘管理器
        if self.tray_manager:
            self.tray_manager.hide_tray_icon()
            self.tray_manager = None
            
        logger.info("应用程序资源清理完成")


def main():
    """主函数"""
    global app
    
    # 初始化日志 (使用默认设置)
    setup_logger()
    logger.info("正在启动ToastBannerSlider...")

    # 打印启动信息
    print("=" * 30)
    print("Toast 横幅通知系统")
    print("=" * 30)
    print("正在启动...")

    # 初始化Qt应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("ToastBannerSlider")
    app.setApplicationDisplayName("Toast Banner Slider")
    app.setOrganizationName("CreeperAWA")
    app.setOrganizationDomain("github.com/CreeperAWA")
    app.setQuitOnLastWindowClosed(False)

    # 设置 Windows 应用程序 User Model ID
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("ToastBannerSlider")
    except Exception as e:
        logger.warning(f"设置应用程序User Model ID失败: {e}")

    # 加载配置
    config = load_config()

    # 此时所有依赖项都已准备就绪，可以安全创建主管理器
    # 注意：许可证验证已在程序启动初期完成，此处无需重复验证
    manager = ToastBannerManager(app, config)
    exit_code = manager.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()