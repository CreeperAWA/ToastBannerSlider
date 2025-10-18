"""警告横幅模块 (GPU版本)

该模块提供警告样式的横幅实现，用于显示重要警告信息。
此版本专为GPU渲染优化，使用QGraphicsView和QOpenGLWidget实现硬件加速。
"""

from PySide6.QtWidgets import (QWidget, QApplication, QLabel, QGraphicsView, 
                               QGraphicsScene, QGraphicsProxyWidget, QGraphicsRectItem,
                               QGraphicsPixmapItem)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (QFont, QPainter, QColor, QPen, QPixmap, QPolygon, QBrush, 
                          QShowEvent, QPaintEvent, QMouseEvent, QSurfaceFormat)
from logger_config import logger
from typing import Dict, Union, Optional
from config import load_config


class WarningBanner(QWidget):
    """顶部警示横幅 (GPU渲染版本)"""
    
    # 定义信号
    window_closed = Signal(object)  # 窗口关闭信号
    
    def __init__(self, text: str = "", y_offset: int = 0):
        super().__init__()
        
        # 初始化属性
        self.config: Dict[str, Union[str, int, float, bool, None]] = load_config()
        self.text = text if text else ""
        self.text_y_offset = y_offset
        
        # 安全地获取配置值，避免因 falsy 值（如 0）被替换为默认值
        speed_val = self.config.get("scroll_speed", 200.0)
        self.speed = float(speed_val if speed_val is not None else 200.0)
        
        space_val = self.config.get("right_spacing", 150)
        self.space = int(space_val if space_val is not None else 150)
        
        max_scrolls_val = self.config.get("scroll_count", 3)
        self.max_scrolls = int(max_scrolls_val if max_scrolls_val is not None else 3)
        
        click_to_close_val = self.config.get("click_to_close", 3)
        self.click_to_close = int(click_to_close_val if click_to_close_val is not None else 3)
        
        # 初始化UI组件属性
        self.message_text: Optional[QLabel] = None
        self.text_proxy: Optional[QGraphicsProxyWidget] = None
        self.graphics_view: Optional[QGraphicsView] = None
        self.scene: Optional[QGraphicsScene] = None
        self.stripe: Optional[QPixmap] = None
        self.stripe_items: list[QGraphicsPixmapItem] = []
        
        # 初始化动画属性
        self.stripe_timer: Optional[QTimer] = None
        self.text_animation: Optional[QPropertyAnimation] = None
        self.fade_in: Optional[QPropertyAnimation] = None
        self.fade_out: Optional[QPropertyAnimation] = None
        self.vertical_animation: Optional[QPropertyAnimation] = None
        
        # 初始化其他属性
        self.offset = 0
        self.scroll_count = 0
        self.click_count = 0
        self.text_width = 0
        self.text_height = 0  # 新增：文字高度
        self._is_closing = False
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self) -> None:
        """初始化用户界面"""
        # 获取屏幕信息
        primary_screen = QApplication.primaryScreen()
        screen_geometry = primary_screen.geometry()
        screen_width: int = screen_geometry.width()
        
        # 获取基础垂直偏移量
        base_vertical_offset: int = int(self.config.get("base_vertical_offset", 0) or 0)
        total_offset: int = base_vertical_offset + self.text_y_offset
        
        # 设置窗口位置和大小
        self.setGeometry(0, total_offset, screen_width, 140)
        
        # 置顶、无边框
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        # 启用窗口渲染优化
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        logger.debug("警告横幅已请求启用OpenGL渲染优化")
        
        # 检查窗口是否真的启用了原生渲染
        if self.testAttribute(Qt.WidgetAttribute.WA_NativeWindow):
            logger.debug("确认：警告横幅已成功启用OpenGL渲染优化")
        else:
            logger.warning("警告横幅请求启用OpenGL渲染优化但未生效")
        
        # 创建 QGraphicsView 以支持 GPU 渲染
        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setGeometry(0, 0, screen_width, 140)
        self.graphics_view.setStyleSheet("background: transparent; border: none;")
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.graphics_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.graphics_view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.graphics_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 设置OpenGL格式以支持透明度
        format = QSurfaceFormat()
        format.setAlphaBufferSize(8)  # 启用8位alpha通道
        format.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
        format.setSamples(4)  # 启用多重采样抗锯齿
        
        viewport = QOpenGLWidget()
        viewport.setFormat(format)
        viewport.setStyleSheet("background: transparent; border: none;")
        # 设置OpenGL视口的透明背景属性
        viewport.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # 启用OpenGL窗口优化
        viewport.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        # 设置OpenGL视口始终堆叠在顶部
        viewport.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        self.graphics_view.setViewport(viewport)
        
        self.graphics_view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.graphics_view.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.graphics_view.setOptimizationFlags(QGraphicsView.OptimizationFlag.DontSavePainterState | 
                                               QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing)
        
        # 创建场景
        self.scene = QGraphicsScene(0, 0, screen_width, 140)
        self.scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)
        self.graphics_view.setScene(self.scene)
        
        # 创建背景矩形项，使用配置的透明度 (与CPU版本一致: QColor(228, 8, 10, 180))
        background_color = QColor(228, 8, 10, 180)  # 保持与CPU版本一致
        background_rect = self.scene.addRect(0, 0, screen_width, 140, 
                                           QPen(Qt.PenStyle.NoPen), 
                                           QBrush(background_color))
        background_rect.setZValue(-1)  # 确保背景在最底层
        
        # 强制更新场景以确保透明度正确应用
        self.scene.update()
        
        # 创建消息文本
        self._create_message_text()
        
        # 创建条纹图案 (与CPU版本保持一致)
        self._create_stripe_pattern()
        
        # 设置动画
        self._setup_animations()
        
        # 设置点击事件处理器
        self._setup_click_handler()
        
    def _create_stripe_pattern(self) -> None:
        """创建条纹图案"""
        # 与CPU版本保持一致的条纹图案
        self.stripe = QPixmap(32, 32)
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
        
        # 在场景中添加条纹
        if self.scene:
            # 清空之前的条纹项
            self.stripe_items = []
            
            # 创建顶部条纹 (与CPU版本保持一致)
            x = -self.stripe.width()
            while x < self.scene.width():
                stripe_item = self.scene.addPixmap(self.stripe)
                stripe_item.setPos(x, 0)
                stripe_item.setZValue(1)
                self.stripe_items.append(stripe_item)
                x += self.stripe.width()
            
            # 创建底部条纹 (与CPU版本保持一致)
            x = -self.stripe.width()
            while x < self.scene.width():
                stripe_item = self.scene.addPixmap(self.stripe)
                stripe_item.setPos(x, self.scene.height() - self.stripe.height())
                stripe_item.setZValue(1)
                self.stripe_items.append(stripe_item)
                x += self.stripe.width()
            
            # 创建分割线 (与CPU版本保持一致)
            top_line = self.scene.addLine(0, self.stripe.height(), self.scene.width(), self.stripe.height(),
                                        QPen(QColor(255, 222, 89, 200), 4))
            top_line.setZValue(1)
            
            bottom_line = self.scene.addLine(0, self.scene.height() - self.stripe.height(), 
                                           self.scene.width(), self.scene.height() - self.stripe.height(),
                                           QPen(QColor(255, 222, 89, 200), 4))
            bottom_line.setZValue(1)
        
    def update_vertical_offset(self, new_offset: int) -> None:
        """更新垂直偏移量
        
        Args:
            new_offset (int): 新的垂直偏移量
        """
        # 获取基础垂直偏移量 (与CPU版本保持一致)
        base_vertical_offset = int(self.config.get("base_vertical_offset", 0) or 0)
        total_offset = base_vertical_offset + new_offset
        
        # 创建垂直位置动画 (与CPU版本保持一致)
        if self.vertical_animation:
            self.vertical_animation.stop()
            self.vertical_animation.deleteLater()
        
        # 重置引用
        self.vertical_animation = None
            
        # 创建新的动画实例
        self.vertical_animation = QPropertyAnimation(self, b"pos")
        self.vertical_animation.setDuration(int(self.config.get("shift_animation_duration", 100) or 100))  # 使用配置的动画时间
        self.vertical_animation.setStartValue(self.pos())
        self.vertical_animation.setEndValue(QPoint(0, total_offset))
        self.vertical_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 启动动画
        self.vertical_animation.start()

    def _create_message_text(self) -> None:
        """创建消息文本标签"""
        # 创建消息文本 (与CPU版本保持一致)
        self.message_text = QLabel(self.text)
        self.message_text.setFont(QFont(["HarmonyOS Sans SC", "Microsoft YaHei UI", "sans-serif"], pointSize=36, weight=QFont.Weight.Bold))
        self.message_text.setStyleSheet("color: #FFDE59; background: transparent;")
        self.message_text.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.message_text.setWordWrap(False)
        
        # 计算文本宽度和高度
        fm = self.message_text.fontMetrics()
        self.text_width = fm.horizontalAdvance(self.text)
        self.text_height = fm.height()  # 新增：获取文字高度
        
        if self.scene:
            # 创建文本代理并添加到场景
            self.text_proxy = QGraphicsProxyWidget()
            self.text_proxy.setWidget(self.message_text)
            self.scene.addItem(self.text_proxy)

    def _setup_animations(self) -> None:
        """设置动画"""
        # 条纹滚动定时器 (与CPU版本保持一致)
        self.stripe_timer = QTimer(self)
        if self.stripe_timer:
            self.stripe_timer.timeout.connect(self._update_stripe_animation)
            self.stripe_timer.start(16)
        
        # 计算垂直居中位置
        window_height = self.height()
        vertical_center_position = (window_height - self.text_height) // 2
        
        # 文本滚动动画 (与CPU版本保持一致)
        if self.text_proxy:
            # GPU渲染模式：使用代理部件
            screen_width: int = self.width()
            scroll_distance: float = float(self.text_width + screen_width + self.space)
            scroll_duration: float = (scroll_distance / self.speed) * 1000  # 转换为毫秒
            
            self.text_animation = QPropertyAnimation(self.text_proxy, b"pos")
            self.text_animation.setDuration(int(scroll_duration))
            self.text_animation.setStartValue(QPoint(screen_width, vertical_center_position))
            self.text_animation.setEndValue(QPoint(-(self.text_width + self.space), vertical_center_position))
            self.text_animation.setEasingCurve(QEasingCurve.Type.Linear)
            self.text_animation.finished.connect(self._on_text_animation_finished)
        
        # 淡入动画 (与CPU版本保持一致)
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        if self.fade_in:
            self.fade_in.setDuration(int(self.config.get("fade_animation_duration", 1500) or 1500))
            self.fade_in.setStartValue(0.0)
            self.fade_in.setEndValue(1.0)
            self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # 淡出动画 (与CPU版本保持一致)
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        if self.fade_out:
            self.fade_out.setDuration(int(self.config.get("fade_animation_duration", 1500) or 1500))
            self.fade_out.setStartValue(1.0)
            self.fade_out.setEndValue(0.0)
            self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.fade_out.finished.connect(self._on_fade_out_finished)
        
    def _update_stripe_animation(self) -> None:
        """更新条纹动画"""
        # 与CPU版本保持一致的条纹动画更新
        if self.stripe:
            self.offset = (self.offset + 1) % self.stripe.width()
            
        # 在GPU渲染模式下，更新场景中的条纹项位置
        if self.scene and hasattr(self, 'stripe_items') and self.stripe:
            # 更新所有条纹项的位置 (与CPU版本保持一致)
            for item in self.stripe_items:
                x_pos: float = item.pos().x()
                new_x: int = int(x_pos - 1)  # 与CPU版本保持一致的速度
                item.setPos(float(new_x), item.pos().y())
            
            # 动态管理条纹项，确保滚动时持续显示
            # 移除已经移出屏幕的条纹项
            items_to_remove: list[QGraphicsPixmapItem] = []
            for item in self.stripe_items:
                if item.pos().x() < -self.stripe.width():
                    items_to_remove.append(item)
            
            for item in items_to_remove:
                if self.scene and item:
                    self.scene.removeItem(item)
                if item in self.stripe_items:
                    self.stripe_items.remove(item)
            
            # 添加新的条纹项以填补空白
            if self.scene.width() > 0 and self.stripe:
                # 检查最右边的条纹项位置
                rightmost_x = -self.stripe.width()
                for item in self.stripe_items:
                    if item.pos().y() == 0 and item.pos().x() > rightmost_x:  # 顶部条纹
                        rightmost_x = item.pos().x()
                
                # 如果最右边的条纹项开始离开屏幕，添加新的条纹项
                while rightmost_x < self.scene.width():
                    # 添加顶部条纹
                    if self.stripe:
                        stripe_item = self.scene.addPixmap(self.stripe)
                        stripe_item.setPos(rightmost_x + self.stripe.width(), 0)
                        stripe_item.setZValue(1)
                        self.stripe_items.append(stripe_item)
                        
                        # 添加底部条纹
                        stripe_item = self.scene.addPixmap(self.stripe)
                        stripe_item.setPos(rightmost_x + self.stripe.width(), 
                                         self.scene.height() - self.stripe.height())
                        stripe_item.setZValue(1)
                        self.stripe_items.append(stripe_item)
                        
                        rightmost_x += self.stripe.width()
                    
            # 强制更新场景
            self.scene.update()
        
    def _on_text_animation_finished(self) -> None:
        """文本动画完成处理"""
        self.scroll_count += 1
        if self.scroll_count >= self.max_scrolls:
            # 达到最大滚动次数，关闭横幅
            self.close_banner()
        else:
            # GPU渲染模式：重置代理部件位置
            # 计算垂直居中位置
            window_height = self.height()
            vertical_center_position = (window_height - self.text_height) // 2
            if self.text_proxy:
                self.text_proxy.setPos(self.width(), vertical_center_position)
            
            if self.text_animation:
                # 确保动画状态正确再启动
                if self.text_animation.state() == QPropertyAnimation.State.Stopped:
                    self.text_animation.start()
        
    def showEvent(self, event: QShowEvent) -> None:
        """窗口显示事件，启动淡入动画和文本滚动"""
        super().showEvent(event)
        
        if self.graphics_view:
            # 显示 QGraphicsView 内容
            self.graphics_view.show()
            # 确保场景正确显示
            if self.scene and self.graphics_view:
                self.graphics_view.setScene(self.scene)
        
        # 开始淡入动画 (与CPU版本保持一致)
        if self.fade_in:
            self.fade_in.start()
        # 开始文本滚动动画 (与CPU版本保持一致)
        if self.text_animation:
            # 延迟启动动画以确保UI完全显示
            QTimer.singleShot(100, lambda: self.text_animation.start() if self.text_animation else None)
        
    def _setup_click_handler(self) -> None:
        """设置场景点击事件处理器"""
        if self.scene:
            # 创建一个覆盖整个场景的透明矩形项用于接收点击事件
            click_rect = QGraphicsRectItem(0, 0, self.width(), self.height())
            click_rect.setZValue(100)  # 置于最顶层以确保能接收到事件
            click_rect.setPen(Qt.PenStyle.NoPen)
            click_rect.setBrush(QColor(0, 0, 0, 1))  # 几乎完全透明的画刷
            
            # 重写矩形项的鼠标事件
            def mousePressEvent(item, event):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.click_count += 1
                    if self.click_count >= self.click_to_close:
                        self.close_banner()
                # 事件已处理，不向后传递
                event.accept()
            
            # 动态添加鼠标事件处理方法
            click_rect.mousePressEvent = lambda event: mousePressEvent(click_rect, event)
            self.scene.addItem(click_rect)
            
            # 确保场景可以接收鼠标事件
            click_rect.setAcceptHoverEvents(False)
            click_rect.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        
    def close_banner(self) -> None:
        """关闭横幅"""
        if not self._is_closing:
            self._is_closing = True
            # 启动淡出动画 (与CPU版本保持一致)
            if self.fade_out:
                self.fade_out.start()
        
    def _on_fade_out_finished(self) -> None:
        """淡出动画完成后的处理"""
        # 停止条纹动画和其他动画 (与CPU版本保持一致)
        if self.stripe_timer:
            self.stripe_timer.stop()
        if self.text_animation:
            self.text_animation.stop()
        self.close()
        self.window_closed.emit(self)
        
    def update_opacity(self, opacity: float) -> None:
        """更新横幅透明度
        
        Args:
            opacity (float): 透明度值 (0.0-1.0)
        """
        try:
            logger.debug(f"更新警告横幅透明度为: {opacity}")
            if self.scene:
                # 在GPU渲染模式下，更新场景中背景矩形的透明度
                # 查找背景矩形项（第一个添加的矩形，z值为-1）
                for item in self.scene.items():
                    # 检查是否为QGraphicsRectItem并且z值为-1
                    if isinstance(item, QGraphicsRectItem) and item.zValue() == -1:
                        # 更新背景矩形的画刷透明度
                        brush = item.brush()
                        color = brush.color()
                        alpha_value = int(opacity * 255)
                        color.setAlpha(alpha_value)
                        brush.setColor(color)
                        item.setBrush(brush)
                        self.scene.update()  # 强制更新场景
                        logger.debug("GPU渲染模式下横幅透明度已更新")
                        break
                        
                # 同时更新OpenGL视口的透明度
                if self.graphics_view and hasattr(self.graphics_view, 'viewport') and self.graphics_view.viewport():
                    self.graphics_view.viewport().setWindowOpacity(opacity)
        except Exception as e:
            logger.error(f"更新警告横幅透明度时出错: {e}")
        
    def update_config(self, new_config: Dict[str, Union[str, float, int, bool, None]]) -> None:
        """更新配置
        
        Args:
            new_config (dict): 新的配置字典
        """
        try:
            logger.debug("更新警告横幅配置")
            old_opacity = float(self.config.get("banner_opacity", 0.9) or 0.9)
            self.config.update(new_config)
            new_opacity = float(self.config.get("banner_opacity", 0.9) or 0.9)
            
            # 如果透明度发生变化，则更新透明度
            if old_opacity != new_opacity:
                self.update_opacity(new_opacity)
                
            logger.debug("警告横幅配置更新完成")
        except Exception as e:
            logger.error(f"更新警告横幅配置时出错: {e}")