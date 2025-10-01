"""ToastBannerSlider主程序

该模块整合了通知监听和显示功能，提供系统托盘图标和用户交互界面。
负责管理整个应用程序的生命周期，包括配置管理、通知监听和显示等核心功能。
"""

import sys
import time
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject
from notice_slider import NotificationWindow
from config import load_config, get_config_path
from logger_config import logger, setup_logger
from tray_manager import TrayManager
from notification_listener import NotificationListenerThread
from config_dialog import ConfigDialog
from send_notification_dialog import SendNotificationDialog
from typing import Optional, List, Tuple, Dict, Union, Callable


# 程序启动时立即初始化日志系统
config = load_config()
setup_logger(config)


class ConfigWatcher(QObject):
    """配置文件观察者 - 监听配置文件变化并发出信号"""
    
    def __init__(self) -> None:
        super().__init__()
        self.config_path = get_config_path()
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
        current_mtime = self._get_mtime()
        if current_mtime > self.last_mtime:
            self.last_mtime = current_mtime
            # 发出配置更改信号（通过调用回调函数实现）
            if hasattr(self, 'config_changed_callback') and self.config_changed_callback:
                self.config_changed_callback()


class ToastBannerManager(QObject):
    """Toast横幅通知管理器 - 控制整个应用程序的生命周期和核心功能"""
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """初始化Toast横幅管理器"""
        super().__init__(parent)
        logger.info("正在启动ToastBannerSlider...")
        
        # 创建Qt应用程序实例
        app_instance = QApplication.instance()
        if app_instance is not None:
            self.app = app_instance
        else:
            self.app = QApplication(sys.argv)
        
        # 初始化成员变量
        self.notification_windows: List[NotificationWindow] = []  # 存储当前显示的通知窗口
        self.last_notification: Optional[str] = None   # 存储最后一条通知内容
        self.config_watcher: Optional[ConfigWatcher] = None
        self.config_timer: Optional[QTimer] = None
        self.listener_thread: Optional[NotificationListenerThread] = None
        self.tray_manager: Optional[TrayManager] = None
        self._send_dialog: Optional[SendNotificationDialog] = None  # 用于保持发送通知对话框的引用
        self.message_history: List[Tuple[str, float]] = []
        self.has_notifications: bool = False
        self.config: Dict[str, Union[str, float, int, bool, None]] = {}
        
        # 初始化UI
        self.init_ui()
        
        logger.info("ToastBannerSlider初始化完成")
        
    def init_ui(self) -> None:
        """初始化用户界面"""
        # 初始化消息历史记录和通知状态
        self.message_history = []
        self.has_notifications = False
        
        # 创建并启动配置文件观察者
        self.config_watcher = ConfigWatcher()
        self.config_watcher.config_changed_callback = self.update_config
        self.config_timer = QTimer()
        self.config_timer.timeout.connect(self.config_watcher.check_config_change)
        self.config_timer.start(1000)  # 每秒检查一次配置文件变化
        
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
        
        # 延迟创建托盘图标，确保GUI环境完全初始化
        QTimer.singleShot(1000, self._delayed_create_tray_icon)  # 减少延迟时间
        
        # 加载初始配置
        self.config = load_config()
        
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
            logger.debug("创建NotificationWindow实例")
            window = NotificationWindow(message, vertical_offset=total_existing_height + total_spacing, max_scrolls=max_scrolls)
            logger.debug("NotificationWindow实例创建完成")
            
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
            window.window_closed.connect(self.remove_notification_window)
            
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
        logger.debug("准备显示配置对话框")
        # 确保不会因为对话框关闭而退出主程序
        # 使用类型注释忽略Pylance错误
        if hasattr(self.app, 'setQuitOnLastWindowClosed') and callable(getattr(self.app, 'setQuitOnLastWindowClosed', None)):
            self.app.setQuitOnLastWindowClosed(False)  # type: ignore
        old_title = str(self.config.get("notification_title", "911 呼唤群"))
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
        new_title = str(self.config.get("notification_title", "911 呼唤群"))
        if old_title != new_title and self.tray_manager:
            logger.info(f"配置已更新，监听标题从 '{old_title}' 更改为 '{new_title}'")
            # 更新托盘管理器中的监听标题
            self.tray_manager.update_tooltip(new_title)
    
    def update_config(self) -> None:
        """更新配置"""
        try:
            logger.debug("更新配置")
            # 重新加载配置
            self.config = load_config()
            logger.info("配置已更新")
            
            # 更新日志等级
            setup_logger(self.config)
            
            # 更新托盘管理器
            if self.tray_manager:
                self.tray_manager.update_config()
                
            # 更新所有现有的通知窗口
            for window in self.notification_windows:
                # 使用类型安全的方法调用update_config
                if hasattr(window, 'update_config'):
                    try:
                        window.update_config(self.config)  # type: ignore
                    except Exception:
                        pass
                    
        except Exception as e:
            logger.error(f"更新配置时出错：{e}")
    
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
                # 使用公共方法替代私有方法调用
                if hasattr(window, 'close'):
                    window.close()
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


def main() -> None:
    """主函数 - 程序入口点"""
    print("=" * 30)
    print("Toast 横幅通知系统")
    print("=" * 30)
    print("正在启动...")
    
    # 确保即使在无控制台模式下也能正确创建 QApplication
    app_instance = QApplication.instance()
    if not app_instance:
        app = QApplication(sys.argv)
    else:
        app = app_instance
    
    # 设置应用程序属性
    # 添加类型检查以避免Pylance错误
    if hasattr(app, 'setQuitOnLastWindowClosed') and callable(getattr(app, 'setQuitOnLastWindowClosed', None)):
        app.setQuitOnLastWindowClosed(False)  # type: ignore

    
    # 设置应用程序元信息
    if hasattr(app, 'setApplicationName') and callable(getattr(app, 'setApplicationName', None)):
        app.setApplicationName("ToastBannerSlider")  # type: ignore
    if hasattr(app, 'setApplicationDisplayName') and callable(getattr(app, 'setApplicationDisplayName', None)):
        app.setApplicationDisplayName("Toast Banner Slider")  # type: ignore
    if hasattr(app, 'setOrganizationName') and callable(getattr(app, 'setOrganizationName', None)):
        app.setOrganizationName("CreeperAWA")  # type: ignore
    if hasattr(app, 'setOrganizationDomain') and callable(getattr(app, 'setOrganizationDomain', None)):
        app.setOrganizationDomain("github.com/CreeperAWA")  # type: ignore
    
    # 设置Windows应用程序User Model ID，确保Toast通知显示正确的应用程序名称
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("ToastBannerSlider")
    except Exception as e:
        logger.warning(f"设置应用程序User Model ID失败: {e}")
    
    manager = ToastBannerManager()
    exit_code = manager.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()