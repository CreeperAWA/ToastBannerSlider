"""默认样式横幅模块 (QML版本)

该模块提供默认样式的横幅实现，用于显示普通通知信息。
此版本使用QML进行渲染，提供更流畅的动画效果。
"""

from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QUrl, Property, QTimer, QObject, Slot, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QShowEvent, QMouseEvent, QSurfaceFormat
from PySide6.QtQuickWidgets import QQuickWidget
from config import load_config
from typing import Dict, Union, Optional
from pathlib import Path
import os
import sys


class NoticeSliderQML(QWidget):
    """顶部通知横幅 (QML渲染版本)"""
    
    # 定义窗口关闭信号
    window_closed = Signal(object)
    
    def __init__(self, text: str = "", y_offset: int = 0, max_scrolls: Optional[int] = None):
        super().__init__()
        self.setFixedHeight(128)  # 横幅高度
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, False)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)  # 启用不透明绘制事件优化

        # 置顶、无边框
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        
        # 消息文本
        self._text: str = text if text else ""
        self.text_y_offset: int = y_offset
        
        # 加载配置
        self.config: Dict[str, Union[str, float, int, bool, None]] = load_config()
        
        # 点击次数和关闭阈值
        self.click_count: int = 0
        self.click_to_close: int = int(self.config.get("click_to_close", 3) or 3)  # 从配置中获取点击关闭次数

        # 滚动动画参数
        self.scroll_count: int = 0
        self.max_scrolls: int = max_scrolls if max_scrolls is not None else int(self.config.get("scroll_count", 3) or 3)
        self.speed: float = float(self.config.get("scroll_speed", 200.0) or 200.0)  # 滚动速度 (px/s)
        self.space: int = int(self.config.get("right_spacing", 150) or 150)  # 右侧间隔距离
        self.banner_spacing: int = int(self.config.get("banner_spacing", 10) or 10)  # 横幅间距（用于多横幅间的间隔）
        
        # 新增配置项
        self.banner_opacity: float = float(self.config.get("banner_opacity", 0.9) or 0.9)  # 横幅透明度
        self.scroll_mode: str = str(self.config.get("scroll_mode", "always") or "always")  # 滚动模式
        self.icon_scale: float = float(self.config.get("icon_scale", 1.0) or 1.0)  # 图标缩放比例
        self.left_margin: int = int(self.config.get("left_margin", 93) or 93)  # 左边距
        self.right_margin: int = int(self.config.get("right_margin", 93) or 93)  # 右边距
        self.label_mask_width: int = int(self.config.get("label_mask_width", 305) or 305)  # 标签遮罩宽度
        self.font_size: float = float(self.config.get("font_size", 48.0) or 48.0)  # 字体大小
        self.label_offset_x: int = int(self.config.get("label_offset_x", 0) or 0)  # 标签文本x轴偏移
        self.fade_animation_duration: int = int(self.config.get("fade_animation_duration", 1500) or 1500)  # 淡入淡出动画时间
        
        # 垂直动画
        self.vertical_animation: Optional[QPropertyAnimation] = None
        
        # 设置窗口位置和大小（考虑横幅间距）
        self._set_initial_position()
        
        # 创建QML视图
        self.quick_widget: Optional[QQuickWidget] = None
        self._setup_qml_view()
        
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
        # 计算总偏移量，包括基础偏移、文本偏移和横幅间距
        total_offset = base_vertical_offset + self.text_y_offset
        
        # 设置窗口位置和大小
        self.setGeometry(0, total_offset, screen_width, 128)
        
    def _get_icon_path(self) -> str:
        """获取图标路径用于QML显示
        
        Returns:
            str: 图标文件路径
        """
        try:
            # 尝试加载自定义图标
            custom_icon_filename = self.config.get("custom_icon")
            if custom_icon_filename:
                # 确保custom_icon_filename是字符串类型
                custom_icon_filename = str(custom_icon_filename)
                
                # 获取图标目录
                if getattr(sys, 'frozen', False):
                    # 打包后的程序
                    config_dir = os.path.dirname(sys.executable)
                else:
                    # 开发环境，使用sys.argv[0]而不是__file__
                    config_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                    
                # 构建图标目录路径
                icons_dir = os.path.join(config_dir, "icons")
                icon_path = os.path.join(icons_dir, custom_icon_filename)
                if os.path.exists(icon_path):
                    return icon_path
            
            # 如果没有自定义图标或加载失败，使用默认图标
            # 获取可执行文件所在目录
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # Nuitka单文件模式，资源在临时目录中
                base_path = str(sys._MEIPASS)  # type: ignore
            elif getattr(sys, 'frozen', False):
                # 其他打包模式
                base_path = str(os.path.dirname(sys.executable))
            else:
                # 开发环境，使用__file__获取当前文件目录
                base_path = str(os.path.dirname(os.path.abspath(__file__)))
                
            # 尝试PNG图标
            icon_path = os.path.join(base_path, "notification_icon.png")
            if os.path.exists(icon_path):
                return icon_path
                
            # 尝试ICO图标
            icon_path = os.path.join(base_path, "notification_icon.ico")
            if os.path.exists(icon_path):
                return icon_path
                
            # 返回空字符串表示没有找到图标
            return ""
        except Exception:
            return ""
        
    def _setup_qml_view(self) -> None:
        """设置QML视图"""
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 设置QSurfaceFormat以优化渲染性能
        format = QSurfaceFormat()
        format.setAlphaBufferSize(8)
        format.setSamples(4)  # 启用多重采样抗锯齿
        format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)  # 双缓冲
        format.setSwapInterval(1)  # 垂直同步
        QSurfaceFormat.setDefaultFormat(format)
        
        # 创建QML视图组件
        self.quick_widget = QQuickWidget()
        self.quick_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.quick_widget.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.quick_widget.setClearColor(Qt.GlobalColor.transparent)
        
        # 优化QQuickWidget性能
        self.quick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        
        # 获取QML文件路径
        qml_file = Path(__file__).parent / "NoticeSlider.qml"
        
        # 获取图标路径
        icon_path = self._get_icon_path()
        
        # 加载QML文件前设置上下文属性
        print(f"设置QML上下文属性: maxScrolls={self.max_scrolls}, scrollSpeed={self.speed}, rightSpacing={self.space}, bannerText='{self._text}', bannerOpacity={self.banner_opacity}")
        self.quick_widget.rootContext().setContextProperty("bannerText", self._text)
        self.quick_widget.rootContext().setContextProperty("bannerObject", self)
        self.quick_widget.rootContext().setContextProperty("maxScrolls", self.max_scrolls)
        self.quick_widget.rootContext().setContextProperty("scrollSpeed", float(self.speed))
        self.quick_widget.rootContext().setContextProperty("rightSpacing", self.space)
        self.quick_widget.rootContext().setContextProperty("bannerSpacing", self.banner_spacing)
        self.quick_widget.rootContext().setContextProperty("bannerOpacity", self.banner_opacity)
        self.quick_widget.rootContext().setContextProperty("scrollMode", self.scroll_mode)
        self.quick_widget.rootContext().setContextProperty("iconScale", self.icon_scale)
        self.quick_widget.rootContext().setContextProperty("leftMargin", self.left_margin)
        self.quick_widget.rootContext().setContextProperty("rightMargin", self.right_margin)
        self.quick_widget.rootContext().setContextProperty("labelMaskWidth", self.label_mask_width)
        self.quick_widget.rootContext().setContextProperty("fontSize", self.font_size)
        self.quick_widget.rootContext().setContextProperty("labelOffsetX", self.label_offset_x)
        self.quick_widget.rootContext().setContextProperty("iconPath", icon_path)
        self.quick_widget.rootContext().setContextProperty("fadeAnimationDuration", self.fade_animation_duration)
        
        # 加载QML文件
        self.quick_widget.setSource(QUrl.fromLocalFile(str(qml_file)))
        
        # 将QML视图添加到布局中
        layout.addWidget(self.quick_widget)
            
    def showEvent(self, event: QShowEvent) -> None:
        """窗口显示事件"""
        super().showEvent(event)
        # 更新QML中的配置参数
        if self.quick_widget and self.quick_widget.rootObject():
            try:
                print(f"更新QML属性: maxScrolls={self.max_scrolls}, scrollSpeed={self.speed}, rightSpacing={self.space}, bannerText='{self._text}', bannerOpacity={self.banner_opacity}")
                self.quick_widget.rootObject().setProperty("bannerText", self._text)
                self.quick_widget.rootObject().setProperty("maxScrolls", self.max_scrolls)
                self.quick_widget.rootObject().setProperty("scrollSpeed", float(self.speed))
                self.quick_widget.rootObject().setProperty("rightSpacing", self.space)
                self.quick_widget.rootObject().setProperty("bannerSpacing", self.banner_spacing)
                self.quick_widget.rootObject().setProperty("bannerOpacity", self.banner_opacity)
                self.quick_widget.rootObject().setProperty("scrollMode", self.scroll_mode)
                self.quick_widget.rootObject().setProperty("iconScale", self.icon_scale)
                self.quick_widget.rootObject().setProperty("leftMargin", self.left_margin)
                self.quick_widget.rootObject().setProperty("rightMargin", self.right_margin)
                self.quick_widget.rootObject().setProperty("labelMaskWidth", self.label_mask_width)
                self.quick_widget.rootObject().setProperty("fontSize", self.font_size)
                self.quick_widget.rootObject().setProperty("labelOffsetX", self.label_offset_x)
                self.quick_widget.rootObject().setProperty("fadeAnimationDuration", self.fade_animation_duration)
                
                # 更新图标路径
                icon_path = self._get_icon_path()
                self.quick_widget.rootObject().setProperty("iconPath", icon_path)
            except Exception as e:
                print(f"Failed to update QML properties: {e}")
        
    def close_banner(self) -> None:
        """关闭横幅"""
        if not self._is_closing:
            self._is_closing = True
            # 启动淡出动画
            self._start_fade_out()
                
    def _start_fade_out(self) -> None:
        """启动淡出动画"""
        if self.quick_widget and self.quick_widget.rootObject():
            try:
                self.quick_widget.rootObject().startFadeOut()
            except Exception as e:
                print(f"QML fade out error: {e}")
                self.handleFadeOutFinished()
        else:
            self.handleFadeOutFinished()
            
    # 注意：这个函数将被QML调用
    @Slot()
    def handleFadeOutFinished(self) -> None:
        """处理淡出动画完成事件"""
        # 清理QML中的动画对象
        if self.quick_widget and self.quick_widget.rootObject():
            try:
                self.quick_widget.rootObject().cleanup()
            except Exception as e:
                print(f"QML cleanup error: {e}")
        
        # 延迟销毁窗口以避免QML信号处理冲突
        QTimer.singleShot(100, self._safe_close)
            
    def _safe_close(self) -> None:
        """安全关闭窗口"""
        self.close()
        self.window_closed.emit(self)
            
    @Slot()
    def close_banner_slot(self) -> None:
        """供QML调用的关闭横幅方法"""
        self.close_banner()
            
    def getText(self) -> str:
        """获取横幅文本"""
        return self._text
        
    def setText(self, text: str) -> None:
        """设置横幅文本"""
        self._text = text
        # 更新QML中的文本
        if self.quick_widget and self.quick_widget.rootObject():
            try:
                self.quick_widget.rootObject().setProperty("bannerText", text)
            except Exception as e:
                print(f"Failed to update QML text: {e}")
            
    # 定义属性
    text = Property(str, getText, setText)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """处理鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.click_count += 1
            if self.click_count >= self.click_to_close:
                self.close_banner()
        super().mousePressEvent(event)
        
    def update_vertical_offset(self, new_offset: int) -> None:
        """更新垂直偏移量（带动画效果）
        
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