"""通知横幅显示模块

该模块负责创建和显示顶部通知横幅窗口，实现文字滚动动画和用户交互功能。
"""

import sys
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QHBoxLayout, 
                           QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, Signal
from PySide6.QtGui import QFont, QRegion
from config import load_config
from loguru import logger

class NotificationWindow(QWidget):
    """顶部通知窗口 - 实现消息滚动显示和交互功能"""
    
    # 定义窗口关闭信号
    window_closed = Signal(object)
    
    def __init__(self, message: str = "", vertical_offset: int = 0):
        """初始化通知窗口
        
        Args:
            message (str, optional): 要显示的消息内容
            vertical_offset (int): 垂直偏移量，用于多窗口显示
        """
        logger.debug(f"NotificationWindow.__init__ 开始，message={message}, vertical_offset={vertical_offset}")
        
        try:
            # 调用父类构造函数
            logger.debug("调用父类QWidget构造函数")
            super().__init__()
            logger.debug("父类QWidget构造函数调用完成")
            
            # 添加关闭状态标志，防止重复关闭
            self._is_closing = False
            
            # 加载配置
            logger.debug("开始加载配置")
            self.config = load_config()
            logger.debug(f"配置加载完成: {self.config}")
            
            # 获取基础垂直偏移量
            base_vertical_offset = self.config.get("base_vertical_offset", 0)
            # 合并传入的垂直偏移量和基础垂直偏移量
            self.vertical_offset = vertical_offset + base_vertical_offset
            logger.debug(f"基础垂直偏移量: {base_vertical_offset}, 总垂直偏移量: {self.vertical_offset}")
            
            # 初始化消息和滚动参数
            logger.debug("初始化消息和滚动参数")
            # 将多行文本替换为单行文本，用空格连接
            initial_message = message or "这是一条测试消息，用于验证通知显示功能是否正常工作。消息长度可能会变化，需要确保滚动效果正确。"
            self.message = " ".join(initial_message.splitlines())
            
            self.scroll_count = 0
            self.max_scrolls = self.config.get("scroll_count", 3)  # 从配置中获取最大滚动次数
            self.animation = None
            self.text_width = 0
            self.speed = self.config.get("scroll_speed", 200.0)  # 从配置中获取滚动速度 (px/s)
            self.space = self.config.get("right_spacing", 150)  # 从配置中获取右侧间隔距离
            self.font_size = self.config.get("font_size", 48.0)   # 从配置中获取字体大小
            self.left_margin = self.config.get("left_margin", 93)   # 从配置中获取左侧边距
            self.right_margin = self.config.get("right_margin", 93) # 从配置中获取右侧边距
            self.icon_scale = self.config.get("icon_scale", 1.0)      # 从配置中获取图标缩放倍数
            self.label_offset_x = self.config.get("label_offset_x", 0)  # 从配置中获取标签文本x轴偏移
            self.window_height = self.config.get("window_height", 128)  # 从配置中获取窗口高度
            self.label_mask_width = self.config.get("label_mask_width", 305)  # 从配置中获取标签遮罩宽度
            self.vertical_animation = None  # 垂直位置动画
            self.fade_in = None  # 淡入动画
            self.fade_out = None  # 淡出动画

            # 初始化点击交互参数
            self.click_count = 0
            self.click_to_close = self.config.get("click_to_close", 3)  # 从配置中获取触发关闭的点击次数

            # 初始化UI
            logger.debug("开始初始化UI")
            self.init_ui()
            logger.debug("UI初始化完成")
            
            # 确保message_text已创建且文本尺寸已计算后再设置动画
            logger.debug("开始设置动画")
            if hasattr(self, 'message_text'):
                self.setup_animation()
            else:
                logger.error("message_text未创建，无法设置动画")
            logger.debug("动画设置完成")
            
            logger.debug(f"NotificationWindow创建完成，消息内容：{self.message}")
        except Exception as e:
            logger.error(f"初始化NotificationWindow时出错: {e}", exc_info=True)
            raise

    def _create_icon_label(self) -> QLabel:
        """创建图标标签控件
        
        Returns:
            QLabel: 包含喇叭图标的标签
        """
        try:
            from icon_manager import load_icon
            icon_label = QLabel()
            icon_size = int(48 * self.icon_scale)  # 根据配置的缩放倍数调整图标大小
            
            # 尝试加载自定义图标
            try:
                icon = load_icon()
                if not icon.isNull():
                    pixmap = icon.pixmap(icon_size, icon_size)
                    icon_label.setPixmap(pixmap)
                else:
                    # 如果图标加载失败，使用文本图标
                    icon_label.setText("🔊")
                    icon_label.setFont(QFont("Arial", int(32 * self.icon_scale)))
            except Exception as e:
                logger.warning(f"加载图标失败: {e}")
                icon_label.setText("🔊")
                icon_label.setFont(QFont("Arial", int(32 * self.icon_scale)))
                
            icon_label.setStyleSheet("color: white; background: transparent;")
            icon_label.setFixedSize(icon_size, icon_size)
            icon_label.setAlignment(Qt.AlignCenter)
            return icon_label
        except Exception as e:
            logger.error(f"创建图标标签时出错: {e}", exc_info=True)
            # 创建默认图标标签
            icon_label = QLabel("🔊")
            icon_label.setStyleSheet("color: white; background: transparent;")
            icon_label.setFixedSize(48, 48)
            icon_label.setAlignment(Qt.AlignCenter)
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
        label_text = QLabel("消息提醒:")
        label_text.setFont(QFont("Microsoft YaHei", int(self.font_size // 2)))  # 根据配置的字体大小调整
        label_text.setStyleSheet("color: #3b9fdc; background: transparent;")
        label_text.setAlignment(Qt.AlignVCenter)
        label_text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
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
        try:
            logger.debug(f"开始创建消息文本，屏幕宽度: {screen_width}")
            
            # 创建消息文本
            message_text = QLabel(self.message)
            message_text.setFont(QFont("Microsoft YaHei", int(self.font_size // 2)))  # 使用配置的字体大小
            message_text.setStyleSheet("color: white; background: transparent;")
            message_text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            message_text.setAttribute(Qt.WA_TranslucentBackground)
            message_text.setWordWrap(False)
            
            # 设置文本标签的高度与父容器一致
            message_text.setGeometry(0, 0, 1000, self.window_height)  # 使用配置的高度
            message_text.setMinimumHeight(self.window_height)
            message_text.setMaximumHeight(self.window_height)
            
            # 在这里赋值给实例变量
            self.message_text = message_text
            
            logger.debug("消息文本创建完成")
            return message_text
        except Exception as e:
            logger.error(f"创建消息文本时出错: {e}", exc_info=True)
            # 创建一个默认的消息文本标签作为兜底方案
            message_text = QLabel("默认消息")
            message_text.setStyleSheet("color: white; background: transparent;")
            message_text.setMinimumHeight(self.window_height)
            message_text.setMaximumHeight(self.window_height)
            self.message_text = message_text
            return message_text

    def init_ui(self):
        """初始化用户界面"""
        logger.debug("开始初始化用户界面")
        
        try:
            # 设置窗口属性
            logger.debug("设置窗口属性")
            self.setWindowFlags(
                Qt.FramelessWindowHint |  # 无边框
                Qt.WindowStaysOnTopHint |  # 置顶
                Qt.Tool |  # 工具窗口
                Qt.WindowDoesNotAcceptFocus |  # 不接受焦点
                Qt.X11BypassWindowManagerHint  # 绕过窗口管理器（仅在X11下有效）
            )
            self.setAttribute(Qt.WA_TranslucentBackground, True)  # 背景透明
            
            # 获取屏幕信息
            logger.debug("获取屏幕信息")
            primary_screen = QApplication.primaryScreen()
            screen_geometry = primary_screen.geometry()
            available_geometry = primary_screen.availableGeometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            
            logger.debug(f"屏幕尺寸: {screen_width}x{screen_height}")
            logger.debug(f"屏幕几何信息: {screen_geometry}")
            logger.debug(f"可用屏幕几何信息: {available_geometry}")
            
            
            # 创建主容器 - 使用样式表实现半透明背景
            logger.debug("创建主容器")
            self.main_content = QWidget(self)
            self.main_content.setGeometry(0, 0, screen_width, self.window_height)
            self.main_content.setStyleSheet("""
                QWidget {
                    background-color: rgba(30, 30, 30, 230);
                    border: none;
                }
            """)
            
            # 主布局
            logger.debug("创建主布局")
            layout = QHBoxLayout(self.main_content)
            layout.setContentsMargins(self.left_margin, 0, self.right_margin, 0)
            layout.setSpacing(0)
            
            # 创建标签部件（包含图标和文本）
            logger.debug("创建标签部件")
            label_widget = self._create_label_widget()
            layout.addWidget(label_widget)
            
            # 创建消息容器
            logger.debug("创建消息容器")
            self.message_container = QWidget()
            self.message_container.setStyleSheet("background: transparent;")
            self.message_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.message_container.setFixedHeight(self.window_height)
            
            # 创建消息滑动区域
            logger.debug("创建消息滑动区域")
            slider_width = screen_width - self.left_margin - self.label_mask_width - self.right_margin
            self.message_slider_box = QWidget(self.message_container)
            self.message_slider_box.setGeometry(0, 0, slider_width, self.window_height)
            self.message_slider_box.setStyleSheet("background: transparent;")
            self.message_slider_box.setContentsMargins(0, 0, 0, 0)
            
            # 创建消息文本
            logger.debug("创建消息文本")
            self.message_text = self._create_message_text(screen_width)
            self.message_text.setParent(self.message_slider_box)
            
            # 隐藏消息文本，防止旧内容闪现
            self.message_text.hide()
            
            # 添加到主布局
            layout.addWidget(self.message_container)
            
            logger.debug("UI初始化完成")

            # 在UI构建完成后，设置初始位置
            self._set_initial_position()
        except Exception as e:
            logger.error(f"初始化UI时出错: {e}", exc_info=True)
            raise

    def setup_animation(self):
        """设置滚动动画"""
        logger.debug("开始设置滚动动画")
        
        try:
            # 清除之前的动画
            if self.animation:
                self.animation.stop()
                self.animation.deleteLater()
                self.animation = None
                
            # 确保文本大小已计算
            self._calculate_text_dimensions()
            
            # 获取屏幕信息
            primary_screen = QApplication.primaryScreen()
            screen_geometry = primary_screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            
            logger.debug(f"屏幕尺寸: {screen_width}x{screen_height}")
            
            # 获取文本宽度
            self._calculate_text_dimensions()
            logger.debug(f"文本内容: '{self.message}'")
            logger.debug(f"计算得到的文本宽度: {self.text_width}")
            
            # 计算可用宽度（屏幕宽度减去左右边距和标签遮罩宽度）
            available_width = screen_width - self.left_margin - self.label_mask_width - self.right_margin
            logger.debug(f"容器内可用宽度: {available_width}")
            
            # 获取滚动模式配置
            config = load_config()
            scroll_mode = config.get("scroll_mode", "always")  # 默认为"always"
            logger.debug(f"滚动模式: {scroll_mode}")
            
            # 根据滚动模式决定是否启动动画
            should_scroll = False
            if scroll_mode == "always":
                # 不论如何都滚动
                should_scroll = True
                logger.debug("滚动模式为'always'，将启动滚动动画")
            elif scroll_mode == "auto":
                # 可以展示完全的不滚动
                if self.text_width > available_width:
                    should_scroll = True
                    logger.debug("滚动模式为'auto'且文本宽度大于可用宽度，将启动滚动动画")
                else:
                    should_scroll = False
                    logger.debug("滚动模式为'auto'且文本宽度小于等于可用宽度，不启动滚动动画")
            
            if should_scroll:
                logger.debug("文本将启动滚动动画")
                
                # 设置文本标签的宽度
                if hasattr(self, 'message_text'):
                    self.message_text.setFixedWidth(self.text_width)
                    self.message_text.show()
                
                # 计算滚动距离和持续时间
                scroll_distance = self.text_width + available_width + self.space
                scroll_duration = (scroll_distance / self.speed) * 1000  # 转换为毫秒
                logger.debug(f"滚动距离: {scroll_distance}, 持续时间: {int(scroll_duration)}ms, 速度: {self.speed}px/s")
                
                # 创建动画 - 从右侧外开始滚动到左侧外结束
                if hasattr(self, 'message_text'):
                    self.animation = QPropertyAnimation(self.message_text, b"pos")
                    self.animation.setDuration(int(scroll_duration))
                    self.animation.setStartValue(QPoint(available_width, 0))  # 从右侧外部开始
                    self.animation.setEndValue(QPoint(-(self.text_width + self.space), 0))  # 滚动到左侧外部结束
                    self.animation.setEasingCurve(QEasingCurve.Linear)
                    self.animation.finished.connect(self.animation_completed)
                    self.animation.start()
                
                logger.debug(f"滚动动画已启动，持续时间: {int(scroll_duration)} 毫秒")
            else:
                logger.debug("文本不滚动，居中显示")
                # 文本不滚动，居中显示
                if hasattr(self, 'message_text'):
                    self.message_text.setAlignment(Qt.AlignCenter)
                    self.message_text.setFixedWidth(available_width)
                    self.message_text.show()

            logger.debug("滚动动画设置完成")
        except Exception as e:
            logger.error(f"设置滚动动画时出错: {e}", exc_info=True)
            # 延迟设置动画，等待文本渲染完成
            QTimer.singleShot(100, self._setup_animation_after_render)

    def _setup_animation_after_render(self):
        """在文本完成渲染后设置动画参数"""
        try:
            logger.debug("延迟设置动画参数")
            primary_screen = QApplication.primaryScreen()
            screen_geometry = primary_screen.geometry()
            screen_width = screen_geometry.width()
            
            logger.debug(f"延迟设置时获取屏幕宽度: {screen_width}")
            
            # 确保文本大小已计算
            if hasattr(self, 'message_text'):
                self.message_text.adjustSize()
                logger.debug("消息文本尺寸已调整")
            
            # 使用 fontMetrics 获取更准确的文本宽度
            if hasattr(self, 'message_text'):
                fm = self.message_text.fontMetrics()
                self.text_width = fm.horizontalAdvance(self.message)
                logger.debug(f"通过fontMetrics计算文本宽度: {self.text_width}")
            
            if self.text_width == 0:
                self.text_width = 800  # 默认宽度
                logger.debug("使用默认文本宽度: 800")
                
            # 重新设置文本标签的宽度以适应内容
            if hasattr(self, 'message_text'):
                self.message_text.setFixedWidth(self.text_width)
                # 在设置好位置和尺寸后再显示文本
                self.message_text.show()
                
            # 计算滚动参数
            available_width = screen_width - self.left_margin - self.label_mask_width - self.right_margin
            scroll_distance = screen_width + self.text_width + self.space
            scroll_duration = (scroll_distance / self.speed) * 1000  # 转换为毫秒
            
            logger.debug(f"可用宽度: {available_width}")
            logger.debug(f"滚动距离: {scroll_distance}")
            logger.debug(f"滚动持续时间: {int(scroll_duration)}ms")

            # 创建动画 - 垂直居中位置保持一致
            if self.animation:
                self.animation.stop()
                self.animation.deleteLater()
                self.animation = None
                
            if hasattr(self, 'message_text'):
                self.animation = QPropertyAnimation(self.message_text, b"pos")
                self.animation.setDuration(int(scroll_duration))
                # 从右侧开始，y=0保持垂直居中
                self.animation.setStartValue(QPoint(available_width, 0))
                self.animation.setEndValue(QPoint(-(self.text_width + self.space), 0))
                self.animation.setEasingCurve(QEasingCurve.Linear)
                self.animation.finished.connect(self.animation_completed)
                self.animation.start()
                logger.debug(f"滚动动画已启动，持续时间：{int(scroll_duration)} 毫秒")
            else:
                logger.error("message_text未创建，无法启动动画")
        except Exception as e:
            logger.error(f"延迟设置动画参数时出错: {e}", exc_info=True)
            
    def update_vertical_offset(self, new_offset):
        """更新窗口的垂直偏移量
        
        Args:
            new_offset (int): 新的垂直偏移量
        """
        try:
            logger.debug(f"更新垂直偏移量: {new_offset}")
            
            # 添加基础垂直偏移量
            base_vertical_offset = self.config.get("base_vertical_offset", 0)
            actual_offset = new_offset + base_vertical_offset
            logger.debug(f"基础垂直偏移量: {base_vertical_offset}, 实际垂直偏移量: {actual_offset}")
            
            # 创建垂直位置动画
            if self.vertical_animation:
                self.vertical_animation.stop()
                self.vertical_animation.deleteLater()
                
            self.vertical_animation = QPropertyAnimation(self, b"pos")
            self.vertical_animation.setDuration(self.config.get("shift_animation_duration", 100))  # 使用配置的动画时间
            self.vertical_animation.setStartValue(self.pos())
            self.vertical_animation.setEndValue(QPoint(0, actual_offset))
            self.vertical_animation.setEasingCurve(QEasingCurve.OutCubic)
            self.vertical_animation.start()
            
            logger.debug(f"垂直偏移动画已启动，从 {self.pos().y()} 移动到 {actual_offset}")
        except Exception as e:
            logger.error(f"更新垂直偏移量时出错: {e}", exc_info=True)
            
    def animation_completed(self):
        """处理动画完成后的逻辑，包括循环滚动或关闭窗口"""
        self.scroll_count += 1
        logger.debug(f"动画完成，当前滚动次数：{self.scroll_count}/{self.max_scrolls}")
        
        # 检查是否达到最大滚动次数
        if self.scroll_count >= self.max_scrolls:
            # 淡出并关闭
            self.close_with_animation()
        else:
            # 重置位置并重新开始动画
            primary_screen = QApplication.primaryScreen()
            screen_width = primary_screen.geometry().width()
            device_pixel_ratio = primary_screen.devicePixelRatio()
            
            adjusted_left_margin = int(self.left_margin * device_pixel_ratio)
            adjusted_right_margin = int(self.right_margin * device_pixel_ratio)
            adjusted_label_mask_width = int(self.label_mask_width * device_pixel_ratio)
            available_width = screen_width - adjusted_left_margin - adjusted_label_mask_width - adjusted_right_margin
            
            if hasattr(self, 'message_text'):
                self.message_text.move(available_width, 0)
                if self.animation:
                    self.animation.start()
            logger.debug("重新开始滚动动画")
            
    def close_with_animation(self):
        """带动画效果关闭窗口"""
        # 检查是否已经在关闭过程中，防止重复调用
        if self._is_closing:
            logger.debug("窗口已在关闭过程中，忽略重复关闭请求")
            return
            
        logger.debug("开始关闭窗口动画")
        try:
            # 设置关闭状态标志
            self._is_closing = True
            
            logger.debug("停止滚动动画")
            # 停止滚动动画
            if self.animation:
                self.animation.stop()
                
            # 创建淡出动画
            logger.debug("创建淡出动画")
            if self.fade_out:
                self.fade_out.stop()
                self.fade_out.deleteLater()
                
            self.fade_out = QPropertyAnimation(self, b"windowOpacity")
            # 使用配置中的动画时间，默认为1500ms
            fade_duration = self.config.get("fade_animation_duration", 1500)
            self.fade_out.setDuration(fade_duration)
            self.fade_out.setStartValue(1.0)
            self.fade_out.setEndValue(0.0)
            self.fade_out.setEasingCurve(QEasingCurve.OutCubic)
            self.fade_out.finished.connect(self._on_fade_out_finished)
            self.fade_out.start()
            logger.debug(f"淡出动画已启动，持续时间: {fade_duration}ms")
        except Exception as e:
            logger.error(f"关闭窗口动画时出错: {e}", exc_info=True)
            # 如果动画出错，直接关闭窗口
            self._cleanup_and_close()
        
    def _on_fade_out_finished(self):
        """淡出动画完成后的处理"""
        try:
            logger.debug("淡出动画完成，关闭窗口")
            self._cleanup_and_close()
        except Exception as e:
            logger.error(f"处理淡出动画完成时出错: {e}", exc_info=True)
        
    def _cleanup_and_close(self):
        """清理资源并关闭窗口"""
        logger.debug("开始清理资源并关闭窗口")
        try:
            # 停止所有动画
            logger.debug("停止所有动画")
            animations_to_stop = [self.animation, self.vertical_animation, self.fade_in, self.fade_out]
            for i, anim in enumerate(animations_to_stop):
                if anim:
                    try:
                        logger.debug(f"停止动画 {i+1}")
                        anim.stop()
                        anim.deleteLater()
                    except Exception as e:
                        logger.warning(f"停止动画 {i+1} 时出错: {e}")
                    
            # 重置动画引用
            logger.debug("重置动画引用")
            self.animation = None
            self.vertical_animation = None
            self.fade_in = None
            self.fade_out = None
                
            # 发出窗口关闭信号
            logger.debug("发出窗口关闭信号")
            try:
                self.window_closed.emit(self)
            except Exception as e:
                logger.warning(f"发出窗口关闭信号时出错: {e}")
            
            # 调用父类的close方法
            logger.debug("调用父类close方法")
            super().close()
            logger.debug("窗口已关闭")
        except Exception as e:
            logger.error(f"清理资源并关闭窗口时出错: {e}", exc_info=True)
        
    def _on_animation_finished(self):
        """滚动动画完成后的处理"""
        self.scroll_count += 1
        logger.debug(f"滚动动画完成，当前滚动次数：{self.scroll_count}")
        
        # 如果未达到最大滚动次数，则重新开始
        if self.scroll_count < self.max_scrolls:
            screen_width = QApplication.primaryScreen().geometry().width()
            self.message_text.move(screen_width - self.left_margin - self.label_mask_width - self.right_margin, 0)  # 使用配置的边距
            if self.animation:
                self.animation.start()
        else:
            # 达到最大滚动次数，延时关闭窗口
            logger.debug("达到最大滚动次数，准备关闭窗口")
            QTimer.singleShot(2000, self.close_with_animation)  # 2秒后自动关闭

    def closeEvent(self, event):
        """处理窗口关闭事件
        
        Args:
            event (QCloseEvent): 关闭事件对象
        """
        logger.debug("窗口关闭事件触发")
        try:
            # 检查是否已经在关闭过程中
            if self._is_closing:
                logger.debug("窗口已在关闭过程中，跳过重复的关闭事件处理")
                event.accept()
                return
                
            # 设置关闭状态标志
            self._is_closing = True
            
            # 发出窗口关闭信号
            logger.debug("发出窗口关闭信号")
            self.window_closed.emit(self)
            
            # 接受关闭事件
            event.accept()
            logger.debug("窗口关闭事件处理完成")
        except Exception as e:
            logger.error(f"处理窗口关闭事件时出错: {e}", exc_info=True)
            event.accept()  # 确保窗口能正常关闭

    def __del__(self):
        """析构函数 - 确保资源被正确释放"""
        logger.debug("NotificationWindow对象被销毁")

    def _set_initial_position(self):
        """设置窗口初始位置（屏幕顶部居中）"""
        try:
            # 获取主屏幕尺寸
            screen_geometry = QApplication.primaryScreen().geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            
            # 设置窗口位置和尺寸
            self.setFixedHeight(self.window_height)
            self.setFixedWidth(screen_width)
            self.move(0, self.vertical_offset)
            
            logger.debug(f"窗口位置设置完成：宽度={screen_width}, 高度={self.window_height}, 垂直偏移={self.vertical_offset}")
        except Exception as e:
            logger.error(f"设置初始位置时出错: {e}", exc_info=True)
            raise

    def _calculate_text_dimensions(self):
        """计算文本尺寸"""
        try:
            if not hasattr(self, 'message_text') or not self.message_text:
                logger.warning("消息文本标签未创建，无法计算尺寸")
                return
                
            # 使用 fontMetrics 获取更准确的文本宽度
            fm = self.message_text.fontMetrics()
            self.text_width = fm.horizontalAdvance(self.message)
            
            logger.debug(f"文本尺寸计算完成：宽度={self.text_width}")
        except Exception as e:
            logger.error(f"计算文本尺寸时出错: {e}", exc_info=True)
            self.text_width = 0

    def _start_fade_in_animation(self):
        """启动淡入动画"""
        try:
            logger.debug("开始设置淡入动画")
            # 创建淡入动画
            if self.fade_in:
                self.fade_in.stop()
                self.fade_in.deleteLater()
                
            self.fade_in = QPropertyAnimation(self, b"windowOpacity")
            # 使用配置中的动画时间，默认为1500ms
            fade_duration = self.config.get("fade_animation_duration", 1500)
            self.fade_in.setDuration(fade_duration)
            self.fade_in.setStartValue(0.0)
            self.fade_in.setEndValue(1.0)
            self.fade_in.setEasingCurve(QEasingCurve.InCubic)
            self.fade_in.start()
            logger.debug(f"淡入动画已启动，持续时间: {fade_duration}ms")
        except Exception as e:
            logger.error(f"启动淡入动画时出错: {e}", exc_info=True)
            
    def show(self):
        """显示窗口"""
        logger.debug("开始显示窗口")
        try:
            # 设置窗口标志以减少闪烁
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.Tool |
                Qt.X11BypassWindowManagerHint
            )
            
            super().show()
            logger.debug("窗口已显示")
            
            # 启动淡入动画
            logger.debug("启动淡入动画")
            self._start_fade_in_animation()
            logger.debug("淡入动画已启动")
        except Exception as e:
            logger.error(f"显示窗口时出错: {e}", exc_info=True)
            raise

    def mousePressEvent(self, event):
        """处理鼠标点击事件，支持多次点击关闭功能
        
        Args:
            event (QMouseEvent): 鼠标点击事件
        """
        # 如果窗口已经在关闭过程中，则忽略点击事件
        if self._is_closing:
            logger.debug("窗口已在关闭过程中，忽略点击事件")
            event.accept()
            return
            
        # 增加点击计数
        self.click_count += 1
        logger.debug(f"通知窗口被点击，点击次数：{self.click_count}/{self.click_to_close}")
        
        # 检查是否达到关闭所需的点击次数
        if self.click_count >= self.click_to_close:
            logger.debug("达到关闭所需点击次数，开始关闭通知窗口")
            self.close_with_animation()
        else:
            logger.debug(f"尚未达到关闭所需点击次数，还需点击 {self.click_to_close - self.click_count} 次")
        
        # 接受事件，防止事件传播
        event.accept()

def main():
    """主函数 - 用于测试通知窗口显示"""
    print("="*50)
    print("PyQt消息通知系统")
    print("功能：显示可交互的顶部消息通知横幅")
    print("="*50)
    print("正在启动通知窗口...")
    
    app = QApplication(sys.argv)
    window = NotificationWindow("测试通知消息")
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()