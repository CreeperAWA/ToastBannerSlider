"""警告横幅模块 (CPU版本)

该模块提供警告样式的横幅实现，用于显示重要警告信息。
此版本专为CPU渲染优化，不使用GPU加速。
"""

from PySide6.QtWidgets import QWidget, QApplication, QLabel
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QPixmap, QMouseEvent, QPolygon, QPaintEvent, QShowEvent
from config import load_config
from typing import Dict, Union, Optional


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

        # 消息文本
        self.text: str = text if text else ""
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
        
    def _set_initial_position(self) -> None:
        """设置初始位置和大小"""
        # 获取屏幕信息
        primary_screen = QApplication.primaryScreen()
        screen_geometry = primary_screen.geometry()
        screen_width = screen_geometry.width()
        
        # 获取基础垂直偏移量
        base_vertical_offset = int(self.config.get("base_vertical_offset", 0) or 0)
        total_offset = base_vertical_offset + self.text_y_offset
        
        # 设置窗口位置和大小
        self.setGeometry(0, total_offset, screen_width, 140)
        
    def _create_message_text(self) -> None:
        """创建消息文本标签"""
        # 创建消息文本
        self.message_text = QLabel(self.text, self)
        self.message_text.setFont(QFont(["HarmonyOS Sans SC", "Microsoft YaHei UI", "sans-serif"], pointSize=36, weight=QFont.Weight.Bold))
        self.message_text.setStyleSheet("color: #FFDE59; background: transparent;")
        self.message_text.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.message_text.setWordWrap(False)
        
        # 设置文本标签的位置和尺寸
        if self.message_text:
            # 动态计算文本宽度
            fm = self.message_text.fontMetrics()
            self.text_width = fm.horizontalAdvance(self.text)
            # 确保最小宽度为屏幕宽度，以便长文本可以完全滚动
            screen_width = QApplication.primaryScreen().geometry().width()
            calculated_width = max(self.text_width, screen_width)
            
            self.message_text.setGeometry(0, 0, calculated_width, 140)
            # 初始位置在右侧不可见
            self.message_text.move(screen_width, 0)
            self.message_text.hide()  # 隐藏消息文本，防止旧内容闪现

    def update_vertical_offset(self, new_offset: int) -> None:
        """更新垂直偏移量
        
        Args:
            new_offset (int): 新的垂直偏移量
        """
        # 获取基础垂直偏移量
        base_vertical_offset = int(self.config.get("base_vertical_offset", 0) or 0)
        total_offset = base_vertical_offset + new_offset
        
        # 创建垂直位置动画
        if self.vertical_animation:
            self.vertical_animation.stop()
            self.vertical_animation.deleteLater()
            
        self.vertical_animation = QPropertyAnimation(self, b"pos")
        self.vertical_animation.setDuration(int(self.config.get("shift_animation_duration", 100) or 100))  # 使用配置的动画时间
        self.vertical_animation.setStartValue(self.pos())
        self.vertical_animation.setEndValue(QPoint(0, total_offset))
        self.vertical_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        if self.vertical_animation:
            self.vertical_animation.start()
        
    def _setup_animations(self) -> None:
        """设置动画"""
        # 条纹滚动定时器
        self.stripe_timer = QTimer(self)
        if self.stripe_timer:
            self.stripe_timer.timeout.connect(self._update_stripe_animation)
            self.stripe_timer.start(16)
        
        # 文本滚动动画
        if self.message_text:
            # 计算滚动距离和持续时间
            screen_width = QApplication.primaryScreen().geometry().width()
            scroll_distance = self.text_width + screen_width + self.space
            scroll_duration = (scroll_distance / self.speed) * 1000  # 转换为毫秒
            
            self.text_animation = QPropertyAnimation(self.message_text, b"pos")
            self.text_animation.setDuration(int(scroll_duration))
            self.text_animation.setStartValue(QPoint(screen_width, 0))
            self.text_animation.setEndValue(QPoint(-(self.text_width + self.space), 0))
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
        
    def _update_stripe_animation(self) -> None:
        """更新条纹动画"""
        self.offset = (self.offset + 1) % self.stripe.width()
        self.update()
        
    def _on_text_animation_finished(self) -> None:
        """文本动画完成处理"""
        self.scroll_count += 1
        if self.scroll_count >= self.max_scrolls:
            # 达到最大滚动次数，关闭横幅
            self.close_banner()
        else:
            # 重置位置并重新开始动画
            screen_width = QApplication.primaryScreen().geometry().width()
            if self.message_text:
                self.message_text.move(screen_width, 0)
                if self.text_animation:
                    self.text_animation.start()
        
    def showEvent(self, event: QShowEvent) -> None:
        """窗口显示事件，启动淡入动画和文本滚动"""
        super().showEvent(event)
        # 显示消息文本
        if self.message_text:
            self.message_text.show()
        # 开始淡入动画
        if self.fade_in:
            self.fade_in.start()
        # 开始文本滚动动画
        if self.text_animation:
            self.text_animation.start()
        
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """处理鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.click_count += 1
            if self.click_count >= self.click_to_close:
                self.close_banner()
        super().mousePressEvent(event)
        
    def close_banner(self) -> None:
        """关闭横幅"""
        if not self._is_closing:
            self._is_closing = True
            # 启动淡出动画
            if self.fade_out:
                self.fade_out.start()
        
    def _on_fade_out_finished(self) -> None:
        """淡出动画完成后的处理"""
        # 停止条纹动画和其他动画
        if self.stripe_timer:
            self.stripe_timer.stop()
        if self.text_animation:
            self.text_animation.stop()
        self.close()
        self.window_closed.emit(self)
        
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿

        # 背景橙色
        painter.fillRect(self.rect(), QColor(228, 8, 10, 180))

        # 顶部条纹
        y = 0
        x = -self.offset
        while x < self.width():
            painter.drawPixmap(x, y, self.stripe)
            x += self.stripe.width()

        # 分割线（条纹下边缘）
        painter.setPen(QPen(QColor(255, 222, 89, 200), 4))
        painter.drawLine(0, self.stripe.height(), self.width(), self.stripe.height())

        # 底部条纹
        y = self.height() - self.stripe.height()
        x = -self.offset
        while x < self.width():
            painter.drawPixmap(x, y, self.stripe)
            x += self.stripe.width()

        # 分割线（条纹上边缘）
        painter.drawLine(0, y, self.width(), y)
        
        # 确保在退出前结束绘制
        painter.end()