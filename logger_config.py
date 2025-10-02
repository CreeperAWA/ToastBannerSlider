"""日志配置模块

该模块负责统一管理应用程序的日志配置。
所有其他模块都应该从这里导入logger对象并使用。
"""

from loguru import logger
import sys
import os
from typing import Optional, Dict, Union


def get_base_path() -> str:
    """获取应用程序基础路径
    
    Returns:
        str: 应用程序基础路径
    """
    if getattr(sys, 'frozen', False):
        # Nuitka打包后的程序
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境，使用sys.argv[0]而不是__file__
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return base_path


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
    
    # 获取基础路径
    base_path = get_base_path()
    frozen = getattr(sys, 'frozen', False)
    
    logger.debug(f"sys.frozen: {frozen}")
    logger.debug(f"sys.executable: {sys.executable}")
    logger.debug(f"sys.argv[0]: {sys.argv[0]}")
    logger.debug(f"基础路径: {base_path}")
    logger.debug(f"当前工作目录: {os.getcwd()}")
    
    # 构建日志文件路径
    log_file_path = os.path.join(base_path, "toast_banner_slider.log")
    logger.debug(f"日志文件路径: {log_file_path}")
    
    # 确保日志目录存在
    try:
        os.makedirs(base_path, exist_ok=True)
        logger.debug(f"确保日志目录存在: {base_path}")
    except Exception as e:
        logger.error(f"创建日志目录失败: {e}")
    
    # 尝试创建一个测试文件来检查写入权限
    test_file_path = os.path.join(base_path, "test_write_permission.txt")
    try:
        with open(test_file_path, "w") as f:
            f.write("Test write permission")
        os.remove(test_file_path)
        logger.debug("写入权限检查通过")
    except Exception as e:
        logger.error(f"写入权限检查失败: {e}")
    
    try:
        logger.add(log_file_path, 
                  rotation="5 MB", 
                  format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", 
                  level=str(log_level))
        logger.debug(f"日志文件处理器添加成功")
    except Exception as e:
        logger.error(f"添加日志文件处理器失败: {e}")
        # 尝试使用当前工作目录作为备选方案
        fallback_log_path = os.path.join(os.getcwd(), "toast_banner_slider.log")
        logger.debug(f"尝试备选日志路径: {fallback_log_path}")
        try:
            logger.add(fallback_log_path,
                      rotation="5 MB",
                      format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
                      level=str(log_level))
            logger.debug(f"备选日志文件处理器添加成功")
            log_file_path = fallback_log_path
        except Exception as e2:
            logger.error(f"备选日志文件处理器也失败了: {e2}")
    
    logger.debug(f"日志记录器已配置，等级: {log_level}，文件路径: {log_file_path}")
    return str(log_level)


# 导出logger对象供其他模块使用
# 注意：请在主程序中调用 setup_logger() 进行初始化
__all__ = ['logger', 'setup_logger']