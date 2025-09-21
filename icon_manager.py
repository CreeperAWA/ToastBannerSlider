"""图标资源管理模块

该模块负责处理应用程序中使用的各种图标资源，提供统一的图标加载和管理功能。
"""

import os
import sys
from PyQt5.QtGui import QIcon
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


def load_icon(icon_name="notification_icon.png"):
    """加载图标资源
    
    Args:
        icon_name (str): 图标文件名
        
    Returns:
        QIcon: 加载的图标对象，加载失败返回空图标
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