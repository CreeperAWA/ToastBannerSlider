"""警告横幅模块 (CPU版本)

该模块提供警告样式的横幅实现，用于显示重要警告信息。
此版本专为CPU渲染优化，不使用GPU加速。
"""

from PySide6.QtWidgets import QWidget, QApplication, QLabel
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QPixmap, QMouseEvent, QPolygon, QPaintEvent, QShowEvent
from config import load_config
from typing import Dict, Union, Optional
from keyword_replacer import process_text_with_html  # 确保导入process_text_with_html


class WarningBanner(QWidget):
    """顶部警示横幅 (CPU渲染版本)"""
    
    # 定义窗口关闭信号
    window_closed = Signal(object)

    def __init__(self, text: str = "", y_offset: int = 0):
        super().__init__()
        self.setFixedHeight(140)  # 横幅高度
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 置顶、无边框
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )

        # 消息文本 - 处理文本中的关键字替换并生成HTML格式
        processed_text = process_text_with_html(text) if text else ""
        self.text: str = processed_text if processed_text else ""
        self.text_y_offset: int = y_offset
        
        # 加载配置
        self.config: Dict[str, Union[str, float, int, bool, None]] = load_config()
        
        # 点击次数和关闭阈值
        self.click_count: int = 0
        self.click_to_close: int = int(self.config.get("click_to_close", 3) or 3)  # 从配置中获取点击关闭次数

        # 条纹偏移量
        self.offset: int = 0

        # 设置窗口位置和大小
        self._set_initial_position()

        # 创建消息文本标签
        self.message_text: Optional[QLabel] = None
        self.text_width: int = 0
        self._create_message_text()

        # 生成斜纹
        self.stripe = QPixmap(40, 32)
        self.stripe.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self.stripe)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿
        painter.setBrush(QColor(255, 222, 89, 200))
        painter.setPen(Qt.PenStyle.NoPen)
        polygon = QPolygon([
            QPoint(0, 32),
            QPoint(16, 0),
            QPoint(32, 0),
            QPoint(16, 32)
        ])
        painter.drawPolygon(polygon)
        painter.end()

        # 滚动动画参数
        self.scroll_count: int = 0
        self.max_scrolls: int = int(self.config.get("scroll_count", 3) or 3)
        self.speed: float = float(self.config.get("scroll_speed", 200.0) or 200.0)  # 滚动速度 (px/s)
        self.space: int = int(self.config.get("right_spacing", 150) or 150)  # 右侧间隔距离
        self.scroll_mode: str = str(self.config.get("scroll_mode", "always") or "always")  # 滚动模式
        
        # 垂直动画
        self.vertical_animation: Optional[QPropertyAnimation] = None
        
        # 初始化动画
        self.stripe_timer: Optional[QTimer] = None
        self.text_animation: Optional[QPropertyAnimation] = None
        self.fade_in: Optional[QPropertyAnimation] = None
        self.fade_out: Optional[QPropertyAnimation] = None
        self._setup_animations()
        
        # 添加关闭状态标志，防止重复关闭
        self._is_closing: bool = False
        
    def _setup_animations(self) -> None:
        """设置动画"""
        # 条纹滚动定时器
        self.stripe_timer = QTimer(self)
        if self.stripe_timer:
            self.stripe_timer.timeout.connect(self._update_stripe_animation)
            self.stripe_timer.start(16)
        
        # 文本滚动动画
        if self.message_text:
            # 根据滚动模式决定是否滚动
            if self.scroll_mode == "never":
                # 文本居中显示
                screen_width = QApplication.primaryScreen().geometry().width()
                self.message_text.move((screen_width - self.text_width) // 2, (self.height() - self.text_height) // 2)
            elif self.scroll_mode == "auto" and self.text_width <= QApplication.primaryScreen().geometry().width():
                # 文本居中显示
                screen_width = QApplication.primaryScreen().geometry().width()
                self.message_text.move((screen_width - self.text_width) // 2, (self.height() - self.text_height) // 2)
            else:
                # 计算滚动距离和持续时间
                screen_width = QApplication.primaryScreen().geometry().width()
                scroll_distance = self.text_width + screen_width + self.space
                scroll_duration = (scroll_distance / self.speed) * 1000  # 转换为毫秒
                
                self.text_animation = QPropertyAnimation(self.message_text, b"pos")
                self.text_animation.setDuration(int(scroll_duration))
                self.text_animation.setStartValue(QPoint(screen_width, (self.height() - self.text_height) // 2))
                self.text_animation.setEndValue(QPoint(-(self.text_width + self.space), (self.height() - self.text_height) // 2))
                self.text_animation.setEasingCurve(QEasingCurve.Type.Linear)
                if self.text_animation:
                    self.text_animation.finished.connect(self._on_text_animation_finished)
        
        # 淡入动画
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        if self.fade_in:
            self.fade_in.setDuration(int(self.config.get("fade_animation_duration", 1500) or 1500))
            self.fade_in.setStartValue(0.0)
            self.fade_in.setEndValue(1.0)
            self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # 淡出动画
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        if self.fade_out:
            self.fade_out.setDuration(int(self.config.get("fade_animation_duration", 1500) or 1500))
            self.fade_out.setStartValue(1.0)
            self.fade_out.setEndValue(0.0)
            self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.fade_out.finished.connect(self._on_fade_out_finished)
        
    def _set_initial_position(self) -> None:
        """设置初始窗口位置"""
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().availableGeometry()
        
        # 获取基础垂直偏移量
        base_vertical_offset = int(self.config.get("base_vertical_offset", 0) or 0)
        total_offset = base_vertical_offset + self.text_y_offset
        
        # 设置窗口位置和宽度
        self.setGeometry(
            0,
            total_offset,
            screen.width(),
            140
        )
        
    def _create_message_text(self) -> None:
        """创建消息文本标签"""
        # 创建消息文本
        self.message_text = QLabel(self)
        self.message_text.setFont(QFont(["HarmonyOS Sans SC", "Microsoft YaHei UI", "sans-serif"], pointSize=36, weight=QFont.Weight.Bold))
        self.message_text.setStyleSheet("color: #FFDE59; background: transparent;")
        self.message_text.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.message_text.setWordWrap(False)
        self.message_text.setTextFormat(Qt.TextFormat.RichText)  # 支持富文本
        
        # 处理关键字替换并生成HTML格式文本
        html_text = process_text_with_html(self.text) if self.text else ""
        self.message_text.setText(html_text)
        
        # 设置文本标签的位置和尺寸
        if self.message_text:
            # 使用sizeHint来正确计算富文本的实际显示尺寸
            self.text_width = self.message_text.sizeHint().width() if html_text else 0
            self.text_height = self.message_text.sizeHint().height()
            
            # 获取屏幕宽度
            screen_width = QApplication.primaryScreen().geometry().width()
            
            # 获取滚动模式配置
            scroll_mode = self.config.get("scroll_mode", "always")  # 默认为"always"
            
            # 根据滚动模式决定是否启动动画
            if scroll_mode == "always":
                # 不论如何都滚动
                should_scroll = True
            elif scroll_mode == "auto":
                # 可以展示完全的不滚动
                # 对于警告样式横幅，使用屏幕宽度作为参考
                should_scroll = self.text_width > screen_width * 0.8  # 当文本宽度超过屏幕宽度的80%时滚动
            else:
                should_scroll = True  # 默认滚动
            
            if should_scroll:
                # 确保最小宽度为屏幕宽度，以便长文本可以完全滚动
                calculated_width = max(self.text_width, screen_width)
                self.message_text.setGeometry(0, 0, calculated_width, 140)
                # 初始位置在右侧不可见
                self.message_text.move(screen_width, 0)
            else:
                # 文本不滚动，居中显示
                self.message_text.setGeometry(0, 0, screen_width, 140)
                self.message_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.message_text.hide()  # 隐藏消息文本，防止旧内容闪现

    def _init_text_animation(self) -> None:
        """初始化文本动画"""
        # 获取屏幕宽度
        screen_width = QApplication.primaryScreen().geometry().width()
        
        # 获取滚动模式配置
        scroll_mode = self.config.get("scroll_mode", "always")  # 默认为"always"
        
        # 根据滚动模式决定是否启动动画
        if scroll_mode == "always":
            # 不论如何都滚动
            should_scroll = True
        elif scroll_mode == "auto":
            # 可以展示完全的不滚动
            # 对于警告样式横幅，使用屏幕宽度作为参考
            should_scroll = self.text_width > screen_width * 0.8  # 当文本宽度超过屏幕宽度的80%时滚动
        else:
            should_scroll = True  # 默认滚动
        
        message_text = self.message_text
        if message_text is not None:
            if should_scroll:
                scroll_distance = self.text_width + screen_width + self.space
                scroll_duration = (scroll_distance / self.speed) * 1000  # 转换为毫秒
                
                self.text_animation = QPropertyAnimation(message_text, b"pos")
                self.text_animation.setDuration(int(scroll_duration))
                self.text_animation.setStartValue(QPoint(screen_width, 0))
                self.text_animation.setEndValue(QPoint(-(self.text_width + self.space), 0))
                self.text_animation.setEasingCurve(QEasingCurve.Type.Linear)
                if self.text_animation:
                    self.text_animation.finished.connect(self._on_text_animation_finished)
            else:
                # 不滚动时不需要设置动画
                # 文本居中显示
                message_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
                message_text.move((screen_width - self.text_width) // 2, (self.height() - self.text_height) // 2)
                if self.text_animation:
                    self.text_animation.stop()
                    self.text_animation = None