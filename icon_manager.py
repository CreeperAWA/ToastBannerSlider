"""图标资源管理模块

该模块负责处理应用程序中使用的各种图标资源，提供统一的图标加载和管理功能。
"""

import os
import sys
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
from loguru import logger


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


def get_icons_dir():
    """获取图标目录路径
    
    Returns:
        str: 图标目录的绝对路径
    """
    # 使用可执行文件所在目录
    icons_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "icons")
    
    # 确保目录存在
    if not os.path.exists(icons_dir):
        try:
            os.makedirs(icons_dir)
            logger.info(f"创建图标目录: {icons_dir}")
        except Exception as e:
            logger.error(f"创建图标目录失败: {e}")
            
    return icons_dir


def load_icon(icon_name="notification_icon.png"):
    """加载图标资源
    
    Args:
        icon_name (str): 图标文件名
        
    Returns:
        QIcon: 加载的图标对象，加载失败返回空图标
    """
    # 首先尝试从配置中加载自定义图标
    from config import load_config
    config = load_config()
    custom_icon = config.get("custom_icon")
    
    if custom_icon:
        # 尝试加载自定义图标
        custom_icon_path = os.path.join(get_icons_dir(), custom_icon)
        logger.debug(f"尝试加载自定义图标：{custom_icon}，路径：{custom_icon_path}")
        
        if os.path.exists(custom_icon_path):
            pixmap = QPixmap(custom_icon_path)
            if not pixmap.isNull():
                # 缩放图标以避免锯齿
                scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon = QIcon(scaled_pixmap)
                if not icon.isNull():
                    logger.info(f"使用自定义图标：{custom_icon_path}")
                    return icon
            logger.warning(f"自定义图标文件无效：{custom_icon_path}")
    
    # 如果没有自定义图标或者加载失败，使用默认图标
    icon_path = get_resource_path(icon_name)
    logger.debug(f"尝试加载默认图标：{icon_name}，路径：{icon_path}")
    
    if os.path.exists(icon_path):
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            # 缩放图标以避免锯齿
            scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon = QIcon(scaled_pixmap)
            if not icon.isNull():
                return icon
        logger.warning(f"默认图标文件无效：{icon_path}")
    
    # 如果指定图标加载失败，尝试加载默认图标
    default_icon_path = get_resource_path("default_icon.png")
    if os.path.exists(default_icon_path):
        default_pixmap = QPixmap(default_icon_path)
        if not default_pixmap.isNull():
            # 缩放图标以避免锯齿
            scaled_default_pixmap = default_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            default_icon = QIcon(scaled_default_pixmap)
            if not default_icon.isNull():
                logger.info(f"使用默认图标替代：{default_icon_path}")
                return default_icon
    
    logger.error("无法加载任何图标资源")
    return QIcon()  # 返回空图标