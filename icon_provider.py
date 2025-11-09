"""图标提供者模块

该模块为QML提供图标资源加载功能。
"""

from PySide6.QtCore import QObject, Slot
from icon_manager import load_icon
from typing import Dict, Union, Optional


class IconProvider(QObject):
    """为QML提供图标资源的类"""
    
    def __init__(self, config: Optional[Dict[str, Union[str, float, int, bool, None]]] = None):
        super().__init__()
        self.config = config or {}
    
    @Slot(result=str)
    def getIconPath(self) -> str:
        """获取图标路径
        
        Returns:
            str: 图标文件的QML URL路径
        """
        try:
            # 尝试加载图标
            icon = load_icon(self.config)
            if not icon.isNull():
                # 在QML中我们无法直接使用QIcon，需要获取实际的图片路径
                # 由于icon_manager已经处理了图标的加载，我们需要提供一个通用的图标路径
                return "qrc:/notification_icon.png"
            else:
                # 返回默认图标路径
                return ""
        except Exception:
            # 出现异常时返回空字符串
            return ""