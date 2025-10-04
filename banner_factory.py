"""横幅工厂模块

该模块提供工厂方法，用于根据配置创建不同样式的横幅。
"""

from typing import Union, Dict, Optional
from notice_slider import NotificationWindow
from warning_banner import WarningBanner
from config import load_config


def create_banner(message: str = "", vertical_offset: int = 0, max_scrolls: Optional[int] = None) -> Union[NotificationWindow, WarningBanner]:
    """根据配置创建横幅实例
    
    Args:
        message (str, optional): 要显示的消息内容
        vertical_offset (int): 垂直偏移量，用于多窗口显示
        max_scrolls (int, optional): 最大滚动次数，如果为None则使用配置文件中的设置
        
    Returns:
        Union[NotificationWindow, WarningBanner]: 横幅实例
    """
    # 加载配置
    config: Dict[str, Union[str, float, int, bool, None]] = load_config()
    
    # 获取横幅样式配置
    banner_style = config.get("banner_style", "default")
    
    # 根据样式创建对应的横幅实例
    if banner_style == "warning":
        # 创建警告样式横幅
        banner = WarningBanner(text=message, y_offset=vertical_offset)
        return banner
    else:
        # 创建默认样式横幅
        banner = NotificationWindow(message=message, vertical_offset=vertical_offset, max_scrolls=max_scrolls)
        return banner