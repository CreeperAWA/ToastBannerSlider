"""配置对话框模块

该模块提供图形化配置界面，允许用户修改各种参数。
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
                               QPushButton, QGroupBox, QComboBox, QLabel,
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QIcon, QPixmap
from logger_config import logger
from config import load_config, save_config, get_config_path
from icon_manager import load_icon, get_resource_path
import os

class TrayIconUpdateEvent(QEvent):
    """托盘图标更新事件"""
    def __init__(self):
        super().__init__(QEvent.Type(QEvent.registerEventType()))

class ConfigDialog(QDialog):
    """配置对话框"""
    
    def __init__(self, parent=None):
        """初始化配置对话框"""
        try:
            super().__init__(parent)
            logger.debug("初始化配置对话框")
            
            # 先加载配置
            self.config = load_config()
            
            # 设置窗口属性
            self.setWindowTitle("配置设置")
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
            self.setModal(False)
            
            # 设置窗口图标
            self._set_window_icon()
            
            # 创建UI
            self._create_ui()
            
            # 连接信号
            self._connect_signals()
            
            logger.debug("配置对话框初始化完成")
        except Exception as e:
            logger.error(f"初始化配置对话框时出错: {e}")
            raise
            
    def _set_window_icon(self):
        """设置配置对话框窗口图标"""
        try:
            logger.debug("设置配置对话框窗口图标")
            
            # 先加载配置
            if not hasattr(self, 'config'):
                self.config = load_config()
                
            # 加载图标
            icon = load_icon(self.config)
            if not icon.isNull():
                self.setWindowIcon(icon)
                logger.debug("配置对话框窗口图标设置成功")
            else:
                logger.warning("配置对话框窗口图标为空")
        except Exception as e:
            logger.error(f"设置配置对话框窗口图标时出错: {e}")
            
    def _create_ui(self):
        """创建用户界面"""
        try:
            logger.debug("创建配置对话框UI")
            
            # 创建主布局
            main_layout = QVBoxLayout(self)
            
            # 创建滚动区域以容纳所有配置项
            from PySide6.QtWidgets import QScrollArea, QWidget
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            # 创建滚动区域的内容部件
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            
            # 基本设置组
            basic_group = self._create_basic_group()
            scroll_layout.addWidget(basic_group)
            
            # 显示设置组
            display_group = self._create_display_group()
            scroll_layout.addWidget(display_group)
            
            # 动画设置组
            animation_group = self._create_animation_group()
            scroll_layout.addWidget(animation_group)
            
            # 高级设置组
            advanced_group = self._create_advanced_group()
            scroll_layout.addWidget(advanced_group)
            
            # 图标设置组
            icon_group = self._create_icon_group()
            scroll_layout.addWidget(icon_group)
            
            # 添加伸展以保持布局紧凑
            scroll_layout.addStretch()
            
            # 设置滚动区域的内容
            scroll_area.setWidget(scroll_content)
            main_layout.addWidget(scroll_area)
            
            # 创建按钮布局
            button_layout = QHBoxLayout()
            
            # 恢复默认按钮
            reset_button = QPushButton("恢复默认")
            reset_button.clicked.connect(self._on_reset)
            button_layout.addWidget(reset_button)
            
            # 添加伸展
            button_layout.addStretch()
            
            # 确定和取消按钮
            ok_button = QPushButton("确定")
            ok_button.clicked.connect(self._on_ok)
            cancel_button = QPushButton("取消")
            cancel_button.clicked.connect(self._on_cancel)
            
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            
            main_layout.addLayout(button_layout)
            
            logger.debug("配置对话框UI创建完成")
        except Exception as e:
            logger.error(f"创建配置对话框UI时出错: {e}")
            
    def _create_basic_group(self):
        """创建基本设置组
        
        Returns:
            QGroupBox: 基本设置组
        """
        try:
            group = QGroupBox("基本设置")
            layout = QFormLayout(group)
            
            # 通知标题
            self.title_edit = QLineEdit()
            self.title_edit.setText(self.config.get("notification_title", "911 呼唤群"))
            layout.addRow("通知标题:", self.title_edit)
            
            # 滚动速度
            self.speed_spinbox = QDoubleSpinBox()
            self.speed_spinbox.setRange(1.0, 1000.0)
            self.speed_spinbox.setValue(self.config.get("scroll_speed", 200.0))
            self.speed_spinbox.setSuffix(" px/s")
            layout.addRow("滚动速度:", self.speed_spinbox)
            
            # 滚动次数
            self.scroll_count_spinbox = QSpinBox()
            self.scroll_count_spinbox.setRange(1, 100)
            self.scroll_count_spinbox.setValue(self.config.get("scroll_count", 3))
            layout.addRow("滚动次数:", self.scroll_count_spinbox)
            
            # 点击关闭次数
            self.click_close_spinbox = QSpinBox()
            self.click_close_spinbox.setRange(1, 10)
            self.click_close_spinbox.setValue(self.config.get("click_to_close", 3))
            layout.addRow("点击关闭次数:", self.click_close_spinbox)
            
            return group
        except Exception as e:
            logger.error(f"创建基本设置组时出错: {e}")
            return QGroupBox("基本设置")
            
    def _create_display_group(self):
        """创建显示设置组
        
        Returns:
            QGroupBox: 显示设置组
        """
        try:
            group = QGroupBox("显示设置")
            layout = QFormLayout(group)
            
            # 右侧间隔距离
            self.spacing_spinbox = QSpinBox()
            self.spacing_spinbox.setRange(0, 1000)
            self.spacing_spinbox.setValue(self.config.get("right_spacing", 150))
            self.spacing_spinbox.setSuffix(" px")
            layout.addRow("右侧间隔距离:", self.spacing_spinbox)
            
            # 字体大小
            self.font_size_spinbox = QDoubleSpinBox()
            self.font_size_spinbox.setRange(1.0, 100.0)
            self.font_size_spinbox.setValue(self.config.get("font_size", 48.0))
            self.font_size_spinbox.setSuffix(" px")
            layout.addRow("字体大小:", self.font_size_spinbox)
            
            # 左侧边距
            self.left_margin_spinbox = QSpinBox()
            self.left_margin_spinbox.setRange(0, 500)
            self.left_margin_spinbox.setValue(self.config.get("left_margin", 93))
            self.left_margin_spinbox.setSuffix(" px")
            layout.addRow("左侧边距:", self.left_margin_spinbox)
            
            # 右侧边距
            self.right_margin_spinbox = QSpinBox()
            self.right_margin_spinbox.setRange(0, 500)
            self.right_margin_spinbox.setValue(self.config.get("right_margin", 93))
            self.right_margin_spinbox.setSuffix(" px")
            layout.addRow("右侧边距:", self.right_margin_spinbox)
            
            # 图标缩放倍数
            self.icon_scale_spinbox = QDoubleSpinBox()
            self.icon_scale_spinbox.setRange(0.1, 5.0)
            self.icon_scale_spinbox.setValue(self.config.get("icon_scale", 1.0))
            self.icon_scale_spinbox.setSingleStep(0.1)
            layout.addRow("图标缩放倍数:", self.icon_scale_spinbox)
            
            # 标签文本x轴偏移
            self.label_offset_x_spinbox = QSpinBox()
            self.label_offset_x_spinbox.setRange(-500, 500)
            self.label_offset_x_spinbox.setValue(self.config.get("label_offset_x", 0))
            self.label_offset_x_spinbox.setSuffix(" px")
            layout.addRow("标签文本x轴偏移:", self.label_offset_x_spinbox)
            
            # 窗口高度
            self.window_height_spinbox = QSpinBox()
            self.window_height_spinbox.setRange(20, 500)
            self.window_height_spinbox.setValue(self.config.get("window_height", 128))
            self.window_height_spinbox.setSuffix(" px")
            layout.addRow("窗口高度:", self.window_height_spinbox)
            
            # 标签遮罩宽度
            self.label_mask_width_spinbox = QSpinBox()
            self.label_mask_width_spinbox.setRange(50, 1000)
            self.label_mask_width_spinbox.setValue(self.config.get("label_mask_width", 305))
            self.label_mask_width_spinbox.setSuffix(" px")
            layout.addRow("标签遮罩宽度:", self.label_mask_width_spinbox)
            
            # 横幅间隔
            self.banner_spacing_spinbox = QSpinBox()
            self.banner_spacing_spinbox.setRange(0, 100)
            self.banner_spacing_spinbox.setValue(self.config.get("banner_spacing", 10))
            self.banner_spacing_spinbox.setSuffix(" px")
            layout.addRow("横幅间隔:", self.banner_spacing_spinbox)
            
            # 基础垂直偏移量
            self.base_vertical_offset_spinbox = QSpinBox()
            self.base_vertical_offset_spinbox.setRange(-1000, 1000)
            self.base_vertical_offset_spinbox.setValue(self.config.get("base_vertical_offset", 50))
            self.base_vertical_offset_spinbox.setSuffix(" px")
            layout.addRow("基础垂直偏移量:", self.base_vertical_offset_spinbox)
            
            # 添加横幅透明度设置，使用0-1范围的双精度浮点数
            self.banner_opacity_spinbox = QDoubleSpinBox()
            self.banner_opacity_spinbox.setRange(0.0, 1.0)
            self.banner_opacity_spinbox.setValue(self.config.get("banner_opacity", 0.9))
            self.banner_opacity_spinbox.setSingleStep(0.01)
            layout.addRow("横幅透明度:", self.banner_opacity_spinbox)
            
            # 滚动模式
            self.scroll_mode_combo = QComboBox()
            self.scroll_mode_combo.addItem("不论如何都滚动", "always")
            self.scroll_mode_combo.addItem("可以展示完全的不滚动", "auto")
            current_mode = self.config.get("scroll_mode", "always")
            index = self.scroll_mode_combo.findData(current_mode)
            if index >= 0:
                self.scroll_mode_combo.setCurrentIndex(index)
            layout.addRow("滚动模式:", self.scroll_mode_combo)
            
            return group
        except Exception as e:
            logger.error(f"创建显示设置组时出错: {e}")
            return QGroupBox("显示设置")
            
    def _create_animation_group(self):
        """创建动画设置组
        
        Returns:
            QGroupBox: 动画设置组
        """
        try:
            group = QGroupBox("动画设置")
            layout = QFormLayout(group)
            
            # 上移动画持续时间
            self.shift_duration_spinbox = QSpinBox()
            self.shift_duration_spinbox.setRange(0, 5000)
            self.shift_duration_spinbox.setValue(self.config.get("shift_animation_duration", 100))
            self.shift_duration_spinbox.setSuffix(" ms")
            layout.addRow("上移动画持续时间:", self.shift_duration_spinbox)
            
            # 淡入淡出动画时间
            self.fade_duration_spinbox = QSpinBox()
            self.fade_duration_spinbox.setRange(0, 10000)
            self.fade_duration_spinbox.setValue(self.config.get("fade_animation_duration", 1500))
            self.fade_duration_spinbox.setSuffix(" ms")
            layout.addRow("淡入淡出动画时间:", self.fade_duration_spinbox)
            
            return group
        except Exception as e:
            logger.error(f"创建动画设置组时出错: {e}")
            return QGroupBox("动画设置")
            
    def _create_advanced_group(self):
        """创建高级设置组
        
        Returns:
            QGroupBox: 高级设置组
        """
        try:
            group = QGroupBox("高级设置")
            layout = QFormLayout(group)
            
            # 日志等级
            self.log_level_combo = QComboBox()
            self.log_level_combo.addItem("TRACE", "TRACE")
            self.log_level_combo.addItem("DEBUG", "DEBUG")
            self.log_level_combo.addItem("INFO", "INFO")
            self.log_level_combo.addItem("SUCCESS", "SUCCESS")
            self.log_level_combo.addItem("WARNING", "WARNING")
            self.log_level_combo.addItem("ERROR", "ERROR")
            self.log_level_combo.addItem("CRITICAL", "CRITICAL")
            current_level = self.config.get("log_level", "INFO")
            index = self.log_level_combo.findData(current_level)
            if index >= 0:
                self.log_level_combo.setCurrentIndex(index)
            layout.addRow("日志等级:", self.log_level_combo)
            
            # 忽略重复通知
            self.ignore_duplicate_checkbox = QCheckBox("忽略5分钟内的重复通知")
            self.ignore_duplicate_checkbox.setChecked(self.config.get("ignore_duplicate", False))
            layout.addRow(self.ignore_duplicate_checkbox)
            
            # 免打扰模式
            self.dnd_checkbox = QCheckBox("免打扰模式")
            self.dnd_checkbox.setChecked(self.config.get("do_not_disturb", False))
            layout.addRow(self.dnd_checkbox)
            
            return group
        except Exception as e:
            logger.error(f"创建高级设置组时出错: {e}")
            return QGroupBox("高级设置")
            
    def _create_icon_group(self):
        """创建图标设置组
        
        Returns:
            QGroupBox: 图标设置组
        """
        try:
            group = QGroupBox("图标设置")
            layout = QVBoxLayout(group)
            
            # 自定义图标文件名
            icon_layout = QHBoxLayout()
            icon_layout.addWidget(QLabel("自定义图标:"))
            
            self.icon_edit = QLineEdit()
            current_icon = self.config.get("custom_icon")
            if current_icon:
                self.icon_edit.setText(current_icon)
            icon_layout.addWidget(self.icon_edit)
            
            # 选择图标按钮
            select_icon_button = QPushButton("选择")
            select_icon_button.clicked.connect(self._on_select_icon)
            icon_layout.addWidget(select_icon_button)
            
            # 清除图标按钮
            clear_icon_button = QPushButton("清除")
            clear_icon_button.clicked.connect(self._on_clear_icon)
            icon_layout.addWidget(clear_icon_button)
            
            layout.addLayout(icon_layout)
            
            # 图标预览
            preview_layout = QHBoxLayout()
            preview_layout.addWidget(QLabel("图标预览:"))
            
            from PySide6.QtWidgets import QFrame
            preview_frame = QFrame()
            preview_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
            preview_frame.setFixedSize(64, 64)
            
            from PySide6.QtWidgets import QHBoxLayout as PreviewLayout
            preview_inner_layout = PreviewLayout(preview_frame)
            preview_inner_layout.setContentsMargins(0, 0, 0, 0)
            
            self.icon_preview_label = QLabel()
            self.icon_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview_inner_layout.addWidget(self.icon_preview_label)
            
            preview_layout.addWidget(preview_frame)
            preview_layout.addStretch()
            
            layout.addLayout(preview_layout)
            
            # 更新图标预览
            self._update_icon_preview()
            
            return group
        except Exception as e:
            logger.error(f"创建图标设置组时出错: {e}")
            return QGroupBox("图标设置")
            
    def _connect_signals(self):
        """连接信号"""
        try:
            logger.debug("连接配置对话框信号")
            
            # 连接图标选择相关信号
            self.icon_edit.textChanged.connect(self._on_icon_changed)
            
        except Exception as e:
            logger.error(f"连接配置对话框信号时出错: {e}")
            
    def _on_select_icon(self):
        """处理选择图标事件"""
        try:
            logger.debug("处理选择图标事件")
            
            # 打开文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择图标文件",
                "",
                "图标文件 (*.png *.jpg *.jpeg *.ico *.bmp);;所有文件 (*)"
            )
            
            if file_path:
                logger.debug(f"选择的图标文件: {file_path}")
                
                # 保存图标文件到icons目录并使用UUID重命名
                from icon_manager import save_custom_icon
                saved_filename = save_custom_icon(file_path)
                
                if saved_filename:
                    # 更新图标编辑框
                    self.icon_edit.setText(saved_filename)
                    
                    # 更新图标预览
                    self._update_icon_preview()
                    
                    logger.debug(f"图标文件已保存并重命名为: {saved_filename}")
                else:
                    logger.error("保存图标文件失败")
                    QMessageBox.critical(self, "错误", "保存图标文件失败")
            else:
                logger.debug("未选择图标文件")
        except Exception as e:
            logger.error(f"处理选择图标事件时出错: {e}")
            QMessageBox.critical(self, "错误", f"选择图标文件时出错: {e}")
            
    def _on_clear_icon(self):
        """处理清除图标事件"""
        try:
            logger.debug("处理清除图标事件")
            
            # 清除编辑框
            self.icon_edit.clear()
            
            # 如果有之前的图标文件，删除它
            current_icon = self.config.get("custom_icon")
            if current_icon:
                config_dir = os.path.dirname(get_config_path())
                icons_dir = os.path.join(config_dir, "icons")
                icon_path = os.path.join(icons_dir, current_icon)
                if os.path.exists(icon_path):
                    os.remove(icon_path)
                    
            logger.debug("图标已清除")
            
            # 立即更新托盘图标
            if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'update_config'):
                self.parent().update_config()
        except Exception as e:
            logger.error(f"处理清除图标事件时出错: {e}")
            QMessageBox.critical(self, "错误", f"清除图标文件时出错: {e}")
            
    def _on_icon_changed(self, text):
        """处理图标文本变化事件
        
        Args:
            text (str): 新的图标文件名
        """
        try:
            logger.debug(f"处理图标文本变化事件: {text}")
            self._update_icon_preview()
        except Exception as e:
            logger.error(f"处理图标文本变化事件时出错: {e}")
            
    def _update_icon_preview(self):
        """更新图标预览"""
        try:
            logger.debug("更新图标预览")
            
            icon_text = self.icon_edit.text().strip()
            if icon_text:
                # 获取图标目录
                config_dir = os.path.dirname(get_config_path())
                icons_dir = os.path.join(config_dir, "icons")
                icon_path = os.path.join(icons_dir, icon_text)
                
                logger.debug(f"图标目录路径: {icons_dir}")
                
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        self.icon_preview_label.setPixmap(icon.pixmap(32, 32))
                        logger.debug(f"图标预览已更新: {icon_path}")
                        return
            
            # 使用默认图标预览
            logger.debug("使用默认图标预览")
            resource_icon_path = get_resource_path("notification_icon.ico")
            if os.path.exists(resource_icon_path):
                icon = QIcon(resource_icon_path)
                if not icon.isNull():
                    self.icon_preview_label.setPixmap(icon.pixmap(32, 32))
                else:
                    # 创建一个简单的默认图像
                    pixmap = QPixmap(32, 32)
                    pixmap.fill(Qt.GlobalColor.gray)
                    self.icon_preview_label.setPixmap(pixmap)
            else:
                # 创建一个简单的默认图像
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.GlobalColor.gray)
                self.icon_preview_label.setPixmap(pixmap)
        except Exception as e:
            logger.error(f"更新图标预览时出错: {e}")
            # 出错时显示一个简单的默认图像
            try:
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.GlobalColor.gray)
                self.icon_preview_label.setPixmap(pixmap)
            except Exception as e2:
                logger.error(f"设置默认图标预览时出错: {e2}")
    def _on_reset(self):
        """处理恢复默认事件"""
        try:
            logger.debug("处理恢复默认事件")
            
            # 弹出确认对话框
            reply = QMessageBox.question(
                self, 
                "确认", 
                "确定要恢复所有设置为默认值吗？", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 从config模块导入默认配置
                from config import DEFAULT_CONFIG
                
                # 更新界面控件
                self.title_edit.setText(DEFAULT_CONFIG.get("notification_title", "911 呼唤群"))
                self.speed_spinbox.setValue(DEFAULT_CONFIG.get("scroll_speed", 200.0))
                self.scroll_count_spinbox.setValue(DEFAULT_CONFIG.get("scroll_count", 3))
                self.click_close_spinbox.setValue(DEFAULT_CONFIG.get("click_to_close", 3))
                self.spacing_spinbox.setValue(DEFAULT_CONFIG.get("right_spacing", 150))
                self.font_size_spinbox.setValue(DEFAULT_CONFIG.get("font_size", 48.0))
                self.left_margin_spinbox.setValue(DEFAULT_CONFIG.get("left_margin", 93))
                self.right_margin_spinbox.setValue(DEFAULT_CONFIG.get("right_margin", 93))
                self.icon_scale_spinbox.setValue(DEFAULT_CONFIG.get("icon_scale", 1.0))
                self.label_offset_x_spinbox.setValue(DEFAULT_CONFIG.get("label_offset_x", 0))
                self.window_height_spinbox.setValue(DEFAULT_CONFIG.get("window_height", 128))
                self.label_mask_width_spinbox.setValue(DEFAULT_CONFIG.get("label_mask_width", 305))
                self.banner_spacing_spinbox.setValue(DEFAULT_CONFIG.get("banner_spacing", 10))
                self.shift_duration_spinbox.setValue(DEFAULT_CONFIG.get("shift_animation_duration", 100))
                self.fade_duration_spinbox.setValue(DEFAULT_CONFIG.get("fade_animation_duration", 1500))
                self.base_vertical_offset_spinbox.setValue(DEFAULT_CONFIG.get("base_vertical_offset", 50))
                # 更新横幅透明度的重置逻辑
                self.banner_opacity_spinbox.setValue(DEFAULT_CONFIG.get("banner_opacity", 0.9))
                
                # 滚动模式
                index = self.scroll_mode_combo.findData(DEFAULT_CONFIG.get("scroll_mode", "always"))
                if index >= 0:
                    self.scroll_mode_combo.setCurrentIndex(index)
                    
                # 日志等级
                index = self.log_level_combo.findData(DEFAULT_CONFIG.get("log_level", "INFO"))
                if index >= 0:
                    self.log_level_combo.setCurrentIndex(index)
                    
                # 复选框
                self.ignore_duplicate_checkbox.setChecked(DEFAULT_CONFIG.get("ignore_duplicate", False))
                self.dnd_checkbox.setChecked(DEFAULT_CONFIG.get("do_not_disturb", False))
                
                # 图标
                default_icon = DEFAULT_CONFIG.get("custom_icon")
                if default_icon:
                    self.icon_edit.setText(default_icon)
                else:
                    self.icon_edit.clear()
                    
                # 更新图标预览
                self._update_icon_preview()
                
                logger.debug("已恢复默认设置")
                QMessageBox.information(self, "信息", "已恢复默认设置")
        except Exception as e:
            logger.error(f"处理恢复默认事件时出错: {e}")
            QMessageBox.critical(self, "错误", f"恢复默认设置时出错: {e}")
            
    def _on_ok(self):
        """处理确定事件"""
        try:
            logger.debug("处理确定事件")
            
            # 收集配置
            new_config = {
                "notification_title": self.title_edit.text(),
                "scroll_speed": self.speed_spinbox.value(),
                "scroll_count": self.scroll_count_spinbox.value(),
                "click_to_close": self.click_close_spinbox.value(),
                "right_spacing": self.spacing_spinbox.value(),
                "font_size": self.font_size_spinbox.value(),
                "left_margin": self.left_margin_spinbox.value(),
                "right_margin": self.right_margin_spinbox.value(),
                "icon_scale": self.icon_scale_spinbox.value(),
                "label_offset_x": self.label_offset_x_spinbox.value(),
                "window_height": self.window_height_spinbox.value(),
                "label_mask_width": self.label_mask_width_spinbox.value(),
                "banner_spacing": self.banner_spacing_spinbox.value(),
                "shift_animation_duration": self.shift_duration_spinbox.value(),
                "fade_animation_duration": self.fade_duration_spinbox.value(),
                "base_vertical_offset": self.base_vertical_offset_spinbox.value(),
                # 更新横幅透明度的保存逻辑
                "banner_opacity": self.banner_opacity_spinbox.value(),
                "log_level": self.log_level_combo.currentData(),
                "scroll_mode": self.scroll_mode_combo.currentData(),
                "ignore_duplicate": self.ignore_duplicate_checkbox.isChecked(),
                "do_not_disturb": self.dnd_checkbox.isChecked(),
                "custom_icon": self.icon_edit.text().strip() if self.icon_edit.text().strip() else None
            }
            
            # 保存配置
            if save_config(new_config):
                logger.debug("配置已保存")
                # 检查图标是否发生变化
                old_icon = self.config.get("custom_icon")
                new_icon = new_config.get("custom_icon")
                self.config = new_config
                if (old_icon is None and new_icon is not None) or \
                   (old_icon is not None and new_icon is None) or \
                   (old_icon != new_icon):
                    # 图标发生变化，通知主程序更新托盘图标
                    if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'update_config'):
                        self.parent().update_config()
                self.accept()
            else:
                logger.error("保存配置失败")
                QMessageBox.critical(self, "错误", "保存配置失败")
        except Exception as e:
            logger.error(f"处理确定事件时出错: {e}")
            QMessageBox.critical(self, "错误", f"保存配置时出错: {e}")
            
    def _on_cancel(self):
        """处理取消事件"""
        try:
            logger.debug("处理取消事件")
            self.reject()
        except Exception as e:
            logger.error(f"处理取消事件时出错: {e}")

    def event(self, event):
        """处理自定义事件"""
        if isinstance(event, TrayIconUpdateEvent):
            # 通知主程序更新托盘图标
            if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'update_config'):
                self.parent().update_config()
            return True
        return super().event(event)
