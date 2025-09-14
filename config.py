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

CONFIG_FILE = "config.json"

def load_config():
    """
    加载配置文件，如果不存在则创建默认配置
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 确保所有必需的键都存在
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            logger.debug("配置文件加载成功")
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
    """
    保存配置到文件
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logger.info("配置已保存")
        return True
    except Exception as e:
        logger.error(f"保存配置文件时出错：{e}")
        return False