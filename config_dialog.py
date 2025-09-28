"""配置对话框模块

该模块提供图形界面用于修改应用程序配置。
"""

import sys
import os
import uuid
import shutil
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QSpinBox, QCheckBox, QDoubleSpinBox, QMessageBox,
                               QComboBox, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from config import load_config, save_config, setup_logger
from icon_manager import load_icon, get_icons_dir
from loguru import logger


class ConfigDialog(QDialog):
    """配置对话框 - 允许用户修改应用程序配置"""
    
    def __init__(self, parent=None):
        """初始化配置对话框
        
        Args:
            parent (QWidget, optional): 父级窗口
        """
        super().__init__(parent)
        # 加载配置用于界面显示
        self.config = load_config()
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("配置设置")
        self.setModal(True)  # 恢复为模态对话框
        
        # 设置窗口图标，与托盘图标一致
        self.setWindowIcon(load_icon("notification_icon.png"))
        
        layout = QVBoxLayout()
        
        # 通知标题设置
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("通知标题："))
        self.title_edit = QLineEdit()
        self.title_edit.setText(self.config.get("notification_title", "911 呼唤群"))
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # 自定义图标设置
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(QLabel("程序图标："))
        self.icon_button = QPushButton("选择图标文件")
        self.icon_button.clicked.connect(self.select_icon)
        icon_layout.addWidget(self.icon_button)
        
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(32, 32)
        self.icon_preview.setStyleSheet("border: 1px solid gray;")
        icon_layout.addWidget(self.icon_preview)
        
        self.clear_icon_button = QPushButton("清除")
        self.clear_icon_button.clicked.connect(self.clear_custom_icon)
        icon_layout.addWidget(self.clear_icon_button)
        layout.addLayout(icon_layout)
        
        # 显示当前图标
        self.update_icon_preview()
        
        # 滚动速度设置
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("滚动速度 (px/s)："))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 2000)
        self.speed_spin.setValue(self.config.get("scroll_speed", 200))
        speed_layout.addWidget(self.speed_spin)
        layout.addLayout(speed_layout)
        
        # 滚动次数设置
        scroll_layout = QHBoxLayout()
        scroll_layout.addWidget(QLabel("滚动次数："))
        self.scroll_spin = QSpinBox()
        self.scroll_spin.setRange(0, 20)
        self.scroll_spin.setValue(self.config.get("scroll_count", 3))
        scroll_layout.addWidget(self.scroll_spin)
        layout.addLayout(scroll_layout)
        
        # 点击关闭次数设置
        click_layout = QHBoxLayout()
        click_layout.addWidget(QLabel("点击关闭次数："))
        self.click_spin = QSpinBox()
        self.click_spin.setRange(1, 10)
        self.click_spin.setValue(self.config.get("click_to_close", 3))
        click_layout.addWidget(self.click_spin)
        layout.addLayout(click_layout)
        
        # 右侧间隔距离设置
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("右侧间隔距离 (px)："))
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 1000)
        self.spacing_spin.setValue(self.config.get("right_spacing", 150))
        spacing_layout.addWidget(self.spacing_spin)
        layout.addLayout(spacing_layout)
        
        # 字体大小设置
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体大小 (px)："))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 100)
        self.font_spin.setValue(self.config.get("font_size", 48))
        font_layout.addWidget(self.font_spin)
        layout.addLayout(font_layout)
        
        # 左边距设置
        left_margin_layout = QHBoxLayout()
        left_margin_layout.addWidget(QLabel("左侧边距 (px)："))
        self.left_margin_spin = QSpinBox()
        self.left_margin_spin.setRange(0, 500)
        self.left_margin_spin.setValue(self.config.get("left_margin", 93))
        left_margin_layout.addWidget(self.left_margin_spin)
        layout.addLayout(left_margin_layout)
        
        # 右边距设置
        right_margin_layout = QHBoxLayout()
        right_margin_layout.addWidget(QLabel("右侧边距 (px)："))
        self.right_margin_spin = QSpinBox()
        self.right_margin_spin.setRange(0, 500)
        self.right_margin_spin.setValue(self.config.get("right_margin", 93))
        right_margin_layout.addWidget(self.right_margin_spin)
        layout.addLayout(right_margin_layout)
        
        # 图标缩放设置
        icon_scale_layout = QHBoxLayout()
        icon_scale_layout.addWidget(QLabel("图标缩放倍数："))
        self.icon_scale_spin = QDoubleSpinBox()
        self.icon_scale_spin.setRange(0.1, 5.0)
        self.icon_scale_spin.setSingleStep(0.1)
        self.icon_scale_spin.setValue(self.config.get("icon_scale", 1.0))
        self.icon_scale_spin.setDecimals(2)
        icon_scale_layout.addWidget(self.icon_scale_spin)
        layout.addLayout(icon_scale_layout)
        
        # 标签偏移设置
        label_offset_layout = QHBoxLayout()
        label_offset_layout.addWidget(QLabel("标签文本x轴偏移 (px)："))
        self.label_offset_spin = QSpinBox()
        self.label_offset_spin.setRange(-500, 500)
        self.label_offset_spin.setValue(self.config.get("label_offset_x", 0))
        label_offset_layout.addWidget(self.label_offset_spin)
        layout.addLayout(label_offset_layout)
        
        # 窗口高度设置
        window_height_layout = QHBoxLayout()
        window_height_layout.addWidget(QLabel("窗口高度 (px)："))
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(20, 500)
        self.window_height_spin.setValue(self.config.get("window_height", 128))
        window_height_layout.addWidget(self.window_height_spin)
        layout.addLayout(window_height_layout)
        
        # 标签遮罩宽度设置
        mask_width_layout = QHBoxLayout()
        mask_width_layout.addWidget(QLabel("标签遮罩宽度 (px)："))
        self.mask_width_spin = QSpinBox()
        self.mask_width_spin.setRange(0, 1000)
        self.mask_width_spin.setValue(self.config.get("label_mask_width", 305))
        mask_width_layout.addWidget(self.mask_width_spin)
        layout.addLayout(mask_width_layout)
        
        # 横幅间隔设置
        banner_spacing_layout = QHBoxLayout()
        banner_spacing_layout.addWidget(QLabel("横幅间隔 (px)："))
        self.banner_spacing_spin = QSpinBox()
        self.banner_spacing_spin.setRange(0, 100)
        self.banner_spacing_spin.setValue(self.config.get("banner_spacing", 10))
        banner_spacing_layout.addWidget(self.banner_spacing_spin)
        layout.addLayout(banner_spacing_layout)
        
        # 上移动画持续时间设置
        shift_duration_layout = QHBoxLayout()
        shift_duration_layout.addWidget(QLabel("上移动画持续时间 (ms)："))
        self.shift_duration_spin = QSpinBox()
        self.shift_duration_spin.setRange(0, 5000)
        self.shift_duration_spin.setValue(self.config.get("shift_animation_duration", 100))
        shift_duration_layout.addWidget(self.shift_duration_spin)
        layout.addLayout(shift_duration_layout)
        
        # 淡入淡出动画时间设置
        fade_duration_layout = QHBoxLayout()
        fade_duration_layout.addWidget(QLabel("淡入淡出动画时间 (ms)："))
        self.fade_duration_spin = QSpinBox()
        self.fade_duration_spin.setRange(100, 10000)
        self.fade_duration_spin.setValue(self.config.get("fade_animation_duration", 1500))
        fade_duration_layout.addWidget(self.fade_duration_spin)
        layout.addLayout(fade_duration_layout)
        
        # 基础垂直偏移设置
        base_vertical_offset_layout = QHBoxLayout()
        base_vertical_offset_layout.addWidget(QLabel("基础垂直偏移 (px)："))
        self.base_vertical_offset_spin = QSpinBox()
        self.base_vertical_offset_spin.setRange(0, 1000)
        self.base_vertical_offset_spin.setValue(self.config.get("base_vertical_offset", 0))
        base_vertical_offset_layout.addWidget(self.base_vertical_offset_spin)
        layout.addLayout(base_vertical_offset_layout)
        
        # 滚动模式
        scroll_mode_layout = QHBoxLayout()
        scroll_mode_layout.addWidget(QLabel("滚动模式："))
        self.scroll_mode_combo = QComboBox()
        self.scroll_mode_combo.addItem("不论如何都滚动", "always")
        self.scroll_mode_combo.addItem("可以展示完全的不滚动", "auto")
        current_scroll_mode = self.config.get("scroll_mode", "always")
        index = self.scroll_mode_combo.findData(current_scroll_mode)
        if index >= 0:
            self.scroll_mode_combo.setCurrentIndex(index)
        scroll_mode_layout.addWidget(self.scroll_mode_combo)
        layout.addLayout(scroll_mode_layout)
        
        # 日志等级设置
        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(QLabel("日志等级："))
        self.log_level_combo = QComboBox()
        log_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
        self.log_level_combo.addItems(log_levels)
        current_log_level = self.config.get("log_level", "INFO")
        index = self.log_level_combo.findText(current_log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        log_level_layout.addWidget(self.log_level_combo)
        layout.addLayout(log_level_layout)
        
        # 忽略重复通知设置
        self.ignore_duplicate_checkbox = QCheckBox("忽略重复通知")
        self.ignore_duplicate_checkbox.setChecked(self.config.get("ignore_duplicate", False))
        layout.addWidget(self.ignore_duplicate_checkbox)
        
        # 免打扰模式
        self.do_not_disturb_checkbox = QCheckBox("免打扰模式")
        self.do_not_disturb_checkbox.setChecked(self.config.get("do_not_disturb", False))
        layout.addWidget(self.do_not_disturb_checkbox)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        self.apply_button = QPushButton("应用")
        
        # 连接按钮信号
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self.apply_config)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def accept(self):
        """接受对话框（点击确定按钮）"""
        logger.debug("ConfigDialog accept方法被调用")
        self.apply_config()
        logger.debug("配置已应用，调用super().accept()")
        super().accept()  # 使用标准的accept方法关闭对话框
        logger.debug("ConfigDialog accept方法执行完成")

    def reject(self):
        """拒绝对话框（点击取消按钮或关闭按钮）"""
        logger.debug("ConfigDialog reject方法被调用")
        logger.debug("用户取消配置更改，不保存任何配置")
        logger.debug("调用super().reject()")
        super().reject()  # 使用标准的reject方法关闭对话框
        logger.debug("ConfigDialog reject方法执行完成")
        
    def closeEvent(self, event):
        """处理对话框关闭事件，防止关闭对话框时影响主程序"""
        logger.debug("ConfigDialog closeEvent被调用")
        # 点击关闭按钮时，不保存配置，直接拒绝对话框
        self.reject()
        event.accept()  # 接受关闭事件
        logger.debug("ConfigDialog closeEvent执行完成")

    def update_icon_preview(self):
        """更新图标预览"""
        custom_icon = self.config.get("custom_icon")
        if custom_icon:
            icon_path = os.path.join(get_icons_dir(), custom_icon)
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    self.icon_preview.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    return
                    
        # 如果没有自定义图标或者加载失败，显示默认图标
        default_icon_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "notification_icon.png")
        if os.path.exists(default_icon_path):
            pixmap = QPixmap(default_icon_path)
            if not pixmap.isNull():
                self.icon_preview.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
                
        self.icon_preview.clear()
        
    def select_icon(self):
        """选择自定义图标文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择图标文件", 
            "", 
            "图标文件 (*.png *.jpg *.jpeg *.ico *.bmp);;所有文件 (*)"
        )
        
        if file_path and os.path.exists(file_path):
            try:
                # 生成唯一的文件名以避免冲突
                file_extension = os.path.splitext(file_path)[1]
                unique_filename = str(uuid.uuid4()) + file_extension
                
                # 确保图标目录存在
                icons_dir = get_icons_dir()
                
                # 复制文件到图标目录
                destination_path = os.path.join(icons_dir, unique_filename)
                shutil.copy2(file_path, destination_path)
                
                # 更新配置
                self.config["custom_icon"] = unique_filename
                self.update_icon_preview()
                
                logger.info(f"图标文件已复制到: {destination_path}")
            except Exception as e:
                logger.error(f"选择图标文件时出错: {e}")
                QMessageBox.critical(self, "错误", f"无法选择图标文件: {e}")
                
    def clear_custom_icon(self):
        """清除自定义图标"""
        custom_icon = self.config.get("custom_icon")
        if custom_icon:
            try:
                # 删除图标文件
                icon_path = os.path.join(get_icons_dir(), custom_icon)
                if os.path.exists(icon_path):
                    os.remove(icon_path)
                    
                # 更新配置
                self.config["custom_icon"] = None
                self.update_icon_preview()
                
                logger.info("自定义图标已清除")
            except Exception as e:
                logger.error(f"清除自定义图标时出错: {e}")
                QMessageBox.critical(self, "错误", f"无法清除自定义图标: {e}")
        else:
            QMessageBox.information(self, "信息", "当前没有设置自定义图标")
            
    def apply_config(self):
        """应用配置更改"""
        # 更新配置中的所有字段
        self.config["notification_title"] = self.title_edit.text()
        self.config["scroll_speed"] = self.speed_spin.value()
        self.config["scroll_count"] = self.scroll_spin.value()
        self.config["click_to_close"] = self.click_spin.value()
        self.config["right_spacing"] = self.spacing_spin.value()
        self.config["font_size"] = self.font_spin.value()
        self.config["left_margin"] = self.left_margin_spin.value()
        self.config["right_margin"] = self.right_margin_spin.value()
        self.config["icon_scale"] = self.icon_scale_spin.value()
        self.config["label_offset_x"] = self.label_offset_spin.value()
        self.config["window_height"] = self.window_height_spin.value()
        self.config["label_mask_width"] = self.mask_width_spin.value()
        self.config["banner_spacing"] = self.banner_spacing_spin.value()
        self.config["shift_animation_duration"] = self.shift_duration_spin.value()
        self.config["ignore_duplicate"] = self.ignore_duplicate_checkbox.isChecked()
        self.config["do_not_disturb"] = self.do_not_disturb_checkbox.isChecked()
        self.config["scroll_mode"] = self.scroll_mode_combo.currentData()
        self.config["fade_animation_duration"] = self.fade_duration_spin.value()
        self.config["base_vertical_offset"] = self.base_vertical_offset_spin.value()
        self.config["log_level"] = self.log_level_combo.currentText()
        # custom_icon字段在select_icon和clear_custom_icon方法中已经更新
        
        # 只有配置发生变化时才保存
        old_config = load_config()
        if self.config != old_config:
            # 保存配置
            save_config(self.config)
            logger.info("配置已保存")
            
            # 更新日志等级
            log_level = self.config.get("log_level", "INFO")
            if log_level:
                setup_logger(self.config)
        else:
            logger.debug("配置未发生变化，无需保存")