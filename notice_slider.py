import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QHBoxLayout, 
                           QDesktopWidget, QSizePolicy)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PyQt5.QtGui import QFont, QPixmap
import os
from config import load_config
from loguru import logger

# 配置loguru日志格式
logger.remove()
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

class NotificationWindow(QWidget):
    """顶部通知窗口 - 实现消息滚动显示和交互功能"""
    
    def __init__(self, message=None):
        super().__init__()
        # 加载配置
        config = load_config()
        
        # 初始化消息和滚动参数
        self.message = message or "这是一条测试消息，用于验证通知显示功能是否正常工作。消息长度可能会变化，需要确保滚动效果正确。"
        self.scroll_count = 0
        self.max_scrolls = config.get("scroll_count", 3)  # 从配置中获取最大滚动次数
        self.animation = None
        self.text_width = 0
        self.speed = config.get("scroll_speed", 200)  # 从配置中获取滚动速度 (px/s)
        self.space = 150  # 消息右侧留白距离

        # 初始化点击交互参数
        self.click_count = 0
        self.click_to_close = config.get("click_to_close", 3)  # 从配置中获取触发关闭的点击次数

        # 初始化UI和动画
        self.init_ui()
        self.setup_animation()
        logger.debug(f"创建通知窗口，消息内容：{self.message}")

    def init_ui(self):
        """初始化 UI"""
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        
        # 窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setGeometry(0, 50, screen_width, 128)

        # 主容器 - 使用样式表实现渐变背景
        self.main_content = QWidget(self)
        self.main_content.setGeometry(0, 0, screen_width, 128)
        self.main_content.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 153);
                border: none;
            }
        """)

        # 布局
        layout = QHBoxLayout(self.main_content)
        layout.setContentsMargins(93, 0, 93, 0)  # 左边距 93px，右边距 93px
        layout.setSpacing(0)
        
        # 标签部分 - 固定宽度
        label_widget = QWidget()
        label_widget.setFixedWidth(305)
        label_widget.setStyleSheet("background: transparent;")
        
        label_layout = QHBoxLayout(label_widget)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(5)

        # 喇叭图标
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notification_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("🔊")
            icon_label.setFont(QFont("Arial", 32))
        icon_label.setStyleSheet("color: white; background: transparent;")
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)

        # 标签文本
        label_text = QLabel("消息提醒：")
        label_text.setFont(QFont("Microsoft YaHei", 24))
        label_text.setStyleSheet("color: #3b9fdc; background: transparent;")
        label_text.setAlignment(Qt.AlignVCenter)
        label_text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        label_layout.addWidget(icon_label)
        label_layout.addWidget(label_text)
        label_layout.addStretch()

        # 消息容器
        self.message_container = QWidget()
        self.message_container.setStyleSheet("background: transparent;")
        self.message_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.message_container.setFixedHeight(128)  # 设置固定高度

        # 消息滑动区域
        self.message_slider_box = QWidget(self.message_container)
        slider_width = screen_width - 93 - 305 - 93  # 计算可用宽度
        self.message_slider_box.setGeometry(0, 0, slider_width, 128)  # 高度与窗口一致
        self.message_slider_box.setStyleSheet("background: transparent;")

        # 消息文本
        self.message_text = QLabel(self.message)
        self.message_text.setParent(self.message_slider_box)
        self.message_text.setFont(QFont("Microsoft YaHei", 24))
        self.message_text.setStyleSheet("color: white; background: transparent;")
        self.message_text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.message_text.setAttribute(Qt.WA_TranslucentBackground)
        self.message_text.setWordWrap(False)
        
        # 关键修复：设置文本标签的高度与父容器一致
        self.message_text.setGeometry(0, 0, 1000, 128)  # 宽度先设大一些，后面会调整
        self.message_text.setMinimumHeight(128)
        self.message_text.setMaximumHeight(128)

        # 添加到主布局
        layout.addWidget(label_widget)
        layout.addWidget(self.message_container)

        # 淡入效果
        self.setWindowOpacity(0)
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.start()

    def setup_animation(self):
        """配置动画参数并启动滚动动画"""
        QTimer.singleShot(100, self._setup_animation_after_render)

    def _setup_animation_after_render(self):
        """在文本完成渲染后设置动画参数"""
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        
        # 确保文本大小已计算
        self.message_text.adjustSize()
        
        # 使用 fontMetrics 获取更准确的文本宽度
        fm = self.message_text.fontMetrics()
        self.text_width = fm.horizontalAdvance(self.message)
        
        if self.text_width == 0:
            self.text_width = 800  # 默认宽度

        # 重新设置文本标签的宽度以适应内容
        self.message_text.setFixedWidth(self.text_width)
        
        # 计算滚动参数
        scroll_distance = screen_width + self.text_width + self.space
        scroll_duration = (scroll_distance / self.speed) * 1000  # 转换为毫秒

        # 创建动画 - 垂直居中位置保持一致
        self.animation = QPropertyAnimation(self.message_text, b"pos")
        self.animation.setDuration(int(scroll_duration))
        self.animation.setStartValue(QPoint(screen_width - 93 - 305 - 93, 0))  # 从右侧开始，y=0
        self.animation.setEndValue(QPoint(-(self.text_width + self.space), 0))  # 滚动到左侧，y=0
        self.animation.setEasingCurve(QEasingCurve.Linear)
        self.animation.finished.connect(self.animation_completed)
        self.animation.start()
        logger.debug(f"启动滚动动画，持续时间：{int(scroll_duration)} 毫秒")

    def animation_completed(self):
        """处理动画完成后的逻辑，包括循环滚动或关闭窗口"""
        self.scroll_count += 1
        logger.debug(f"动画完成，当前滚动次数：{self.scroll_count}/{self.max_scrolls}")
        if self.scroll_count >= self.max_scrolls:
            # 淡出并关闭
            self.fade_out = QPropertyAnimation(self, b"windowOpacity")
            self.fade_out.setDuration(500)
            self.fade_out.setStartValue(1)
            self.fade_out.setEndValue(0)
            self.fade_out.finished.connect(self.close)
            self.fade_out.start()
            logger.debug("通知显示完成，开始淡出")
        else:
            # 重置位置并重新开始动画
            screen_width = QDesktopWidget().screenGeometry().width()
            self.message_text.move(screen_width - 93 - 305 - 93, 0)
            self.animation.start()

    def mousePressEvent(self, event):
        """处理鼠标点击事件，支持多次点击关闭功能"""
        self.click_count += 1
        logger.debug(f"通知窗口被点击，点击次数：{self.click_count}/{self.click_to_close}")

        if self.click_count >= self.click_to_close:
            self.close_notification()
        super().mousePressEvent(event)

    def close_notification(self):
        """启动关闭动画，实现窗口淡出效果"""
        logger.info("用户点击关闭通知")
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.finished.connect(self.close)
        self.fade_out.start()

def main():
    print("="*50)
    print("PyQt消息通知系统")
    print("功能：显示可交互的顶部消息通知横幅")
    print("="*50)
    print("正在启动通知窗口...")
    
    app = QApplication(sys.argv)
    window = NotificationWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()