"""配置管理模块

该模块负责管理应用程序的配置，包括加载、保存和提供默认配置。
所有其他模块都应该通过这个模块来获取和修改配置。
"""

import json
import os
import sys
from typing import Dict, Union


# 默认配置
DEFAULT_CONFIG: Dict[str, Union[str, float, int, bool, None]] = {
    "notification_title": "911 呼唤群",
    "scroll_speed": 200.0,           # 滚动速度（像素/秒）
    "scroll_count": 3,               # 滚动次数
    "click_to_close": 3,             # 点击关闭次数
    "right_spacing": 150,            # 右侧间距
    "font_size": 48.0,               # 字体大小
    "left_margin": 93,               # 左边距
    "right_margin": 93,              # 右边距
    "icon_scale": 1.0,               # 图标缩放比例
    "label_offset_x": 0,             # 文字水平偏移
    "window_height": 128,            # 窗口高度
    "label_mask_width": 305,         # 文字遮罩宽度
    "banner_spacing": 10,            # 横幅间距
    "shift_animation_duration": 100, # 移动动画持续时间
    "fade_animation_duration": 1500, # 淡入淡出动画持续时间
    "base_vertical_offset": 50,      # 基础垂直偏移
    "banner_opacity": 0.9,           # 横幅透明度
    "log_level": "INFO",             # 日志等级
    "scroll_mode": "always",         # 滚动模式: always(总是滚动), auto(自动), never(从不滚动)
    "ignore_duplicate": False,       # 忽略重复通知
    "do_not_disturb": False,         # 免打扰模式
    "custom_icon": None              # 自定义图标文件名
}


def get_config_path() -> str:
    """获取配置文件路径
    
    Returns:
        str: 配置文件的绝对路径
    """
    if getattr(sys, 'frozen', False):
        # 打包后的程序
        config_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境，使用sys.argv[0]而不是__file__
        config_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
    return os.path.join(config_dir, "config.json")


def load_config() -> Dict[str, Union[str, float, int, bool, None]]:
    """加载配置
    
    Returns:
        dict: 配置字典
    """
    config_path = get_config_path()
    
    # 如果配置文件不存在，创建默认配置文件
    if not os.path.exists(config_path):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 合并配置，确保所有必需的键都存在
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        
        return merged_config
    except Exception:
        # 如果读取配置文件失败，返回默认配置
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Union[str, float, int, bool, None]]) -> bool:
    """保存配置
    
    Args:
        config (dict): 要保存的配置字典
        
    Returns:
        bool: 保存成功返回True，失败返回False
    """
    try:
        config_path = get_config_path()
        
        # 确保配置目录存在
        config_dir = os.path.dirname(config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        # 保存配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
            
        return True
    except Exception:
        return False


# 导出默认配置供其他模块使用
__all__ = ['DEFAULT_CONFIG', 'load_config', 'save_config', 'get_config_path']