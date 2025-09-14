"""配置管理模块

该模块负责加载和保存应用程序的配置信息。
"""

import json
import os
import sys
from loguru import logger

# 配置loguru日志格式
logger.remove()
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

# 默认配置
DEFAULT_CONFIG = {
    "notification_title": "911 呼唤群",
    "scroll_speed": 200,
    "scroll_count": 3,
    "click_to_close": 3,
    "right_spacing": 150
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
            return config
        except Exception as e:
            logger.error(f"读取配置文件时出错：{e}")
            return DEFAULT_CONFIG
    else:
        # 如果配置文件不存在，创建默认配置文件
        save_config(DEFAULT_CONFIG)
        logger.info("创建默认配置文件")
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
        logger.info(f"配置已保存到: {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"保存配置文件时出错：{e}")
        return False