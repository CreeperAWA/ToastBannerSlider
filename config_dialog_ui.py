"""配置对话框UI模块

该模块提供配置对话框的UI创建和管理功能。
"""

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
                               QPushButton, QGroupBox, QComboBox, QLabel,
                               QFileDialog, QMessageBox, QScrollArea, QWidget,
                               QFrame, QListWidget, QListWidgetItem, QDialogButtonBox,
                               QAbstractItemView)
from PySide6.QtCore import Qt, QAbstractItemModel
from PySide6.QtGui import QStandardItemModel, QIcon, QPixmap, QFont
from logger_config import logger
from config import get_config_path, DEFAULT_CONFIG
from icon_manager import get_resource_path, save_custom_icon
import os
from typing import Dict, Union, List, cast


class ConfigDialogUI:
    """配置对话框UI管理器"""

    def __init__(self, dialog, config: Dict[str, Union[str, float, int, bool, None]]) -> None:
        """
        初始化配置对话框UI管理器

        Args:
            dialog: 父级对话框实例
            config: 配置数据
        """
        self.dialog = dialog
        self.config = config
        self.display_group = None

    def create_ui(self) -> None:
        """创建UI界面"""
        try:
            logger.debug("开始创建配置对话框UI")

            # 创建主布局
            main_layout = QVBoxLayout(self.dialog)

            # 创建滚动区域以容纳所有配置项
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            # 创建滚动区域的内容部件
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)

            # 基本设置组
            self._create_basic_settings_group(scroll_layout)

            # 显示设置组
            self._create_display_settings_group(scroll_layout)

            # 动画设置组
            self._create_animation_settings_group(scroll_layout)

            # 高级设置组
            self._create_advanced_settings_group(scroll_layout)

            # 图标设置组
            self._create_icon_settings_group(scroll_layout)

            # 关键字替换设置组
            self._create_keyword_replacement_group(scroll_layout)

            # 将滚动内容设置到滚动区域
            scroll_area.setWidget(scroll_content)
            main_layout.addWidget(scroll_area)

            # 创建按钮布局
            self._create_buttons(main_layout)

            logger.debug("配置对话框UI创建完成")
        except Exception as e:
            logger.error(f"创建配置对话框UI时出错: {e}", exc_info=True)
            raise

    def _create_basic_settings_group(self, parent_layout: QVBoxLayout) -> None:
        """创建基本设置组"""
        try:
            logger.debug("创建基本设置组")

            # 创建基本设置组
            basic_group = QGroupBox("基本设置")
            basic_layout = QFormLayout(basic_group)

            # 通知标题
            self.dialog.title_edit = QLineEdit()
            self.dialog.title_edit.setText(str(self.config.get("notification_title", "911 呼唤群")))
            basic_layout.addRow("通知标题:", self.dialog.title_edit)

            # 滚动速度
            self.dialog.speed_spinbox = QDoubleSpinBox()
            self.dialog.speed_spinbox.setRange(1.0, 1000.0)
            self.dialog.speed_spinbox.setValue(float(self.config.get("scroll_speed", 200.0) or 200.0))
            self.dialog.speed_spinbox.setSuffix(" px/s")
            basic_layout.addRow("滚动速度:", self.dialog.speed_spinbox)

            # 滚动次数
            self.dialog.scroll_count_spinbox = QSpinBox()
            self.dialog.scroll_count_spinbox.setRange(1, 100)
            self.dialog.scroll_count_spinbox.setValue(int(self.config.get("scroll_count", 3) or 3))
            basic_layout.addRow("滚动次数:", self.dialog.scroll_count_spinbox)

            # 点击关闭次数
            self.dialog.click_close_spinbox = QSpinBox()
            self.dialog.click_close_spinbox.setRange(1, 10)
            self.dialog.click_close_spinbox.setValue(int(self.config.get("click_to_close", 3) or 3))
            basic_layout.addRow("点击关闭次数:", self.dialog.click_close_spinbox)

            # 添加到父布局
            parent_layout.addWidget(basic_group)

            logger.debug("基本设置组创建完成")
        except Exception as e:
            logger.error(f"创建基本设置组时出错: {e}", exc_info=True)

    def _create_display_settings_group(self, parent_layout: QVBoxLayout) -> None:
        """创建显示设置组"""
        try:
            logger.debug("创建显示设置组")

            # 创建显示设置组
            display_group = QGroupBox("显示设置")
            display_layout = QFormLayout(display_group)

            # 保存对显示组的引用，以便在样式更改时访问
            self.display_group = display_group

            # 横幅样式
            self.dialog.banner_style_combo = QComboBox()
            self.dialog.banner_style_combo.addItem("默认样式", "default")
            self.dialog.banner_style_combo.addItem("警告样式", "warning")
            current_style = self.config.get("banner_style", "default")
            index = self.dialog.banner_style_combo.findData(current_style)
            if index >= 0:
                self.dialog.banner_style_combo.setCurrentIndex(index)
            display_layout.addRow("横幅样式:", self.dialog.banner_style_combo)

            # 右侧间隔距离
            self.dialog.spacing_spinbox = QSpinBox()
            self.dialog.spacing_spinbox.setRange(0, 1000)
            self.dialog.spacing_spinbox.setValue(int(self.config.get("right_spacing", 150) or 150))
            self.dialog.spacing_spinbox.setSuffix(" px")
            self.dialog.spacing_label = QLabel("右侧间隔距离:")
            display_layout.addRow(self.dialog.spacing_label, self.dialog.spacing_spinbox)

            # 字体大小
            self.dialog.font_size_spinbox = QDoubleSpinBox()
            self.dialog.font_size_spinbox.setRange(1.0, 100.0)
            self.dialog.font_size_spinbox.setValue(float(self.config.get("font_size", 48.0) or 48.0))
            self.dialog.font_size_spinbox.setSuffix(" px")
            self.dialog.font_size_label = QLabel("字体大小:")
            display_layout.addRow(self.dialog.font_size_label, self.dialog.font_size_spinbox)

            # 左侧边距
            self.dialog.left_margin_spinbox = QSpinBox()
            self.dialog.left_margin_spinbox.setRange(0, 500)
            self.dialog.left_margin_spinbox.setValue(int(self.config.get("left_margin", 93) or 93))
            self.dialog.left_margin_spinbox.setSuffix(" px")
            self.dialog.left_margin_label = QLabel("左侧边距:")
            display_layout.addRow(self.dialog.left_margin_label, self.dialog.left_margin_spinbox)

            # 右侧边距
            self.dialog.right_margin_spinbox = QSpinBox()
            self.dialog.right_margin_spinbox.setRange(0, 500)
            self.dialog.right_margin_spinbox.setValue(int(self.config.get("right_margin", 93) or 93))
            self.dialog.right_margin_spinbox.setSuffix(" px")
            self.dialog.right_margin_label = QLabel("右侧边距:")
            display_layout.addRow(self.dialog.right_margin_label, self.dialog.right_margin_spinbox)

            # 图标缩放倍数
            self.dialog.icon_scale_spinbox = QDoubleSpinBox()
            self.dialog.icon_scale_spinbox.setRange(0.1, 5.0)
            self.dialog.icon_scale_spinbox.setValue(float(self.config.get("icon_scale", 1.0) or 1.0))
            self.dialog.icon_scale_spinbox.setSingleStep(0.1)
            self.dialog.icon_scale_label = QLabel("图标缩放倍数:")
            display_layout.addRow(self.dialog.icon_scale_label, self.dialog.icon_scale_spinbox)

            # 标签文本x轴偏移
            self.dialog.label_offset_x_spinbox = QSpinBox()
            self.dialog.label_offset_x_spinbox.setRange(-500, 500)
            self.dialog.label_offset_x_spinbox.setValue(int(self.config.get("label_offset_x", 0) or 0))
            self.dialog.label_offset_x_spinbox.setSuffix(" px")
            self.dialog.label_offset_x_label = QLabel("标签文本x轴偏移:")
            display_layout.addRow(self.dialog.label_offset_x_label, self.dialog.label_offset_x_spinbox)

            # 窗口高度
            self.dialog.window_height_spinbox = QSpinBox()
            self.dialog.window_height_spinbox.setRange(20, 500)
            self.dialog.window_height_spinbox.setValue(int(self.config.get("window_height", 128) or 128))
            self.dialog.window_height_spinbox.setSuffix(" px")
            self.dialog.window_height_label = QLabel("窗口高度:")
            display_layout.addRow(self.dialog.window_height_label, self.dialog.window_height_spinbox)

            # 标签遮罩宽度
            self.dialog.label_mask_width_spinbox = QSpinBox()
            self.dialog.label_mask_width_spinbox.setRange(50, 1000)
            self.dialog.label_mask_width_spinbox.setValue(int(self.config.get("label_mask_width", 305) or 305))
            self.dialog.label_mask_width_spinbox.setSuffix(" px")
            self.dialog.label_mask_width_label = QLabel("标签遮罩宽度:")
            display_layout.addRow(self.dialog.label_mask_width_label, self.dialog.label_mask_width_spinbox)

            # 横幅间隔
            self.dialog.banner_spacing_spinbox = QSpinBox()
            self.dialog.banner_spacing_spinbox.setRange(0, 100)
            self.dialog.banner_spacing_spinbox.setValue(int(self.config.get("banner_spacing", 10) or 10))
            self.dialog.banner_spacing_spinbox.setSuffix(" px")
            display_layout.addRow("横幅间隔:", self.dialog.banner_spacing_spinbox)

            # 基础垂直偏移量
            self.dialog.base_vertical_offset_spinbox = QSpinBox()
            self.dialog.base_vertical_offset_spinbox.setRange(-1000, 1000)
            self.dialog.base_vertical_offset_spinbox.setValue(int(self.config.get("base_vertical_offset", 50) or 50))
            self.dialog.base_vertical_offset_spinbox.setSuffix(" px")
            display_layout.addRow("基础垂直偏移量:", self.dialog.base_vertical_offset_spinbox)

            # 添加横幅透明度设置，使用0-1范围的双精度浮点数
            self.dialog.banner_opacity_spinbox = QDoubleSpinBox()
            self.dialog.banner_opacity_spinbox.setRange(0.0, 1.0)
            self.dialog.banner_opacity_spinbox.setValue(float(self.config.get("banner_opacity", 0.9) or 0.9))
            self.dialog.banner_opacity_spinbox.setSingleStep(0.01)
            self.dialog.banner_opacity_label = QLabel("横幅透明度:")
            display_layout.addRow(self.dialog.banner_opacity_label, self.dialog.banner_opacity_spinbox)

            # 滚动模式
            self.dialog.scroll_mode_combo = QComboBox()
            self.dialog.scroll_mode_combo.addItem("不论如何都滚动", "always")
            self.dialog.scroll_mode_combo.addItem("可以展示完全的不滚动", "auto")
            current_mode = self.config.get("scroll_mode", "always")
            index = self.dialog.scroll_mode_combo.findData(current_mode)
            if index >= 0:
                self.dialog.scroll_mode_combo.setCurrentIndex(index)

            display_layout.addRow("滚动模式:", self.dialog.scroll_mode_combo)

            # 连接横幅样式变化信号
            self.dialog.banner_style_combo.currentTextChanged.connect(self.dialog._on_banner_style_changed)

            # 初始化时根据当前样式隐藏无效配置
            # 此时 advanced_group 尚未创建，rendering_backend_combo 不存在
            # 因此不调用 _on_rendering_backend_changed
            self.apply_banner_style_visibility(self.dialog.banner_style_combo.currentData())

            # 添加到父布局
            parent_layout.addWidget(display_group)

            logger.debug("显示设置组创建完成")
        except Exception as e:
            logger.error(f"创建显示设置组时出错: {e}", exc_info=True)

    def _create_icon_settings_group(self, parent_layout: QVBoxLayout) -> None:
        """创建图标设置组"""
        try:
            logger.debug("创建图标设置组")

            # 创建图标设置组
            icon_group = QGroupBox("图标设置")
            icon_layout = QVBoxLayout(icon_group)

            # 自定义图标文件名
            icon_h_layout = QHBoxLayout()
            icon_h_layout.addWidget(QLabel("自定义图标:"))

            self.dialog.icon_edit = QLineEdit()
            current_icon = self.config.get("custom_icon")
            if current_icon:
                self.dialog.icon_edit.setText(str(current_icon))
            icon_h_layout.addWidget(self.dialog.icon_edit)

            # 选择图标按钮
            select_icon_button = QPushButton("选择")
            select_icon_button.clicked.connect(self.dialog._on_select_icon)
            icon_h_layout.addWidget(select_icon_button)

            # 清除图标按钮
            clear_icon_button = QPushButton("清除")
            clear_icon_button.clicked.connect(self.dialog._on_clear_icon)
            icon_h_layout.addWidget(clear_icon_button)

            icon_layout.addLayout(icon_h_layout)

            # 图标预览
            preview_layout = QHBoxLayout()
            preview_layout.addWidget(QLabel("图标预览:"))

            preview_frame = QFrame()
            preview_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
            preview_frame.setFixedSize(48, 48)

            preview_inner_layout = QHBoxLayout(preview_frame)
            preview_inner_layout.setContentsMargins(0, 0, 0, 0)

            self.dialog.icon_preview_label = QLabel()
            self.dialog.icon_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview_inner_layout.addWidget(self.dialog.icon_preview_label)

            preview_layout.addWidget(preview_frame)
            preview_layout.addStretch()

            icon_layout.addLayout(preview_layout)

            # 添加到父布局
            parent_layout.addWidget(icon_group)

            # 连接图标选择相关信号
            self.dialog.icon_edit.textChanged.connect(self.dialog._on_icon_changed)

            # 更新图标预览
            self.dialog._update_icon_preview()

            logger.debug("图标设置组创建完成")
        except Exception as e:
            logger.error(f"创建图标设置组时出错: {e}", exc_info=True)

    def apply_banner_style_visibility(self, style_data: str) -> None:
        """根据横幅样式数据应用显示/隐藏逻辑"""
        if style_data == "warning":
            # 隐藏对警告样式无效的配置项
            self.dialog.spacing_spinbox.hide()
            self.dialog.left_margin_spinbox.hide()
            self.dialog.right_margin_spinbox.hide()
            self.dialog.icon_scale_spinbox.hide()
            self.dialog.label_offset_x_spinbox.hide()
            self.dialog.window_height_spinbox.hide()
            self.dialog.label_mask_width_spinbox.hide()
            self.dialog.font_size_spinbox.hide()
            # 隐藏对应标签
            self.dialog.spacing_label.hide()
            self.dialog.left_margin_label.hide()
            self.dialog.right_margin_label.hide()
            self.dialog.icon_scale_label.hide()
            self.dialog.label_offset_x_label.hide()
            self.dialog.window_height_label.hide()
            self.dialog.label_mask_width_label.hide()
            self.dialog.font_size_label.hide()
        else:
            # 对于默认样式，显示所有配置项
            self.dialog.spacing_spinbox.show()
            self.dialog.left_margin_spinbox.show()
            self.dialog.right_margin_spinbox.show()
            self.dialog.icon_scale_spinbox.show()
            self.dialog.label_offset_x_spinbox.show()
            self.dialog.window_height_spinbox.show()
            self.dialog.label_mask_width_spinbox.show()
            self.dialog.font_size_spinbox.show()
            # 显示对应标签
            self.dialog.spacing_label.show()
            self.dialog.left_margin_label.show()
            self.dialog.right_margin_label.show()
            self.dialog.icon_scale_label.show()
            self.dialog.label_offset_x_label.show()
            self.dialog.window_height_label.show()
            self.dialog.label_mask_width_label.show()
            self.dialog.font_size_label.show()

    def _create_animation_settings_group(self, parent_layout: QVBoxLayout) -> None:
        """创建动画设置组"""
        try:
            logger.debug("创建动画设置组")

            # 创建动画设置组
            animation_group = QGroupBox("动画设置")
            animation_layout = QFormLayout(animation_group)

            # 上移动画持续时间
            self.dialog.shift_duration_spinbox = QSpinBox()
            self.dialog.shift_duration_spinbox.setRange(0, 5000)
            self.dialog.shift_duration_spinbox.setValue(int(self.config.get("shift_animation_duration", 100) or 100))
            self.dialog.shift_duration_spinbox.setSuffix(" ms")
            animation_layout.addRow("上移动画持续时间:", self.dialog.shift_duration_spinbox)

            # 淡入淡出动画时间
            self.dialog.fade_duration_spinbox = QDoubleSpinBox()  # 修复类型错误，应该使用 QDoubleSpinBox 而不是 QSpinBox
            self.dialog.fade_duration_spinbox.setRange(0, 10000)
            self.dialog.fade_duration_spinbox.setValue(int(self.config.get("fade_animation_duration", 1500) or 1500))
            self.dialog.fade_duration_spinbox.setSuffix(" ms")
            animation_layout.addRow("淡入淡出动画时间:", self.dialog.fade_duration_spinbox)

            # 添加到父布局
            parent_layout.addWidget(animation_group)

            logger.debug("动画设置组创建完成")
        except Exception as e:
            logger.error(f"创建动画设置组时出错: {e}", exc_info=True)

    def _create_advanced_settings_group(self, parent_layout: QVBoxLayout) -> None:
        """创建高级设置组"""
        try:
            logger.debug("创建高级设置组")

            # 创建高级设置组
            advanced_group = QGroupBox("高级设置")
            advanced_layout = QFormLayout(advanced_group)

            # 日志等级
            self.dialog.log_level_combo = QComboBox()
            self.dialog.log_level_combo.addItem("TRACE", "TRACE")
            self.dialog.log_level_combo.addItem("DEBUG", "DEBUG")
            self.dialog.log_level_combo.addItem("INFO", "INFO")
            self.dialog.log_level_combo.addItem("SUCCESS", "SUCCESS")
            self.dialog.log_level_combo.addItem("WARNING", "WARNING")
            self.dialog.log_level_combo.addItem("ERROR", "ERROR")
            self.dialog.log_level_combo.addItem("CRITICAL", "CRITICAL")
            current_level = self.config.get("log_level", "INFO")
            index = self.dialog.log_level_combo.findData(current_level)
            if index >= 0:
                self.dialog.log_level_combo.setCurrentIndex(index)
            advanced_layout.addRow("日志等级:", self.dialog.log_level_combo)

            # 忽略重复通知
            self.dialog.ignore_duplicate_checkbox = QCheckBox("忽略5分钟内的重复通知")
            self.dialog.ignore_duplicate_checkbox.setChecked(bool(self.config.get("ignore_duplicate", False)))
            advanced_layout.addRow(self.dialog.ignore_duplicate_checkbox)

            # 免打扰模式
            self.dialog.dnd_checkbox = QCheckBox("免打扰模式")
            self.dialog.dnd_checkbox.setChecked(bool(self.config.get("do_not_disturb", False)))
            advanced_layout.addRow(self.dialog.dnd_checkbox)

            # 启用 Qt Quick 选项
            self.dialog.enable_qt_quick_checkbox = QCheckBox("启用 Qt Quick (QML 渲染)")
            self.dialog.enable_qt_quick_checkbox.setChecked(bool(self.config.get("enable_qt_quick", False)))
            advanced_layout.addRow(self.dialog.enable_qt_quick_checkbox)

            # 渲染后端选项
            self.dialog.rendering_backend_combo = QComboBox()
            self.dialog.rendering_backend_combo.addItem("默认 (CPU渲染)", "default")
            self.dialog.rendering_backend_combo.addItem("OpenGL (GPU渲染)", "opengl")
            self.dialog.rendering_backend_combo.addItem("OpenGL ES (GPU渲染)", "opengles")
            current_backend = self.config.get("rendering_backend", "default")
            index = self.dialog.rendering_backend_combo.findData(current_backend)
            if index >= 0:
                self.dialog.rendering_backend_combo.setCurrentIndex(index)
            else:
                # 如果找不到对应的数据，设置为默认值
                default_index = self.dialog.rendering_backend_combo.findData("default")
                if default_index >= 0:
                    self.dialog.rendering_backend_combo.setCurrentIndex(default_index)
            rendering_backend_label = QLabel("渲染后端:")
            rendering_backend_label.setObjectName("rendering_backend_label")
            advanced_layout.addRow(rendering_backend_label, self.dialog.rendering_backend_combo)

            # 连接 Qt Quick 选项变化信号
            self.dialog.enable_qt_quick_checkbox.stateChanged.connect(self.dialog._on_qt_quick_state_changed)

            # 初始化 Qt Quick 状态
            # 不再在这里调用_on_qt_quick_changed，而是在_update_ui_from_config中统一处理
            # self._on_qt_quick_changed(self.enable_qt_quick_checkbox.checkState())

            # 添加到父布局
            parent_layout.addWidget(advanced_group)

            logger.debug("高级设置组创建完成")
        except Exception as e:
            logger.error(f"创建高级设置组时出错: {e}", exc_info=True)

    def _create_buttons(self, parent_layout: QVBoxLayout) -> None:
        """创建按钮"""
        try:
            logger.debug("创建按钮")

            # 创建按钮布局
            button_layout = QHBoxLayout()

            # 恢复默认按钮放在左边
            self.dialog.reset_button = QPushButton("恢复默认")
            self.dialog.reset_button.clicked.connect(self.dialog._on_reset)
            button_layout.addWidget(self.dialog.reset_button)
            
            # 添加弹性空间
            button_layout.addStretch()

            # 确定和取消按钮放在右边
            self.dialog.ok_button = QPushButton("确定")
            self.dialog.ok_button.clicked.connect(self.dialog._on_accept)
            button_layout.addWidget(self.dialog.ok_button)

            self.dialog.cancel_button = QPushButton("取消")
            self.dialog.cancel_button.clicked.connect(self.dialog._on_cancel)
            button_layout.addWidget(self.dialog.cancel_button)

            # 添加到父布局
            parent_layout.addLayout(button_layout)

            logger.debug("按钮创建完成")
        except Exception as e:
            logger.error(f"创建按钮时出错: {e}", exc_info=True)

    def _create_keyword_replacement_group(self, parent_layout: QVBoxLayout) -> None:
        """创建关键字替换组"""
        try:
            logger.debug("创建关键字替换组")

            # 创建关键字替换组
            keyword_group = QGroupBox("关键字替换")
            keyword_layout = QVBoxLayout(keyword_group)

            # 创建列表和按钮布局
            list_layout = QHBoxLayout()

            # 关键字规则列表
            self.dialog.keyword_rules_list = QListWidget()
            self.dialog.keyword_rules_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.dialog.keyword_rules_list.setAlternatingRowColors(True)
            self.dialog.keyword_rules_list.setStyleSheet("""
                QListWidget::item:selected {
                    background-color: #0078d4;
                    color: white;
                }
            """)
            list_layout.addWidget(self.dialog.keyword_rules_list)

            # 按钮布局
            button_layout = QVBoxLayout()
            self.dialog.add_rule_button = QPushButton("添加")
            self.dialog.edit_rule_button = QPushButton("编辑")
            self.dialog.delete_rule_button = QPushButton("删除")
            self.dialog.move_up_button = QPushButton("上移")
            self.dialog.move_down_button = QPushButton("下移")

            # 连接按钮信号
            self.dialog.add_rule_button.clicked.connect(self.dialog._add_rule)
            self.dialog.edit_rule_button.clicked.connect(self.dialog._edit_rule)
            self.dialog.delete_rule_button.clicked.connect(self.dialog._delete_rule)
            self.dialog.move_up_button.clicked.connect(self.dialog._move_rule_up)
            self.dialog.move_down_button.clicked.connect(self.dialog._move_rule_down)

            # 设置按钮大小策略
            button_layout.addWidget(self.dialog.add_rule_button)
            button_layout.addWidget(self.dialog.edit_rule_button)
            button_layout.addWidget(self.dialog.delete_rule_button)
            button_layout.addWidget(self.dialog.move_up_button)
            button_layout.addWidget(self.dialog.move_down_button)
            button_layout.addStretch()

            list_layout.addLayout(button_layout)
            keyword_layout.addLayout(list_layout)

            # 添加到父布局
            parent_layout.addWidget(keyword_group)

            # 加载现有规则
            self.dialog._load_keyword_rules()

            logger.debug("关键字替换组创建完成")
        except Exception as e:
            logger.error(f"创建关键字替换组时出错: {e}", exc_info=True)