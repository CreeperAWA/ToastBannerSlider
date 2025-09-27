"""配置管理模块

该模块负责加载和保存应用程序的配置信息。
"""

import json
import os
import sys
from loguru import logger

# 配置loguru日志格式
logger.remove()

def setup_logger(config=None):
    """根据配置设置日志记录器
    
    Args:
        config (dict, optional): 配置字典
        
    Returns:
        str: 日志级别
    """
    # 如果没有提供配置，则加载配置
    if config is None:
        config = load_config()
    
    # 获取日志等级，默认为INFO
    log_level = config.get("log_level", "INFO")
    
    return log_level

# 默认配置
DEFAULT_CONFIG = {
    "notification_title": "911 呼唤群",
    "scroll_speed": 200.0,        # 滚动速度可以是浮点数
    "scroll_count": 3,            # 滚动次数为整数
    "click_to_close": 3,          # 点击关闭次数为整数
    "right_spacing": 150,         # 右侧间隔为像素值，整数
    "font_size": 48.0,            # 字体大小可以是浮点数
    "left_margin": 93,            # 左边距为像素值，整数
    "right_margin": 93,           # 右边距为像素值，整数
    "icon_scale": 1.0,            # 图标缩放倍数为浮点数
    "label_offset_x": 0,          # 标签文本x轴偏移为像素值，整数
    "window_height": 128,         # 窗口高度为像素值，整数
    "label_mask_width": 305,      # 标签遮罩宽度为像素值，整数
    "banner_spacing": 10,         # 横幅间隔为像素值，整数
    "ignore_duplicate": False,    # 是否忽略重复通知
    "shift_animation_duration": 100,       # 通知上移动画持续时间 (ms) - 整数
    "do_not_disturb": False,               # 免打扰模式 - 布尔值
    "fade_animation_duration": 1500,       # 淡入淡出动画持续时间 (ms) - 整数
    "base_vertical_offset": 0,             # 基础垂直偏移量 - 整数
    "log_level": "INFO"                    # 日志等级 - 字符串 (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
}


def get_config_path():
    """获取配置文件的路径，兼容打包后的程序
    
    Returns:
        str: 配置文件的路径
    """
    # 统一使用可执行文件所在目录
    config_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    config_path = os.path.join(config_dir, "config.json")
    logger.debug(f"配置文件路径: {config_path}")
    return config_path


def load_config():
    """加载配置文件，如果不存在则创建默认配置
    
    Returns:
        dict: 配置字典，包含所有配置项
    """
    CONFIG_FILE = get_config_path()
    logger.debug(f"尝试加载配置文件: {CONFIG_FILE}")
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 确保所有必需的键都存在
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            logger.info("配置文件加载成功")
            # 设置日志记录器
            setup_logger(config)
            return config
        except Exception as e:
            logger.error(f"读取配置文件时出错：{e}")
            # 即使配置读取失败，也要设置日志记录器
            setup_logger(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    else:
        # 如果配置文件不存在，创建默认配置文件
        save_config(DEFAULT_CONFIG)
        logger.info("创建默认配置文件")
        # 设置日志记录器
        setup_logger(DEFAULT_CONFIG)
        return DEFAULT_CONFIG


def save_config(config):
    """保存配置到文件
    
    Args:
        config (dict): 要保存的配置字典
        
    Returns:
        bool: 保存成功返回True，失败返回False
    """
    CONFIG_FILE = get_config_path()
    logger.debug(f"尝试保存配置文件: {CONFIG_FILE}")
    
    try:
        # 确保目录存在
        config_dir = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logger.info("配置已保存")
        # 重新设置日志记录器（包括日志等级）
        setup_logger(config)
        return True
    except Exception as e:
        logger.error(f"保存配置文件时出错：{e}")
        return False
