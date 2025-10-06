"""图标资源管理模块

该模块负责处理应用程序中使用的各种图标资源，提供统一的图标加载和管理功能。
"""

import os
import sys
import uuid
from PySide6.QtGui import QIcon
from logger_config import logger
from typing import Optional, Dict, Any


def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径，兼容打包后的程序
    
    Args:
        relative_path (str): 相对路径
        
    Returns:
        str: 资源文件的绝对路径
    """
    # 获取可执行文件所在目录
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Nuitka单文件模式，资源在临时目录中
        base_path = sys._MEIPASS
    elif getattr(sys, 'frozen', False):
        # 其他打包模式
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境，使用__file__获取当前文件目录
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    # 构建完整路径
    full_path = os.path.join(base_path, relative_path)
    logger.debug(f"资源路径解析: {relative_path} -> {full_path}")
    return full_path


def get_icons_dir() -> Optional[str]:
    """获取图标目录路径
    
    Returns:
        str: 图标目录的绝对路径，如果创建失败则返回None
    """
    # 使用与配置模块相同的方式获取基础目录，避免Nuitka单文件模式下保存到临时文件夹
    if getattr(sys, 'frozen', False):
        # 打包后的程序
        config_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境，使用sys.argv[0]而不是__file__
        config_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
    # 构建图标目录路径
    icons_dir = os.path.join(config_dir, "icons")
    
    # 确保图标目录存在
    if not os.path.exists(icons_dir):
        try:
            os.makedirs(icons_dir)
            logger.debug(f"创建图标目录: {icons_dir}")
        except Exception as e:
            logger.error(f"创建图标目录失败: {e}")
            return None
            
    logger.debug(f"图标目录路径: {icons_dir}")
    return icons_dir


def save_custom_icon(icon_path: str) -> Optional[str]:
    """保存自定义图标，使用UUID重命名以避免冲突
    
    Args:
        icon_path (str): 原始图标文件路径
        
    Returns:
        str: 保存后的图标文件名（仅文件名），失败时返回None
    """
    try:
        if not icon_path or not os.path.exists(icon_path):
            logger.warning(f"图标文件不存在或路径无效: {icon_path}")
            return None
            
        # 获取图标目录
        icons_dir = get_icons_dir()
        if not icons_dir:
            logger.error("无法获取图标目录")
            return None
            
        # 获取文件扩展名
        _, ext = os.path.splitext(icon_path)
        if not ext:
            ext = ".png"  # 默认扩展名
            
        # 生成UUID文件名
        unique_filename = f"{uuid.uuid4()}{ext}"
        target_path = os.path.join(icons_dir, unique_filename)
        
        # 复制文件
        import shutil
        shutil.copy2(icon_path, target_path)
        
        logger.debug(f"图标文件已保存: {icon_path} -> {target_path}")
        return unique_filename
    except Exception as e:
        logger.error(f"保存自定义图标时出错: {e}")
        return None


def load_icon(config: Optional[Dict[str, Any]] = None) -> QIcon:
    """加载图标
    
    Args:
        config (dict, optional): 配置字典
        
    Returns:
        QIcon: 加载的图标，如果失败则返回空图标
    """
    try:
        logger.debug("开始加载图标")
        
        # 如果提供了配置且包含自定义图标设置，则优先加载自定义图标
        if config and "custom_icon" in config:
            custom_icon_filename = config.get("custom_icon")
            if custom_icon_filename:
                # 确保custom_icon_filename是字符串类型
                custom_icon_filename = str(custom_icon_filename)
                icons_dir = get_icons_dir()
                if icons_dir:
                    icon_path = os.path.join(icons_dir, custom_icon_filename)
                    logger.debug(f"尝试加载自定义图标: {icon_path}")
                    if os.path.exists(icon_path):
                        icon = QIcon(icon_path)
                        if not icon.isNull():
                            logger.debug(f"成功加载自定义图标: {icon_path}")
                            return icon
                        else:
                            logger.warning(f"自定义图标文件无效: {icon_path}")
                    else:
                        logger.warning(f"自定义图标文件不存在: {icon_path}")
                else:
                    logger.warning("无法获取图标目录")
            else:
                logger.debug("配置中custom_icon为空")
        else:
            logger.debug("配置中无自定义图标设置")
        
        # 如果没有自定义图标或加载失败，使用默认图标
        try:
            resource_icon_path = get_resource_path("notification_icon.ico")
            logger.debug(f"尝试加载资源图标: {resource_icon_path}")
            if os.path.exists(resource_icon_path):
                icon = QIcon(resource_icon_path)
                if not icon.isNull():
                    logger.debug(f"成功加载资源图标: {resource_icon_path}")
                    return icon
                else:
                    logger.warning(f"资源图标文件无效: {resource_icon_path}")
            else:
                logger.warning(f"资源图标文件不存在: {resource_icon_path}")
        except Exception as e:
            logger.debug(f"无法从资源加载图标: {e}")
            
        # 尝试使用notification_icon.png作为后备
        try:
            resource_icon_path = get_resource_path("notification_icon.png")
            logger.debug(f"尝试加载PNG资源图标: {resource_icon_path}")
            if os.path.exists(resource_icon_path):
                icon = QIcon(resource_icon_path)
                if not icon.isNull():
                    logger.debug(f"成功加载PNG资源图标: {resource_icon_path}")
                    return icon
                else:
                    logger.warning(f"PNG资源图标文件无效: {resource_icon_path}")
            else:
                logger.warning(f"PNG资源图标文件不存在: {resource_icon_path}")
        except Exception as e:
            logger.debug(f"无法从PNG资源加载图标: {e}")
            
        # 尝试使用系统主题图标作为后备
        system_icon = QIcon.fromTheme("application-x-executable")
        if not system_icon.isNull():
            logger.debug("成功加载系统默认图标")
            return system_icon
            
        logger.warning("无法加载任何图标，返回空图标")
        return QIcon()
        
    except Exception as e:
        logger.error(f"加载图标时发生异常: {e}")
        return QIcon()