"""横幅工厂模块

该模块提供工厂方法，用于根据配置创建不同样式的横幅。
"""

from typing import Union, Dict, Optional
from notice_slider import NotificationWindow
from warning_banner_cpu import WarningBanner as WarningBannerCPU
from warning_banner_gpu import WarningBanner as WarningBannerGPU
from config import load_config


def create_banner(message: str = "", vertical_offset: int = 0, max_scrolls: Optional[int] = None) -> Union[NotificationWindow, WarningBannerCPU, WarningBannerGPU]:
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
    
    # 处理换行符：对于警告样式，将换行符替换为空格
    processed_message = message
    if banner_style == "warning":
        processed_message = " ".join(message.splitlines())
    
    # 根据样式创建对应的横幅实例
    if banner_style == "warning":
        # 获取渲染后端配置
        rendering_backend: str = str(config.get("rendering_backend", "default"))
        
        # 根据渲染后端选择对应的WarningBanner版本
        if rendering_backend in ["opengl", "opengles"]:
            # 使用GPU渲染版本
            banner = WarningBannerGPU(text=processed_message, y_offset=vertical_offset)
        else:
            # 使用CPU渲染版本
            banner = WarningBannerCPU(text=processed_message, y_offset=vertical_offset)
        return banner
    else:
        # 创建默认样式横幅
        banner = NotificationWindow(message=processed_message, vertical_offset=vertical_offset, max_scrolls=max_scrolls)
        return banner