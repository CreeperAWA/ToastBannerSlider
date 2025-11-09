"""关键字规则对话框模块

该模块提供关键字规则编辑对话框，用于配置关键字替换规则。
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QCheckBox, QPushButton, QLabel,
                               QDialogButtonBox, QGroupBox)
from PySide6.QtWidgets import QWidget as QWidgetType
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFontDialog
from logger_config import logger
from typing import Dict, Union, cast
import sys


class KeywordRuleDialog(QDialog):
    """关键字规则编辑对话框"""

    def __init__(self, rule_data: Union[Dict[str, Union[str, float, int, bool, None]], None] = None, 
                 parent: Union[QWidgetType, None] = None) -> None:
        """
        初始化关键字规则对话框

        Args:
            rule_data: 规则数据
            parent: 父级窗口
        """
        super().__init__(parent)
        self.rule_data = rule_data or {}
        self.setWindowTitle("编辑关键字规则")
        self.setModal(True)
        self.resize(500, 400)
        self._create_ui()
        self._load_data()

    def _create_ui(self) -> None:
        """创建界面"""
        layout = QVBoxLayout(self)

        # 模式行
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("匹配内容:"))
        self.pattern_edit = QLineEdit()
        pattern_layout.addWidget(self.pattern_edit)
        self.regex_checkbox = QCheckBox("使用正则表达式")
        pattern_layout.addWidget(self.regex_checkbox)
        layout.addLayout(pattern_layout)

        # 内容替换行
        content_layout = QHBoxLayout()
        self.replace_content_checkbox = QCheckBox("替换内容")
        content_layout.addWidget(self.replace_content_checkbox)
        self.replacement_edit = QLineEdit()
        self.replacement_edit.setPlaceholderText("替换为...")
        content_layout.addWidget(self.replacement_edit)
        layout.addLayout(content_layout)

        # 字体替换行
        font_group = QGroupBox("字体替换")
        font_layout = QVBoxLayout()
        self.replace_font_checkbox = QCheckBox("替换字体")
        font_layout.addWidget(self.replace_font_checkbox)

        # 字体设置
        font_settings_layout = QFormLayout()

        # 字体选择
        font_select_layout = QHBoxLayout()
        self.font_family_edit = QLineEdit()
        self.font_family_edit.setPlaceholderText("选择的字体将显示在这里")
        self.font_family_edit.setReadOnly(True)
        self.font_family_button = QPushButton("选择字体")
        self.font_family_button.clicked.connect(self._select_font)
        font_select_layout.addWidget(self.font_family_edit)
        font_select_layout.addWidget(self.font_family_button)
        font_settings_layout.addRow("字体:", font_select_layout)

        # 字体预览
        self.font_preview_label = QLabel("预览文本 ABC abc 123")
        self.font_preview_label.setStyleSheet("border: 1px solid gray; padding: 5px;")
        self.font_preview_label.setMinimumHeight(50)
        font_settings_layout.addRow("预览:", self.font_preview_label)

        font_layout.addLayout(font_settings_layout)
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _select_font(self) -> None:
        """打开字体选择对话框"""
        # 创建一个初始字体
        current_family = self.font_family_edit.text()
        initial_font = QFont()
        if current_family:
            initial_font.setFamily(current_family)

        # 显示字体选择对话框，使用简体中文标题
        result = QFontDialog.getFont(initial_font, self, "选择字体")
        ok = result[0]
        font = result[1] if len(result) > 1 else None
        if ok and font:
            # 更新UI元素
            self.font_family_edit.setText(font.family())
            # 更新预览
            self.font_preview_label.setFont(font)

    def _load_data(self) -> None:
        """加载规则数据到界面"""
        self.pattern_edit.setText(str(self.rule_data.get("pattern", "")))
        self.regex_checkbox.setChecked(bool(self.rule_data.get("use_regex", False)))
        self.replace_content_checkbox.setChecked(bool(self.rule_data.get("replace_content", False)))
        self.replacement_edit.setText(str(self.rule_data.get("replacement", "")))
        self.replace_font_checkbox.setChecked(bool(self.rule_data.get("replace_font", False)))

        font_settings = self.rule_data.get("font_settings", {})
        if isinstance(font_settings, dict):
            family = str(font_settings.get("family", ""))
            self.font_family_edit.setText(family)

            # 创建预览字体
            preview_font = QFont()
            if family:
                preview_font.setFamily(family)
            size = float(font_settings.get("size", 48.0) or 48.0)
            preview_font.setPointSizeF(size)
            preview_font.setBold(bool(font_settings.get("bold", False)))
            preview_font.setItalic(bool(font_settings.get("italic", False)))
            preview_font.setUnderline(bool(font_settings.get("underline", False)))
            weight = int(font_settings.get("weight", 50) or 50)
            preview_font.setWeight(QFont.Weight(weight))

            # 更新预览
            self.font_preview_label.setFont(preview_font)

    def get_rule_data(self) -> Dict[str, Union[str, float, int, bool, None, Dict[str, Union[str, float, int, bool, None]]]]:
        """获取规则数据"""
        rule_data: Dict[str, Union[str, float, int, bool, None, Dict[str, Union[str, float, int, bool, None]]]] = {
            "pattern": self.pattern_edit.text(),
            "use_regex": self.regex_checkbox.isChecked(),
            "replace_content": self.replace_content_checkbox.isChecked(),
            "replacement": self.replacement_edit.text(),
            "replace_font": self.replace_font_checkbox.isChecked()
        }

        if self.replace_font_checkbox.isChecked():
            # 从预览标签获取当前字体设置
            current_font = self.font_preview_label.font()
            font_settings: Dict[str, Union[str, float, int, bool, None]] = {
                "family": str(current_font.family()),
                "size": float(current_font.pointSizeF()),
                "bold": bool(current_font.bold()),
                "italic": bool(current_font.italic()),
                "underline": bool(current_font.underline()),
                "weight": int(current_font.weight())
            }
            rule_data["font_settings"] = font_settings

        return rule_data