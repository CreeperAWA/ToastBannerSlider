"""Windows Toast通知监听模块

该模块负责监听Windows系统的Toast通知，并解析特定标题的通知内容。
通过访问Windows通知数据库来捕获通知，并将解析后的内容传递给回调函数。
"""

import sqlite3
import base64
import xml.etree.ElementTree as ET
import os
import time
import json
import sys
from datetime import datetime
from config import load_config
from loguru import logger

# 配置loguru日志格式
logger.remove()
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
logger.add("toast_banner_slider_listener.log", rotation="5 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="DEBUG")


# 全局变量用于存储通知回调函数和目标标题
_notification_callback = None
_target_title = None


def set_notification_callback(callback):
    """设置通知回调函数
    
    Args:
        callback (function): 当捕获到通知时调用的回调函数
    """
    global _notification_callback
    _notification_callback = callback


class NotificationListener:
    """通知监听器类"""
    
    def __init__(self):
        """初始化通知监听器"""
        self.target_title = None
        global _listener_instance
        _listener_instance = self
    
    def set_target_title(self, title):
        """设置监听的目标标题
        
        Args:
            title (str): 要监听的目标标题
        """
        old_title = self.target_title
        self.target_title = title
        if old_title != title:
            logger.info(f"监听标题已更新，从 '{old_title}' 更改为 '{title}'")
    
    def get_target_title(self):
        """获取当前监听的目标标题
        
        Returns:
            str: 当前监听的目标标题
        """
        return self.target_title


def get_listener():
    """获取监听器实例
    
    Returns:
        NotificationListener: 监听器实例
    """
    global _listener_instance
    return _listener_instance


def update_target_title(new_title):
    """更新监听的目标标题
    
    Args:
        new_title (str): 新的目标标题
    """
    listener = get_listener()
    if listener:
        listener.set_target_title(new_title)


def get_wpndatabase_path():
    """获取 Windows 通知数据库的路径
    
    Returns:
        str: Windows通知数据库的完整路径
        
    Raises:
        EnvironmentError: 当无法找到LOCALAPPDATA环境变量时抛出
    """
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        raise EnvironmentError("无法找到 LOCALAPPDATA 环境变量")
    
    db_path = os.path.join(local_app_data, 'Microsoft', 'Windows', 'Notifications', 'wpndatabase.db')
    return db_path


def decode_payload(payload):
    """解码 base64 编码的通知载荷
    
    Args:
        payload (str): base64编码的载荷字符串
        
    Returns:
        str: 解码后的字符串，失败时返回None
    """
    try:
        decoded_bytes = base64.b64decode(payload)
        decoded_str = decoded_bytes.decode('utf-8')
        return decoded_str
    except Exception as e:
        logger.error(f"解码载荷时出错：{e}")
        return None


def parse_notification_xml(xml_content):
    """解析通知 XML 内容，提取标题和内容
    
    Args:
        xml_content (str): XML格式的通知内容
        
    Returns:
        tuple: (标题, 内容)的元组，解析失败时返回(None, None)
    """
    try:
        root = ET.fromstring(xml_content)
        binding = root.find('.//binding[@template="ToastGeneric"]')
        if binding is not None:
            texts = binding.findall('text')
            if len(texts) >= 2:
                title = texts[0].text
                content = texts[1].text
                # 将多行文本替换为单行文本，用空格连接
                if content:
                    content = " ".join(content.splitlines())
                return title, content
        return None, None
    except Exception as e:
        logger.error(f"解析 XML 时出错：{e}")
        return None, None


def listen_for_notifications(check_interval=5):
    """监听指定标题的 Windows Toast 通知
    
    Args:
        check_interval (int): 检查通知数据库的间隔时间（秒）
    """
    # 创建监听器实例
    listener = NotificationListener()
    
    db_path = get_wpndatabase_path()
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"未找到通知数据库：{db_path}")
    
    last_check_time = int(time.time() * 10000000) + 116444736000000000  # 转换为 Windows FILETIME 格式

    # 加载配置
    config = load_config()
    target_title = config.get("notification_title", "911 呼唤群")
    listener.set_target_title(target_title)
    
    logger.info(f"开始监听标题为 '{target_title}' 的 Windows Toast 通知...")
    logger.info(f"数据库路径：{db_path}")
    logger.info("按 Ctrl+C 停止监听")
    
    # 用于避免重复通知的集合
    processed_notifications = set()
    
    try:
        while True:
            try:
                # 使用监听器中的目标标题
                target_title = listener.get_target_title()
                
                # 连接到数据库
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 查询 Toast 类型的通知（使用实际的表结构）
                query = """
                SELECT Id, Type, Payload, ArrivalTime
                FROM Notification
                WHERE Type = 'toast'
                AND ArrivalTime > ?
                ORDER BY ArrivalTime DESC
                """
                
                cursor.execute(query, (last_check_time,))
                notifications = cursor.fetchall()
                
                # 更新检查时间
                last_check_time = int(time.time() * 10000000) + 116444736000000000  # 转换为 Windows FILETIME 格式
                
                for notification in notifications:
                    notification_id, notification_type, payload, arrival_time = notification
                    
                    # 避免处理重复通知
                    if notification_id in processed_notifications:
                        continue
                    
                    processed_notifications.add(notification_id)
                    
                    # 解码载荷
                    if payload is None:
                        continue
                        
                    try:
                        # payload 是 BLOB 类型，需要先解码
                        payload_str = base64.b64encode(payload).decode('utf-8')
                        xml_content = decode_payload(payload_str)
                    except Exception as e:
                        logger.error(f"处理载荷时出错：{e}")
                        continue
                        
                    if not xml_content:
                        continue
                    
                    # 解析 XML 内容
                    title, content = parse_notification_xml(xml_content)
                    
                    # 筛选指定标题的通知
                    if title == target_title and content:
                        # 输出通知内容供其他程序使用
                        result = {
                            "timestamp": datetime.now().isoformat(),
                            "title": title,
                            "content": content,
                            "arrival_time": arrival_time
                        }
                        
                        logger.info(f"收到通知 - 标题：{title}，内容：{content}")
                        
                        # 如果设置了回调函数，则调用它
                        if notification_callback:
                            notification_callback(content)
                        else:
                            # 否则输出 JSON 格式，便于其他程序解析
                            print(json.dumps(result, ensure_ascii=False))
                            # 确保立即输出
                            sys.stdout.flush()
                
                conn.close()
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logger.warning("数据库被锁定，等待下次检查...")
                else:
                    logger.error(f"数据库操作错误：{e}")
            except Exception as e:
                logger.error(f"处理通知时出错：{e}")
            
            # 等待下次检查
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("停止监听")


if __name__ == "__main__":
    listen_for_notifications()