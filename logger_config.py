"""日志配置模块

该模块负责统一管理应用程序的日志配置。
所有其他模块都应该从这里导入logger对象并使用。
"""

from loguru import logger
import sys
import os
from config import get_config_path
from typing import Optional, Dict, Union


def setup_logger(config: Optional[Dict[str, Union[str, float, int, bool, None]]] = None) -> str:
    """根据配置设置日志记录器
    
    Args:
        config (dict, optional): 配置字典
        
    Returns:
        str: 日志级别
    """
    # 如果没有提供配置，则加载配置
    if config is None:
        # 避免循环导入，动态导入config模块
        from config import load_config
        config = load_config()
    
    # 获取日志等级，默认为INFO
    log_level = config.get("log_level", "INFO") if config else "INFO"
    if log_level is None:
        log_level = "INFO"
    
    # 移除现有的所有处理器
    logger.remove()
    
    # 添加标准错误输出处理器
    logger.add(sys.stderr, 
              format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", 
              level=str(log_level))  # 终端使用配置的日志级别
    
    # 添加文件输出处理器，5MB轮转
    # 获取配置文件所在目录作为日志文件目录
    config_dir = os.path.dirname(get_config_path())
    log_file_path = os.path.join(config_dir, "toast_banner_slider.log")
    
    logger.add(log_file_path, 
              rotation="5 MB", 
              format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", 
              level=str(log_level))
    
    logger.debug(f"日志记录器已配置，等级: {log_level}")
    return str(log_level)


# 导出logger对象供其他模块使用
# 注意：请在主程序中调用 setup_logger() 进行初始化
__all__ = ['logger', 'setup_logger']