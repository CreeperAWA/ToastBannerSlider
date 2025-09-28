"""通知横幅显示模块

该模块负责创建和显示顶部通知横幅窗口，实现文字滚动动画和用户交互功能。
"""

import sys
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QHBoxLayout, 
                           QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, Signal
from PySide6.QtGui import QFont
from config import load_config
from loguru import logger


class NotificationWindow(QWidget):
    """顶部通知窗口 - 实现消息滚动显示和交互功能"""
    
    # 定义窗口关闭信号
    window_closed = Signal(object)
    
    def __init__(self, message, vertical_offset=0):
        """初始化通知窗口
        
        Args:
            message (str): 要显示的通知消息
            vertical_offset (int): 窗口垂直偏移量（用于多通知堆叠显示）
        """
        super().__init__()
        
        # 初始化成员变量
        self.message = message
        self.click_count = 0
        self.config = load_config()
        self._is_closing = False  # 防止重复关闭
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框窗口
            Qt.WindowStaysOnTopHint |  # 窗口始终置顶
            Qt.Tool |  # 工具窗口类型
            Qt.X11BypassWindowManagerHint  # 绕过窗口管理器（减少闪烁）
        )
        
        # 设置窗口属性（确保在Windows上正确显示）
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示时不激活窗口
        self.setAttribute(Qt.WA_DeleteOnClose)  # 关闭时自动删除对象
        
        # 初始化UI
        self.init_ui()
        
        # 应用配置
        self.apply_config()
        
        # 更新窗口垂直位置
        self.update_vertical_offset(vertical_offset)
        
        # 启动淡入动画
        self.fade_in()
        
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建左侧标签（用于显示消息）
        self.label = QLabel(self.message)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 设置标签样式
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(30, 30, 30, 180);
                padding-left: 20px;
                padding-right: 20px;
                border-radius: 10px;
            }
        """)
        
        # 将标签添加到布局
        main_layout.addWidget(self.label)
        
        # 设置窗口初始大小
        self.resize(800, self.config.get("window_height", 128))
        
    def apply_config(self):
        """应用配置设置"""
        # 重新加载配置
        self.config = load_config()
        
        # 应用字体设置
        font = QFont()
        font.setPixelSize(self.config.get("font_size", 48))
        self.label.setFont(font)
        
        # 应用窗口高度
        current_size = self.size()
        self.resize(current_size.width(), self.config.get("window_height", 128))
        
        # 应用标签样式
        self.update_label_style()
        
    def update_label_style(self):
        """更新标签样式"""
        # 计算遮罩位置
        window_width = self.width()
        mask_width = self.config.get("label_mask_width", 305)
        right_spacing = self.config.get("right_spacing", 150)
        
        # 应用样式
        self.label.setStyleSheet(f"""
            QLabel {{
                color: white;
                background-color: rgba(30, 30, 30, 180);
                padding-left: {self.config.get("left_margin", 93)}px;
                padding-right: {self.config.get("right_margin", 93)}px;
                border-radius: 10px;
            }}
        """)
        
        # 设置遮罩
        self.set_label_mask(window_width, mask_width, right_spacing)
        
    def set_label_mask(self, window_width, mask_width, right_spacing):
        """设置标签遮罩实现滚动效果
        
        Args:
            window_width (int): 窗口宽度
            mask_width (int): 遮罩宽度
            right_spacing (int): 右侧间隔距离
        """
        # 创建遮罩
        # 遮罩从右侧开始，宽度为mask_width，留出right_spacing的间隔
        if window_width > mask_width + right_spacing:
            mask_rect = self.label.rect()
            mask_rect.setLeft(window_width - mask_width - right_spacing)
            mask_rect.setRight(window_width - right_spacing)
            self.label.setMask(QRegion(mask_rect, QRegion.Rectangle))
        else:
            # 如果窗口太小，不应用遮罩
            self.label.setMask(QRegion())
            
    def update_vertical_offset(self, offset):
        """更新窗口垂直偏移量
        
        Args:
            offset (int): 新的垂直偏移量
        """
        # 获取屏幕几何信息
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        
        # 计算基础垂直位置（考虑配置的偏移量）
        base_vertical_offset = self.config.get("base_vertical_offset", 0)
        
        # 更新窗口位置
        self.move(
            screen_geometry.left(), 
            screen_geometry.top() + base_vertical_offset + offset
        )
        
    def fade_in(self):
        """淡入动画"""
        # 设置初始透明度为0
        self.setWindowOpacity(0.0)
        
        # 创建透明度动画
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(self.config.get("fade_animation_duration", 1500))
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 启动动画
        self.fade_in_animation.start()
        
        # 动画结束后启动滚动动画
        self.fade_in_animation.finished.connect(self.start_scroll_animation)
        
    def start_scroll_animation(self):
        """启动滚动动画"""
        # 检查是否应该滚动
        scroll_mode = self.config.get("scroll_mode", "always")
        if scroll_mode == "auto":
            # 自动模式：只有当文本宽度超过遮罩宽度时才滚动
            label_width = self.label.fontMetrics().horizontalAdvance(self.message)
            mask_width = self.config.get("label_mask_width", 305)
            if label_width <= mask_width:
                logger.debug("文本宽度未超过遮罩宽度，不启动滚动")
                return
                
        # 获取标签和窗口的几何信息
        label_width = self.label.width()
        window_width = self.width()
        
        # 计算滚动距离
        text_width = self.label.fontMetrics().horizontalAdvance(self.message)
        scroll_distance = text_width - label_width
        
        # 如果文本宽度小于标签宽度，不需要滚动
        if scroll_distance <= 0:
            logger.debug("文本宽度小于标签宽度，不启动滚动")
            return
            
        # 计算滚动速度和持续时间
        scroll_speed = self.config.get("scroll_speed", 200)  # px/s
        duration = int((scroll_distance / scroll_speed) * 1000)  # 转换为毫秒
        
        # 创建滚动动画
        self.scroll_animation = QPropertyAnimation(self.label, b"pos")
        self.scroll_animation.setDuration(duration)
        self.scroll_animation.setStartValue(QPoint(0, 0))
        self.scroll_animation.setEndValue(QPoint(-scroll_distance, 0))
        self.scroll_animation.setEasingCurve(QEasingCurve.Linear)
        
        # 连接动画完成信号，实现循环滚动
        scroll_count = self.config.get("scroll_count", 3)
        if scroll_count > 0:
            self.scroll_animation.finished.connect(lambda: self.restart_scroll_animation(scroll_count - 1))
        else:
            # 无限滚动
            self.scroll_animation.finished.connect(lambda: self.restart_scroll_animation(-1))
            
        # 启动滚动动画
        self.scroll_animation.start()
        logger.debug(f"启动滚动动画，持续时间: {duration}ms")
        
    def restart_scroll_animation(self, remaining_count):
        """重新启动滚动动画
        
        Args:
            remaining_count (int): 剩余滚动次数，-1表示无限滚动
        """
        # 检查是否应该继续滚动
        if remaining_count == 0:
            logger.debug("滚动次数已达上限，停止滚动")
            return
            
        # 重置标签位置
        self.label.move(0, 0)
        
        # 重新启动滚动动画
        self.start_scroll_animation()
        
    def mousePressEvent(self, event):
        """处理鼠标按下事件
        
        Args:
            event (QMouseEvent): 鼠标事件
        """
        # 增加点击计数
        self.click_count += 1
        logger.debug(f"通知窗口被点击，当前点击次数: {self.click_count}")
        
        # 检查是否达到关闭所需的点击次数
        click_to_close = self.config.get("click_to_close", 3)
        if self.click_count >= click_to_close:
            logger.debug(f"点击次数达到{click_to_close}次，准备关闭窗口")
            self.close_with_animation()
            
        # 调用父类方法
        super().mousePressEvent(event)
        
    def close_with_animation(self):
        """带动画效果关闭窗口"""
        # 检查是否已经在关闭过程中
        if self._is_closing:
            logger.debug("窗口已在关闭过程中，忽略重复关闭请求")
            return
            
        # 设置关闭标志
        self._is_closing = True
        logger.debug("开始关闭窗口动画")
        
        # 创建透明度动画
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(self.config.get("fade_animation_duration", 1500))
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 连接动画完成信号
        self.fade_out_animation.finished.connect(self._cleanup_and_close)
        
        # 启动动画
        self.fade_out_animation.start()
        
    def _cleanup_and_close(self):
        """清理资源并关闭窗口"""
        logger.debug("窗口动画完成，开始清理资源")
        try:
            # 发出窗口关闭信号
            self.window_closed.emit(self)
        except Exception as e:
            logger.error(f"发出窗口关闭信号时出错: {e}")
        finally:
            # 关闭窗口
            try:
                self.close()
            except Exception as e:
                logger.error(f"关闭窗口时出错: {e}")
                
    def closeEvent(self, event):
        """处理窗口关闭事件
        
        Args:
            event (QCloseEvent): 关闭事件
        """
        logger.debug("收到窗口关闭事件")
        # 检查是否已经在关闭过程中
        if self._is_closing:
            logger.debug("窗口已在关闭过程中，接受关闭事件")
            event.accept()
            return
            
        # 设置关闭标志
        self._is_closing = True
        
        # 启动关闭动画
        self.close_with_animation()
        
        # 忽略原始关闭事件，让动画完成后再真正关闭
        event.ignore()

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