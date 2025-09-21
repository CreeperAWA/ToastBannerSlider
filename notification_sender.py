"""通知发送模块

该模块用于发送Windows Toast通知，主要用于测试目的。
通过winsdk库创建并发送Toast通知到Windows通知中心。
"""

import winsdk.windows.ui.notifications as notifications
import winsdk.windows.data.xml.dom as dom
import sys
from loguru import logger


# 配置日志
def setup_logger():
    """配置日志输出格式"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO"
    )


# 常量定义
APP_ID = "QQ"  # 应用程序AUMID
TOAST_TITLE = "912 窗户卡子群"  # 通知标题
TOAST_CONTENT = "我们班的窗户阻窗器不知道被哪个同学拔了，这个我已经告诉了后勤老师，你们班的我看也是这样，这个我已经告诉后勤老师了，这个还是非常的危险啊！"  # 通知内容


def create_toast_xml(title: str, content: str) -> str:
    """创建Toast通知的XML内容
    
    Args:
        title: 通知标题
        content: 通知内容
        
    Returns:
        格式化的XML字符串
    """
    return f"""
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{title}</text>
            <text>{content}</text>
        </binding>
    </visual>
</toast>
"""


def send_toast_notification(title: str, content: str, app_id: str = APP_ID):
    """发送Toast通知
    
    Args:
        title: 通知标题
        content: 通知内容
        app_id: 应用程序AUMID，默认为QQ
    """
    try:
        # 创建并加载XML文档
        xml_doc = dom.XmlDocument()
        toast_xml = create_toast_xml(title, content)
        xml_doc.load_xml(toast_xml)
        
        # 创建通知对象
        toast = notifications.ToastNotification(xml_doc)
        
        # 获取通知管理器并发送通知
        toast_notifier = notifications.ToastNotificationManager.create_toast_notifier(app_id)
        toast_notifier.show(toast)
        
        logger.info("Toast 横幅通知已发送！")
        
    except Exception as e:
        logger.error(f"发送Toast通知失败: {e}")
        raise


def main():
    """主函数 - 发送测试通知"""
    setup_logger()
    send_toast_notification(TOAST_TITLE, TOAST_CONTENT)


if __name__ == "__main__":
    main()