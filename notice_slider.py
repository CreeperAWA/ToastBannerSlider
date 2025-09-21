"""通知横幅显示模块

该模块负责创建和显示顶部通知横幅窗口，实现文字滚动动画和用户交互功能。
"""

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QHBoxLayout, 
                           QDesktopWidget, QSizePolicy)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
import os
from config import load_config
from loguru import logger

# 配置loguru日志格式
logger.remove()
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
logger.add("toast_banner_slider_slider.log", rotation="5 MB", 
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="DEBUG")


class NotificationWindow(QWidget):
    """顶部通知窗口 - 实现消息滚动显示和交互功能"""
    
    # 定义窗口关闭信号
    window_closed = pyqtSignal(object)
    
    def __init__(self, message=None, vertical_offset=0):
        """初始化通知窗口
        
        Args:
            message (str, optional): 要显示的消息内容
            vertical_offset (int): 垂直偏移量，用于多窗口显示
        """
        super().__init__()
        # 加载配置
        config = load_config()
        
        # 初始化消息和滚动参数
        # 将多行文本替换为单行文本，用空格连接
        initial_message = message or "这是一条测试消息，用于验证通知显示功能是否正常工作。消息长度可能会变化，需要确保滚动效果正确。"
        self.message = " ".join(initial_message.splitlines())
        
        self.scroll_count = 0
        self.max_scrolls = config.get("scroll_count", 3)  # 从配置中获取最大滚动次数
        self.animation = None
        self.text_width = 0
        self.speed = config.get("scroll_speed", 200.0)  # 从配置中获取滚动速度 (px/s)
        self.space = config.get("right_spacing", 150)  # 从配置中获取右侧间隔距离
        self.font_size = config.get("font_size", 48.0)   # 从配置中获取字体大小
        self.left_margin = config.get("left_margin", 93)   # 从配置中获取左侧边距
        self.right_margin = config.get("right_margin", 93) # 从配置中获取右侧边距
        self.icon_scale = config.get("icon_scale", 1.0)      # 从配置中获取图标缩放倍数
        self.label_offset_x = config.get("label_offset_x", 0)  # 从配置中获取标签文本x轴偏移
        self.window_height = config.get("window_height", 128)  # 从配置中获取窗口高度
        self.label_mask_width = config.get("label_mask_width", 305)  # 从配置中获取标签遮罩宽度
        self.vertical_offset = vertical_offset  # 垂直偏移量
        self.vertical_animation = None  # 垂直位置动画
        self.fade_in = None  # 淡入动画
        self.fade_out = None  # 淡出动画

        # 初始化点击交互参数
        self.click_count = 0
        self.click_to_close = config.get("click_to_close", 3)  # 从配置中获取触发关闭的点击次数

        # 初始化UI和动画
        self.init_ui()
        self.setup_animation()
        logger.debug(f"创建通知窗口，消息内容：{self.message}")

    def _create_icon_label(self) -> QLabel:
        """创建图标标签控件
        
        Returns:
            QLabel: 包含喇叭图标的标签
        """
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notification_icon.png")
        icon_size = int(48 * self.icon_scale)  # 根据配置的缩放倍数调整图标大小
        
        # 尝试加载自定义图标，如果失败则使用文本图标
        try:
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path).scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                icon_label.setPixmap(pixmap)
            else:
                icon_label.setText("🔊")
                icon_label.setFont(QFont("Arial", int(32 * self.icon_scale)))
        except Exception as e:
            logger.warning(f"加载图标失败: {e}")
            icon_label.setText("🔊")
            icon_label.setFont(QFont("Arial", int(32 * self.icon_scale)))
            
        icon_label.setStyleSheet("color: white; background: transparent;")
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return icon_label

    def _create_label_widget(self) -> QWidget:
        """创建标签部件（包含图标和文本）
        
        Returns:
            QWidget: 标签部件
        """
        # 创建标签容器
        label_widget = QWidget()
        label_widget.setFixedWidth(self.label_mask_width)
        label_widget.setStyleSheet("background: transparent;")
        
        # 设置布局
        label_layout = QHBoxLayout(label_widget)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(5)
        
        # 创建并添加图标
        icon_label = self._create_icon_label()
        label_layout.addWidget(icon_label)
        
        # 创建并添加标签文本
        label_text = QLabel("消息提醒：")
        label_text.setFont(QFont("Microsoft YaHei", int(self.font_size // 2)))  # 根据配置的字体大小调整
        label_text.setStyleSheet("color: #3b9fdc; background: transparent;")
        label_text.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        label_text.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # 应用标签文本的x轴偏移
        if self.label_offset_x != 0:
            label_text.setStyleSheet(f"color: #3b9fdc; background: transparent; margin-left: {self.label_offset_x}px;")
            
        label_layout.addWidget(label_text)
        label_layout.addStretch()
        
        return label_widget

    def _create_message_text(self, screen_width: int) -> QLabel:
        """创建消息文本控件
        
        Args:
            screen_width (int): 屏幕宽度，用于计算布局
            
        Returns:
            QLabel: 消息文本标签
        """
        # 创建消息文本
        message_text = QLabel(self.message)
        message_text.setFont(QFont("Microsoft YaHei", int(self.font_size // 2)))  # 使用配置的字体大小
        message_text.setStyleSheet("color: white; background: transparent;")
        message_text.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        message_text.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        message_text.setWordWrap(False)
        
        # 设置文本标签的高度与父容器一致
        message_text.setGeometry(0, 0, 1000, self.window_height)  # 使用配置的高度
        message_text.setMinimumHeight(self.window_height)
        message_text.setMaximumHeight(self.window_height)
        
        return message_text

    def init_ui(self):
        """初始化用户界面组件"""
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        
        # 窗口基本设置
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setGeometry(0, 50 + self.vertical_offset, screen_width, self.window_height)

        # 主容器 - 使用样式表实现半透明背景
        self.main_content = QWidget(self)
        self.main_content.setGeometry(0, 0, screen_width, self.window_height)
        self.main_content.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 153);
                border: none;
            }
        """)

        # 主布局
        layout = QHBoxLayout(self.main_content)
        layout.setContentsMargins(self.left_margin, 0, self.right_margin, 0)  # 使用配置的左右边距
        layout.setSpacing(0)
        
        # 创建并添加标签部件
        label_widget = self._create_label_widget()
        layout.addWidget(label_widget)

        # 创建消息容器
        self.message_container = QWidget()
        self.message_container.setStyleSheet("background: transparent;")
        self.message_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.message_container.setFixedHeight(self.window_height)  # 使用配置的高度

        # 创建消息滑动区域
        self.message_slider_box = QWidget(self.message_container)
        slider_width = screen_width - self.left_margin - self.label_mask_width - self.right_margin  # 使用配置的宽度计算可用宽度
        self.message_slider_box.setGeometry(0, 0, slider_width, self.window_height)  # 使用配置的高度
        self.message_slider_box.setStyleSheet("background: transparent;")

        # 创建消息文本
        self.message_text = self._create_message_text(screen_width)
        self.message_text.setParent(self.message_slider_box)
        
        # 隐藏消息文本，防止旧内容闪现
        self.message_text.hide()

        # 添加到主布局
        layout.addWidget(self.message_container)

        # 启动淡入动画
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
        # 在设置好位置和尺寸后再显示文本
        self.message_text.show()
        
        # 计算滚动参数
        scroll_distance = screen_width + self.text_width + self.space
        scroll_duration = (scroll_distance / self.speed) * 1000  # 转换为毫秒

        # 创建动画 - 垂直居中位置保持一致
        if self.animation:
            self.animation.stop()
            self.animation.deleteLater()
            
        self.animation = QPropertyAnimation(self.message_text, b"pos")
        self.animation.setDuration(int(scroll_duration))
        self.animation.setStartValue(QPoint(screen_width - self.left_margin - self.label_mask_width - self.right_margin, 0))  # 使用配置的边距
        self.animation.setEndValue(QPoint(-(self.text_width + self.space), 0))  # 滚动到左侧，y=0
        self.animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.animation.finished.connect(self.animation_completed)
        self.animation.start()
        logger.debug(f"启动滚动动画，持续时间：{int(scroll_duration)} 毫秒")
        
    def update_vertical_offset(self, offset, animation_duration=100):
        """更新窗口的垂直偏移量，带动画效果
        
        Args:
            offset (int): 新的垂直偏移量
            animation_duration (int): 动画持续时间（毫秒）
        """
        # 如果已有垂直动画在运行，先停止它
        if self.vertical_animation and self.vertical_animation.state() == QPropertyAnimation.State.Running:
            self.vertical_animation.stop()
            self.vertical_animation.deleteLater()
            
        # 创建垂直位置动画
        self.vertical_animation = QPropertyAnimation(self, b"geometry")
        self.vertical_animation.setDuration(animation_duration)  # 使用配置的动画时间
        self.vertical_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 获取当前屏幕宽度
        screen_width = QDesktopWidget().screenGeometry().width()
        
        # 设置起始和结束几何位置
        current_geometry = self.geometry()
        target_geometry = current_geometry.adjusted(0, offset - self.vertical_offset, 0, offset - self.vertical_offset)
        
        self.vertical_animation.setStartValue(current_geometry)
        self.vertical_animation.setEndValue(target_geometry)
        self.vertical_animation.start()
        
        # 更新垂直偏移量
        self.vertical_offset = offset
        
    def animation_completed(self):
        """处理动画完成后的逻辑，包括循环滚动或关闭窗口"""
        self.scroll_count += 1
        logger.debug(f"动画完成，当前滚动次数：{self.scroll_count}/{self.max_scrolls}")
        if self.scroll_count >= self.max_scrolls:
            # 淡出并关闭
            if self.fade_out:
                self.fade_out.stop()
                self.fade_out.deleteLater()
                
            self.fade_out = QPropertyAnimation(self, b"windowOpacity")
            self.fade_out.setDuration(500)
            self.fade_out.setStartValue(1)
            self.fade_out.setEndValue(0)
            self.fade_out.finished.connect(self.close)  # type: ignore
            self.fade_out.start()
            logger.debug("通知显示完成，开始淡出")
        else:
            # 重置位置并重新开始动画
            screen_width = QDesktopWidget().screenGeometry().width()
            self.message_text.move(screen_width - self.left_margin - self.label_mask_width - self.right_margin, 0)  # 使用配置的边距
            self.animation.start()

    def mousePressEvent(self, event):
        """处理鼠标点击事件，支持多次点击关闭功能
        
        Args:
            event (QMouseEvent): 鼠标点击事件
        """
        self.click_count += 1
        logger.debug(f"通知窗口被点击，点击次数：{self.click_count}/{self.click_to_close}")

        if self.click_count >= self.click_to_close:
            self.close_notification()
        # 不调用父类的mousePressEvent，避免可能的闪烁问题
        # super().mousePressEvent(event)

    def close_notification(self):
        """启动关闭动画，实现窗口淡出效果"""
        logger.info("用户点击关闭通知")
        # 如果已有淡出动画在运行，先停止它
        if self.fade_out and self.fade_out.state() == QPropertyAnimation.State.Running:
            self.fade_out.stop()
            self.fade_out.deleteLater()
            
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(self.windowOpacity())
        self.fade_out.setEndValue(0)
        self.fade_out.finished.connect(self.close)  # type: ignore
        self.fade_out.start()
        
    def closeEvent(self, event):
        """处理窗口关闭事件
        
        Args:
            event (QCloseEvent): 窗口关闭事件
        """
        # 停止所有动画并释放资源
        if self.animation:
            self.animation.stop()
            self.animation.deleteLater()
            
        if self.vertical_animation:
            self.vertical_animation.stop()
            self.vertical_animation.deleteLater()
            
        if self.fade_in:
            self.fade_in.stop()
            self.fade_in.deleteLater()
            
        if self.fade_out:
            self.fade_out.stop()
            self.fade_out.deleteLater()
        
        # 发出窗口关闭信号
        self.window_closed.emit(self)
        super().closeEvent(event)

    def __del__(self):
        """析构函数，确保资源被释放"""
        logger.debug("NotificationWindow 对象被销毁")


def main():
    """主函数 - 用于测试通知窗口显示"""
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