"""通知发送模块

该模块用于发送Windows Toast通知，主要用于测试目的。
通过winsdk库创建并发送Toast通知到Windows通知中心。
"""

import winsdk.windows.ui.notifications as notifications
import winsdk.windows.data.xml.dom as dom
import sys
from loguru import logger

# 配置loguru日志格式
logger.remove()
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

# 获取应用的 Toast 通知管理器
toast_manager = notifications.ToastNotificationManager

# 使用应用程序 AUMID
app_id = "QQ"

# 创建通知的 XML 内容
toast_xml = f"""
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>912 窗户卡子群</text>
            <text>test1</text>
        </binding>
    </visual>
</toast>
"""

# 将 XML 字符串加载到 XmlDocument 对象中
xml_doc = dom.XmlDocument()
xml_doc.load_xml(toast_xml)

# 创建 ToastNotification 对象
toast = notifications.ToastNotification(xml_doc)

# 发送通知
toast_notifier = toast_manager.create_toast_notifier(app_id)
toast_notifier.show(toast)

logger.info("Toast 横幅通知已发送！")