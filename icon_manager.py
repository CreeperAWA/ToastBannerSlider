"""图标资源管理模块

该模块负责处理应用程序中使用的各种图标资源，提供统一的图标加载和管理功能。
"""

import os
import sys
from PySide6.QtGui import QIcon, QPixmap, Qt
from PySide6.QtCore import QCoreApplication
from loguru import logger


def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容打包后的程序
    
    Args:
        relative_path (str): 相对路径
        
    Returns:
        str: 资源文件的绝对路径
    """
    # 获取可执行文件所在目录
    if getattr(sys, 'frozen', False):
        # 打包后的程序
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    # 构建完整路径
    full_path = os.path.join(base_path, relative_path)
    logger.debug(f"资源路径解析: {relative_path} -> {full_path}")
    return full_path


def get_icons_dir():
    """获取图标目录路径
    
    Returns:
        str: 图标目录的绝对路径
    """
    # 获取可执行文件所在目录
    if getattr(sys, 'frozen', False):
        # 打包后的程序
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    # 构建图标目录路径
    icons_dir = os.path.join(base_path, "icons")
    
    # 确保图标目录存在
    if not os.path.exists(icons_dir):
        try:
            os.makedirs(icons_dir)
            logger.info(f"创建图标目录: {icons_dir}")
        except Exception as e:
            logger.error(f"创建图标目录失败: {e}")
            return base_path  # 返回基础路径作为备选
            
    logger.debug(f"图标目录路径: {icons_dir}")
    return icons_dir


def load_icon(icon_name="notification_icon.png"):
    """加载图标文件
    
    Args:
        icon_name (str): 图标文件名，默认为notification_icon.png
        
    Returns:
        QIcon: 加载的图标对象，加载失败时返回空图标
    """
    # 首先尝试加载自定义图标
    custom_icon = None
    try:
        from config import load_config
        config = load_config()
        custom_icon_name = config.get("custom_icon")
        if custom_icon_name:
            custom_icon_path = os.path.join(get_icons_dir(), custom_icon_name)
            if os.path.exists(custom_icon_path):
                custom_icon = QIcon(custom_icon_path)
                if custom_icon.isNull():
                    logger.warning(f"自定义图标加载失败: {custom_icon_path}")
                    custom_icon = None
                else:
                    logger.debug(f"成功加载自定义图标: {custom_icon_path}")
    except Exception as e:
        logger.warning(f"加载自定义图标时出错: {e}")
        
    # 如果有自定义图标且有效，直接返回
    if custom_icon and not custom_icon.isNull():
        return custom_icon
        
    # 尝试加载指定名称的图标
    icon_path = get_resource_path(icon_name)
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        if not icon.isNull():
            logger.debug(f"成功加载图标: {icon_path}")
            return icon
        else:
            logger.warning(f"图标文件加载失败: {icon_path}")
            
    # 如果指定名称的图标加载失败，尝试加载默认图标
    if icon_name != "notification_icon.png":
        default_icon_path = get_resource_path("notification_icon.png")
        if os.path.exists(default_icon_path):
            icon = QIcon(default_icon_path)
            if not icon.isNull():
                logger.debug(f"成功加载默认图标: {default_icon_path}")
                return icon
            else:
                logger.warning(f"默认图标文件加载失败: {default_icon_path}")
                
    # 如果所有图标都加载失败，返回空图标
    logger.warning("所有图标加载失败，返回空图标")
    return QIcon()