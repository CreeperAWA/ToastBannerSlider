"""配置对话框模块

该模块提供图形化配置界面，允许用户修改各种参数。
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
                               QPushButton, QGroupBox, QComboBox, QLabel,
                               QFileDialog, QMessageBox, QScrollArea, QWidget,
                               QFrame)
from PySide6.QtCore import QAbstractItemModel
from PySide6.QtGui import QStandardItemModel
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QIcon, QPixmap
from logger_config import logger
from config import load_config, save_config, get_config_path, DEFAULT_CONFIG
from icon_manager import load_icon, get_resource_path, save_custom_icon
import os
from typing import Dict, Union
from PySide6.QtWidgets import QWidget as QWidgetType


class TrayIconUpdateEvent(QEvent):
    """托盘图标更新事件"""
    def __init__(self):
        super().__init__(QEvent.Type(QEvent.registerEventType()))


class ConfigDialog(QDialog):
    """配置对话框"""
    
    # 类属性类型注解
    config: Dict[str, Union[str, float, int, bool, None]]
    
    # UI组件属性
    title_edit: QLineEdit
    speed_spinbox: QDoubleSpinBox
    scroll_count_spinbox: QSpinBox
    click_close_spinbox: QSpinBox
    spacing_spinbox: QSpinBox
    font_size_spinbox: QDoubleSpinBox
    left_margin_spinbox: QSpinBox
    right_margin_spinbox: QSpinBox
    icon_scale_spinbox: QDoubleSpinBox
    label_offset_x_spinbox: QSpinBox
    window_height_spinbox: QSpinBox
    label_mask_width_spinbox: QSpinBox
    banner_spacing_spinbox: QSpinBox
    shift_duration_spinbox: QSpinBox
    fade_duration_spinbox: QSpinBox
    base_vertical_offset_spinbox: QSpinBox
    banner_opacity_spinbox: QDoubleSpinBox
    scroll_mode_combo: QComboBox
    log_level_combo: QComboBox
    ignore_duplicate_checkbox: QCheckBox
    dnd_checkbox: QCheckBox
    rendering_backend_combo: QComboBox
    banner_style_combo: QComboBox # 添加对样式选择框的引用
    icon_edit: QLineEdit
    icon_preview_label: QLabel
    
    # 按钮属性
    ok_button: QPushButton
    cancel_button: QPushButton
    reset_button: QPushButton
    
    def __init__(self, parent: QWidgetType | None = None) -> None:
        """初始化配置对话框"""
        try:
            super().__init__(parent)
            logger.debug("初始化配置对话框")
            
            # 先加载配置
            self.config: Dict[str, Union[str, float, int, bool, None]] = load_config()
            
            # 设置窗口属性
            self.setWindowTitle("配置设置")
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
            self.setModal(False)
            
            # 设置窗口尺寸
            self.setMinimumSize(500, 700)  # 设置最小尺寸
            self.resize(550, 750)  # 设置默认尺寸
            
            # 设置窗口图标
            self._set_window_icon()
            
            # 创建UI
            self._create_ui()
            
            # 连接信号
            self._connect_signals()
            
            # 初始化后立即应用渲染后端规则（处理初始化时的状态）
            # 此时所有UI组件都已创建
            self._on_rendering_backend_changed(self.rendering_backend_combo.currentIndex())
            
            logger.debug("配置对话框初始化完成")
        except Exception as e:
            logger.error(f"初始化配置对话框时出错: {e}")
            raise
            
    def _set_window_icon(self) -> None:
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
            
    def _create_ui(self) -> None:
        """创建用户界面"""
        try:
            logger.debug("创建配置对话框UI")
            
            # 创建主布局
            main_layout = QVBoxLayout(self)
            
            # 创建滚动区域以容纳所有配置项
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
            self.reset_button = QPushButton("恢复默认")
            self.reset_button.clicked.connect(self._on_reset)
            button_layout.addWidget(self.reset_button)
            
            # 添加伸展
            button_layout.addStretch()
            
            # 确定和取消按钮
            self.ok_button = QPushButton("确定")
            self.ok_button.clicked.connect(self._on_ok)
            self.cancel_button = QPushButton("取消")
            self.cancel_button.clicked.connect(self._on_cancel)
            
            button_layout.addWidget(self.ok_button)
            button_layout.addWidget(self.cancel_button)
            
            main_layout.addLayout(button_layout)
            
            logger.debug("配置对话框UI创建完成")
        except Exception as e:
            logger.error(f"创建配置对话框UI时出错: {e}")
            
    def _create_basic_group(self) -> QGroupBox:
        """创建基本设置组
        
        Returns:
            QGroupBox: 基本设置组
        """
        try:
            group = QGroupBox("基本设置")
            layout = QFormLayout(group)
            
            # 通知标题
            self.title_edit = QLineEdit()
            self.title_edit.setText(str(self.config.get("notification_title", "911 呼唤群")))
            layout.addRow("通知标题:", self.title_edit)
            
            # 滚动速度
            self.speed_spinbox = QDoubleSpinBox()
            self.speed_spinbox.setRange(1.0, 1000.0)
            self.speed_spinbox.setValue(float(self.config.get("scroll_speed", 200.0) or 200.0))
            self.speed_spinbox.setSuffix(" px/s")
            layout.addRow("滚动速度:", self.speed_spinbox)
            
            # 滚动次数
            self.scroll_count_spinbox = QSpinBox()
            self.scroll_count_spinbox.setRange(1, 100)
            self.scroll_count_spinbox.setValue(int(self.config.get("scroll_count", 3) or 3))
            layout.addRow("滚动次数:", self.scroll_count_spinbox)
            
            # 点击关闭次数
            self.click_close_spinbox = QSpinBox()
            self.click_close_spinbox.setRange(1, 10)
            self.click_close_spinbox.setValue(int(self.config.get("click_to_close", 3) or 3))
            layout.addRow("点击关闭次数:", self.click_close_spinbox)
            
            return group
        except Exception as e:
            logger.error(f"创建基本设置组时出错: {e}")
            return QGroupBox("基本设置")
            
    def _create_display_group(self) -> QGroupBox:
        """创建显示设置组
        
        Returns:
            QGroupBox: 显示设置组
        """
        try:
            group = QGroupBox("显示设置")
            layout = QFormLayout(group)
            
            # 保存对显示组的引用，以便在样式更改时访问
            self.display_group = group
            
            # 横幅样式
            self.banner_style_combo = QComboBox()
            self.banner_style_combo.addItem("默认样式", "default")
            self.banner_style_combo.addItem("警告样式", "warning")
            current_style = self.config.get("banner_style", "default")
            index = self.banner_style_combo.findData(current_style)
            if index >= 0:
                self.banner_style_combo.setCurrentIndex(index)
            layout.addRow("横幅样式:", self.banner_style_combo)
            
            # 右侧间隔距离
            self.spacing_spinbox = QSpinBox()
            self.spacing_spinbox.setRange(0, 1000)
            self.spacing_spinbox.setValue(int(self.config.get("right_spacing", 150) or 150))
            self.spacing_spinbox.setSuffix(" px")
            self.spacing_label = QLabel("右侧间隔距离:")
            layout.addRow(self.spacing_label, self.spacing_spinbox)
            
            # 字体大小
            self.font_size_spinbox = QDoubleSpinBox()
            self.font_size_spinbox.setRange(1.0, 100.0)
            self.font_size_spinbox.setValue(float(self.config.get("font_size", 48.0) or 48.0))
            self.font_size_spinbox.setSuffix(" px")
            self.font_size_label = QLabel("字体大小:")
            layout.addRow(self.font_size_label, self.font_size_spinbox)
            
            # 左侧边距
            self.left_margin_spinbox = QSpinBox()
            self.left_margin_spinbox.setRange(0, 500)
            self.left_margin_spinbox.setValue(int(self.config.get("left_margin", 93) or 93))
            self.left_margin_spinbox.setSuffix(" px")
            self.left_margin_label = QLabel("左侧边距:")
            layout.addRow(self.left_margin_label, self.left_margin_spinbox)
            
            # 右侧边距
            self.right_margin_spinbox = QSpinBox()
            self.right_margin_spinbox.setRange(0, 500)
            self.right_margin_spinbox.setValue(int(self.config.get("right_margin", 93) or 93))
            self.right_margin_spinbox.setSuffix(" px")
            self.right_margin_label = QLabel("右侧边距:")
            layout.addRow(self.right_margin_label, self.right_margin_spinbox)
            
            # 图标缩放倍数
            self.icon_scale_spinbox = QDoubleSpinBox()
            self.icon_scale_spinbox.setRange(0.1, 5.0)
            self.icon_scale_spinbox.setValue(float(self.config.get("icon_scale", 1.0) or 1.0))
            self.icon_scale_spinbox.setSingleStep(0.1)
            self.icon_scale_label = QLabel("图标缩放倍数:")
            layout.addRow(self.icon_scale_label, self.icon_scale_spinbox)
            
            # 标签文本x轴偏移
            self.label_offset_x_spinbox = QSpinBox()
            self.label_offset_x_spinbox.setRange(-500, 500)
            self.label_offset_x_spinbox.setValue(int(self.config.get("label_offset_x", 0) or 0))
            self.label_offset_x_spinbox.setSuffix(" px")
            self.label_offset_x_label = QLabel("标签文本x轴偏移:")
            layout.addRow(self.label_offset_x_label, self.label_offset_x_spinbox)
            
            # 窗口高度
            self.window_height_spinbox = QSpinBox()
            self.window_height_spinbox.setRange(20, 500)
            self.window_height_spinbox.setValue(int(self.config.get("window_height", 128) or 128))
            self.window_height_spinbox.setSuffix(" px")
            self.window_height_label = QLabel("窗口高度:")
            layout.addRow(self.window_height_label, self.window_height_spinbox)
            
            # 标签遮罩宽度
            self.label_mask_width_spinbox = QSpinBox()
            self.label_mask_width_spinbox.setRange(50, 1000)
            self.label_mask_width_spinbox.setValue(int(self.config.get("label_mask_width", 305) or 305))
            self.label_mask_width_spinbox.setSuffix(" px")
            self.label_mask_width_label = QLabel("标签遮罩宽度:")
            layout.addRow(self.label_mask_width_label, self.label_mask_width_spinbox)
            
            # 横幅间隔
            self.banner_spacing_spinbox = QSpinBox()
            self.banner_spacing_spinbox.setRange(0, 100)
            self.banner_spacing_spinbox.setValue(int(self.config.get("banner_spacing", 10) or 10))
            self.banner_spacing_spinbox.setSuffix(" px")
            layout.addRow("横幅间隔:", self.banner_spacing_spinbox)
            
            # 基础垂直偏移量
            self.base_vertical_offset_spinbox = QSpinBox()
            self.base_vertical_offset_spinbox.setRange(-1000, 1000)
            self.base_vertical_offset_spinbox.setValue(int(self.config.get("base_vertical_offset", 50) or 50))
            self.base_vertical_offset_spinbox.setSuffix(" px")
            layout.addRow("基础垂直偏移量:", self.base_vertical_offset_spinbox)
            
            # 添加横幅透明度设置，使用0-1范围的双精度浮点数
            self.banner_opacity_spinbox = QDoubleSpinBox()
            self.banner_opacity_spinbox.setRange(0.0, 1.0)
            self.banner_opacity_spinbox.setValue(float(self.config.get("banner_opacity", 0.9) or 0.9))
            self.banner_opacity_spinbox.setSingleStep(0.01)
            self.banner_opacity_label = QLabel("横幅透明度:")
            layout.addRow(self.banner_opacity_label, self.banner_opacity_spinbox)
            
            # 滚动模式
            self.scroll_mode_combo = QComboBox()
            self.scroll_mode_combo.addItem("不论如何都滚动", "always")
            self.scroll_mode_combo.addItem("可以展示完全的不滚动", "auto")
            current_mode = self.config.get("scroll_mode", "always")
            index = self.scroll_mode_combo.findData(current_mode)
            if index >= 0:
                self.scroll_mode_combo.setCurrentIndex(index)
                
            layout.addRow("滚动模式:", self.scroll_mode_combo)
            
            # 连接横幅样式变化信号
            self.banner_style_combo.currentTextChanged.connect(self._on_banner_style_changed)
            
            # 初始化时根据当前样式隐藏无效配置
            # 此时 advanced_group 尚未创建，rendering_backend_combo 不存在
            # 因此不调用 _on_rendering_backend_changed
            self._apply_banner_style_visibility(self.banner_style_combo.currentData())
            
            return group
        except Exception as e:
            logger.error(f"创建显示设置组时出错: {e}")
            return QGroupBox("显示设置")

    def _apply_banner_style_visibility(self, style_data: str) -> None:
        """根据横幅样式数据应用显示/隐藏逻辑"""
        if style_data == "warning":
            # 隐藏对警告样式无效的配置项
            self.spacing_spinbox.hide()
            self.left_margin_spinbox.hide()
            self.right_margin_spinbox.hide()
            self.icon_scale_spinbox.hide()
            self.label_offset_x_spinbox.hide()
            self.window_height_spinbox.hide()
            self.label_mask_width_spinbox.hide()
            self.font_size_spinbox.hide()
            # 隐藏对应标签
            self.spacing_label.hide()
            self.left_margin_label.hide()
            self.right_margin_label.hide()
            self.icon_scale_label.hide()
            self.label_offset_x_label.hide()
            self.window_height_label.hide()
            self.label_mask_width_label.hide()
            self.font_size_label.hide()
        else:
            # 对于默认样式，显示所有配置项
            self.spacing_spinbox.show()
            self.left_margin_spinbox.show()
            self.right_margin_spinbox.show()
            self.icon_scale_spinbox.show()
            self.label_offset_x_spinbox.show()
            self.window_height_spinbox.show()
            self.label_mask_width_spinbox.show()
            self.font_size_spinbox.show()
            # 显示对应标签
            self.spacing_label.show()
            self.left_margin_label.show()
            self.right_margin_label.show()
            self.icon_scale_label.show()
            self.label_offset_x_label.show()
            self.window_height_label.show()
            self.label_mask_width_label.show()
            self.font_size_label.show()

            
    def _on_banner_style_changed(self, style_text: str) -> None:
        """当横幅样式改变时，隐藏对当前样式无效的配置项，并检查渲染后端限制
        
        Args:
            style_text: 当前选择的样式文本
        """
        logger.debug(f"横幅样式改变为: {style_text}")
        # 获取当前选择的样式数据
        current_style = self.banner_style_combo.currentData()
        
        # 应用样式相关的显示/隐藏逻辑
        self._apply_banner_style_visibility(current_style)

        # 检查渲染后端限制（样式改变后可能需要重新检查透明度和GPU选项可用性）
        # 确保 rendering_backend_combo 已存在
        if hasattr(self, 'rendering_backend_combo'):
            self._on_rendering_backend_changed(self.rendering_backend_combo.currentIndex())


    def _create_animation_group(self) -> QGroupBox:
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
            self.shift_duration_spinbox.setValue(int(self.config.get("shift_animation_duration", 100) or 100))
            self.shift_duration_spinbox.setSuffix(" ms")
            layout.addRow("上移动画持续时间:", self.shift_duration_spinbox)
            
            # 淡入淡出动画时间
            self.fade_duration_spinbox = QSpinBox()
            self.fade_duration_spinbox.setRange(0, 10000)
            self.fade_duration_spinbox.setValue(int(self.config.get("fade_animation_duration", 1500) or 1500))
            self.fade_duration_spinbox.setSuffix(" ms")
            layout.addRow("淡入淡出动画时间:", self.fade_duration_spinbox)
            
            return group
        except Exception as e:
            logger.error(f"创建动画设置组时出错: {e}")
            return QGroupBox("动画设置")
            
    def _create_advanced_group(self) -> QGroupBox:
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
            self.ignore_duplicate_checkbox.setChecked(bool(self.config.get("ignore_duplicate", False)))
            layout.addRow(self.ignore_duplicate_checkbox)
            
            # 免打扰模式
            self.dnd_checkbox = QCheckBox("免打扰模式")
            self.dnd_checkbox.setChecked(bool(self.config.get("do_not_disturb", False)))
            layout.addRow(self.dnd_checkbox)
            
            # 渲染后端选项
            self.rendering_backend_combo = QComboBox()
            self.rendering_backend_combo.addItem("默认 (CPU渲染)", "default")
            self.rendering_backend_combo.addItem("OpenGL (GPU渲染)", "opengl")
            self.rendering_backend_combo.addItem("OpenGL ES (GPU渲染)", "opengles")
            current_backend = self.config.get("rendering_backend", "default")
            index = self.rendering_backend_combo.findData(current_backend)
            if index >= 0:
                self.rendering_backend_combo.setCurrentIndex(index)
            else:
                # 如果找不到对应的数据，设置为默认值
                default_index = self.rendering_backend_combo.findData("default")
                if default_index >= 0:
                    self.rendering_backend_combo.setCurrentIndex(default_index)
            layout.addRow("渲染后端:", self.rendering_backend_combo)
            
            return group
        except Exception as e:
            logger.error(f"创建高级设置组时出错: {e}")
            return QGroupBox("高级设置")
            
    def _create_icon_group(self) -> QGroupBox:
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
                self.icon_edit.setText(str(current_icon))
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

            preview_frame = QFrame()
            preview_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
            preview_frame.setFixedSize(64, 64)
            
            preview_inner_layout = QHBoxLayout(preview_frame)
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
            
    def _connect_signals(self) -> None:
        """连接信号"""
        try:
            logger.debug("连接配置对话框信号")
            
            # 连接图标选择相关信号
            self.icon_edit.textChanged.connect(self._on_icon_changed)
            
            # 连接确定按钮
            self.ok_button.clicked.connect(self._on_ok)
            
            # 连接取消按钮
            self.cancel_button.clicked.connect(self._on_cancel)
            
            # 连接恢复默认按钮
            self.reset_button.clicked.connect(self._on_reset)

            # 连接渲染后端选择框变化信号
            self.rendering_backend_combo.currentIndexChanged.connect(self._on_rendering_backend_changed)
            
            logger.debug("配置对话框信号连接完成")
        except Exception as e:
            logger.error(f"连接配置对话框信号时出错: {e}")

    def _update_gpu_options_enabled(self) -> None:
        """根据当前横幅样式更新GPU选项的启用/禁用状态"""
        current_style = self.banner_style_combo.currentData()
        gpu_items = ["opengl", "opengles"]

        # 获取模型
        model: QAbstractItemModel = self.rendering_backend_combo.model()
        
        if current_style == "default":
            # 使用默认横幅样式时不允许选择GPU渲染
            for i in range(self.rendering_backend_combo.count()):
                item_data = self.rendering_backend_combo.itemData(i)
                if isinstance(model, QStandardItemModel):
                    item = model.item(i)
                    if item and item_data in gpu_items:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                        logger.debug(f"禁用GPU选项: {item_data}")
        else:
            # 使用警告样式时，GPU选项可用
            for i in range(self.rendering_backend_combo.count()):
                item_data = self.rendering_backend_combo.itemData(i)
                if isinstance(model, QStandardItemModel):
                    item = model.item(i)
                    if item and item_data in gpu_items:
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
                        logger.debug(f"启用GPU选项: {item_data}")

    def _on_rendering_backend_changed(self, index: int) -> None:
        """当渲染后端改变时，根据是否为GPU模式控制透明度设置的可见性，
        并根据是否为默认样式和GPU模式控制GPU选项的可用性。
        
        Args:
            index: 渲染后端选择框的新索引
        """
        logger.debug(f"渲染后端改变，索引: {index}")
        current_backend = self.rendering_backend_combo.currentData()
        is_gpu = current_backend in ["opengl", "opengles"]

        # 控制透明度设置的可见性
        if is_gpu:
            # 使用GPU模式渲染时隐藏透明度设置
            self.banner_opacity_spinbox.hide()
            self.banner_opacity_label.hide()
            logger.debug("隐藏透明度设置")
        else:
            # 非GPU模式时显示透明度设置
            self.banner_opacity_spinbox.show()
            self.banner_opacity_label.show()
            logger.debug("显示透明度设置")

        # 更新GPU选项的启用/禁用状态
        self._update_gpu_options_enabled()

        # 检查当前是否为GPU模式，如果是且样式为默认，则强制切换回默认渲染后端
        current_style = self.banner_style_combo.currentData()
        if current_style == "default" and is_gpu:
            default_index = self.rendering_backend_combo.findData("default")
            if default_index >= 0:
                self.rendering_backend_combo.setCurrentIndex(default_index)
                logger.debug("因默认样式，强制切换回默认渲染后端")
                # 重新调用此函数以更新透明度显示状态和选项可用性
                # 注意：这里重新调用后，is_gpu 会变为 False，因此不会再进入这个分支
                self._on_rendering_backend_changed(default_index)
            
    def _on_select_icon(self) -> None:
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
                saved_filename = save_custom_icon(file_path)
                
                if saved_filename:
                    # 更新图标编辑框
                    self.icon_edit.setText(str(saved_filename))
                    
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
            
    def _on_clear_icon(self) -> None:
        """处理清除图标事件"""
        try:
            logger.debug("处理清除图标事件")
            
            # 只清除编辑框，不立即删除文件
            self.icon_edit.clear()
            
            logger.debug("图标已清除")
        except Exception as e:
            logger.error(f"处理清除图标事件时出错: {e}")
            QMessageBox.critical(self, "错误", f"清除图标文件时出错: {e}")
            
    def _on_ok(self) -> None:
        """处理确定事件"""
        try:
            logger.debug("处理确定事件")
            
            # 收集配置
            new_config: Dict[str, Union[str, float, int, bool, None]] = {
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
                "banner_opacity": self.banner_opacity_spinbox.value() if self.banner_opacity_spinbox.isVisible() else 0.9, # 保存时检查可见性，或使用默认值
                "banner_style": self.banner_style_combo.currentData(),  # 添加横幅样式配置项
                "log_level": self.log_level_combo.currentData(),
                "scroll_mode": self.scroll_mode_combo.currentData(),
                "ignore_duplicate": self.ignore_duplicate_checkbox.isChecked(),
                "do_not_disturb": self.dnd_checkbox.isChecked(),
                "rendering_backend": self.rendering_backend_combo.currentData(),
                "custom_icon": self.icon_edit.text().strip() if self.icon_edit.text().strip() else None
            }
            
            # 保存配置
            if save_config(new_config):
                logger.debug("配置已保存")
                
                # 检查图标是否发生变化
                old_icon = self.config.get("custom_icon")
                new_icon = new_config.get("custom_icon")
                
                # 如果图标被清除（之前有图标，现在没有了），删除旧图标文件
                if old_icon and not new_icon:
                    config_dir = os.path.dirname(get_config_path())
                    icons_dir = os.path.join(config_dir, "icons")
                    old_icon_path = os.path.join(icons_dir, str(old_icon))
                    if os.path.exists(old_icon_path):
                        try:
                            os.remove(old_icon_path)
                            logger.debug(f"已删除旧图标文件: {old_icon_path}")
                        except Exception as e:
                            logger.error(f"删除旧图标文件时出错: {e}")
                
                # 如果图标被更改（之前有图标，现在有不同图标），删除旧图标文件
                if old_icon and new_icon and old_icon != new_icon:
                    config_dir = os.path.dirname(get_config_path())
                    icons_dir = os.path.join(config_dir, "icons")
                    old_icon_path = os.path.join(icons_dir, str(old_icon))
                    if os.path.exists(old_icon_path):
                        try:
                            os.remove(old_icon_path)
                            logger.debug(f"已删除旧图标文件: {old_icon_path}")
                        except Exception as e:
                            logger.error(f"删除旧图标文件时出错: {e}")
                
                self.config = new_config
                
                # 如果图标发生变化，通知主程序更新托盘图标
                if (old_icon is None and new_icon is not None) or \
                   (old_icon is not None and new_icon is None) or \
                   (old_icon != new_icon):
                    if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'update_config'):
                        try:
                            self.parent().update_config()  # type: ignore
                        except Exception:
                            pass
                self.accept()
            else:
                logger.error("保存配置失败")
                QMessageBox.critical(self, "错误", "保存配置失败")
        except Exception as e:
            logger.error(f"处理确定事件时出错: {e}")
            QMessageBox.critical(self, "错误", f"保存配置时出错: {e}")
            
    def _on_cancel(self) -> None:
        """处理取消事件"""
        try:
            logger.debug("处理取消事件")
            # 拒绝对话框
            self.reject()
        except Exception as e:
            logger.error(f"处理取消事件时出错: {e}")
            
    def _on_reset(self) -> None:
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
                # 重置渲染后端到默认值
                default_backend_index = self.rendering_backend_combo.findData("default")
                if default_backend_index >= 0:
                    self.rendering_backend_combo.setCurrentIndex(default_backend_index)
                
                # 重置样式到默认值
                default_style_index = self.banner_style_combo.findData("default")
                if default_style_index >= 0:
                    self.banner_style_combo.setCurrentIndex(default_style_index)

                # 更新界面控件 (包括透明度，此时应可见)
                self.title_edit.setText(str(DEFAULT_CONFIG.get("notification_title", "911 呼唤群")))
                self.speed_spinbox.setValue(float(DEFAULT_CONFIG.get("scroll_speed", 200.0) or 200.0))
                self.scroll_count_spinbox.setValue(int(DEFAULT_CONFIG.get("scroll_count", 3) or 3))
                self.click_close_spinbox.setValue(int(DEFAULT_CONFIG.get("click_to_close", 3) or 3))
                self.spacing_spinbox.setValue(int(DEFAULT_CONFIG.get("right_spacing", 150) or 150))
                self.font_size_spinbox.setValue(float(DEFAULT_CONFIG.get("font_size", 48.0) or 48.0))
                self.left_margin_spinbox.setValue(int(DEFAULT_CONFIG.get("left_margin", 93) or 93))
                self.right_margin_spinbox.setValue(int(DEFAULT_CONFIG.get("right_margin", 93) or 93))
                self.icon_scale_spinbox.setValue(float(DEFAULT_CONFIG.get("icon_scale", 1.0) or 1.0))
                self.label_offset_x_spinbox.setValue(int(DEFAULT_CONFIG.get("label_offset_x", 0) or 0))
                self.window_height_spinbox.setValue(int(DEFAULT_CONFIG.get("window_height", 128) or 128))
                self.label_mask_width_spinbox.setValue(int(DEFAULT_CONFIG.get("label_mask_width", 305) or 305))
                self.banner_spacing_spinbox.setValue(int(DEFAULT_CONFIG.get("banner_spacing", 10) or 10))
                self.shift_duration_spinbox.setValue(int(DEFAULT_CONFIG.get("shift_animation_duration", 100) or 100))
                self.fade_duration_spinbox.setValue(int(DEFAULT_CONFIG.get("fade_animation_duration", 1500) or 1500))
                self.base_vertical_offset_spinbox.setValue(int(DEFAULT_CONFIG.get("base_vertical_offset", 50) or 50))
                # 更新横幅透明度的重置逻辑
                self.banner_opacity_spinbox.setValue(float(DEFAULT_CONFIG.get("banner_opacity", 0.9) or 0.9))
                self.banner_opacity_spinbox.show() # 确保重置后透明度控件是可见的
                self.banner_opacity_label.show()
                
                # 滚动模式
                index = self.scroll_mode_combo.findData(DEFAULT_CONFIG.get("scroll_mode", "always"))
                if index >= 0:
                    self.scroll_mode_combo.setCurrentIndex(index)
                    
                # 日志等级
                index = self.log_level_combo.findData(DEFAULT_CONFIG.get("log_level", "INFO"))
                if index >= 0:
                    self.log_level_combo.setCurrentIndex(index)
                    
                # 复选框
                self.ignore_duplicate_checkbox.setChecked(bool(DEFAULT_CONFIG.get("ignore_duplicate", False)))
                self.dnd_checkbox.setChecked(bool(DEFAULT_CONFIG.get("do_not_disturb", False)))
        except Exception as e:
            logger.error(f"处理恢复默认事件时出错: {e}")
            
    def _on_icon_changed(self, text: str) -> None:
        """处理图标文本变化事件
        
        Args:
            text (str): 新的图标文件名
        """
        try:
            logger.debug(f"处理图标文本变化事件: {text}")
            self._update_icon_preview()
        except Exception as e:
            logger.error(f"处理图标文本变化事件时出错: {e}")
            
    def _update_icon_preview(self) -> None:
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
                        # 使用更大的尺寸和更好的缩放质量来显示图标预览
                        pixmap = icon.pixmap(48, 48, QIcon.Mode.Normal, QIcon.State.On)
                        if pixmap.isNull():
                            # 如果无法获取指定尺寸的pixmap，尝试使用默认尺寸
                            pixmap = icon.pixmap(icon.availableSizes()[0]) if icon.availableSizes() else QPixmap(48, 48)
                        # 缩放到预览框大小，使用平滑变换
                        pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.icon_preview_label.setPixmap(pixmap)
                        logger.debug(f"图标预览已更新: {icon_path}")
                        return
            
            # 使用默认图标预览
            logger.debug("使用默认图标预览")
            # 尝试加载notification_icon.ico
            resource_icon_path = get_resource_path("notification_icon.ico")
            if os.path.exists(resource_icon_path):
                icon = QIcon(resource_icon_path)
                if not icon.isNull():
                    pixmap = icon.pixmap(48, 48, QIcon.Mode.Normal, QIcon.State.On)
                    if pixmap.isNull():
                        pixmap = icon.pixmap(icon.availableSizes()[0]) if icon.availableSizes() else QPixmap(48, 48)
                    pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.icon_preview_label.setPixmap(pixmap)
                    return
            
            # 尝试加载notification_icon.png
            resource_icon_path = get_resource_path("notification_icon.png")
            if os.path.exists(resource_icon_path):
                icon = QIcon(resource_icon_path)
                if not icon.isNull():
                    pixmap = icon.pixmap(48, 48, QIcon.Mode.Normal, QIcon.State.On)
                    if pixmap.isNull():
                        pixmap = icon.pixmap(icon.availableSizes()[0]) if icon.availableSizes() else QPixmap(48, 48)
                    pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.icon_preview_label.setPixmap(pixmap)
                    return
            
            # 如果所有尝试都失败了，创建一个简单的默认图像
            pixmap = QPixmap(48, 48)
            pixmap.fill(Qt.GlobalColor.gray)
            self.icon_preview_label.setPixmap(pixmap)
        except Exception as e:
            logger.error(f"更新图标预览时出错: {e}")
            # 出错时显示一个简单的默认图像
            try:
                pixmap = QPixmap(48, 48)
                pixmap.fill(Qt.GlobalColor.gray)
                self.icon_preview_label.setPixmap(pixmap)
            except Exception as e2:
                logger.error(f"设置默认图标预览时出错: {e2}")