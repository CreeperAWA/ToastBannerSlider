"""配置对话框模块

该模块提供图形化配置界面，允许用户修改各种参数。
"""

from PySide6.QtWidgets import (QDialog, QListWidgetItem, QLineEdit, QDoubleSpinBox, 
                               QSpinBox, QCheckBox, QPushButton, QComboBox, QLabel, QListWidget)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget as QWidgetType
from logger_config import logger
from config import load_config
from typing import Dict, Union, List
import typing
from typing import List, Dict, Union

# 导入新创建的模块
from keyword_rule_dialog import KeywordRuleDialog
from config_dialog_ui import ConfigDialogUI
from config_dialog_logic import ConfigDialogLogic


class ConfigDialog(QDialog):
    """配置对话框"""

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
    fade_duration_spinbox: QDoubleSpinBox
    base_vertical_offset_spinbox: QSpinBox
    banner_opacity_spinbox: QDoubleSpinBox
    scroll_mode_combo: QComboBox
    log_level_combo: QComboBox
    ignore_duplicate_checkbox: QCheckBox
    dnd_checkbox: QCheckBox
    rendering_backend_combo: QComboBox
    banner_style_combo: QComboBox  # 添加对样式选择框的引用
    icon_edit: QLineEdit
    icon_preview_label: QLabel
    enable_qt_quick_checkbox: QCheckBox
    keyword_rules_list: QListWidget

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

            # 初始化UI管理器和逻辑处理器
            self.ui_manager = ConfigDialogUI(self, self.config)
            self.logic_handler = ConfigDialogLogic(typing.cast(typing.Any, self), self.config)

            # 设置窗口图标
            self.logic_handler.set_window_icon()

            # 创建UI
            self.ui_manager.create_ui()

            # 连接信号
            self.logic_handler.connect_signals()

            # 初始化后立即应用渲染后端规则（处理初始化时的状态）
            # 此时所有UI组件都已创建
            self.logic_handler.on_rendering_backend_changed(self.rendering_backend_combo.currentIndex())

            # 初始化后立即应用 Qt Quick 规则（处理初始化时的状态）
            self.logic_handler.on_qt_quick_changed(self.enable_qt_quick_checkbox.checkState())

            logger.debug("配置对话框初始化完成")
        except Exception as e:
            logger.error(f"初始化配置对话框时出错: {e}", exc_info=True)
            raise

    def _on_banner_style_changed(self, style_text: str) -> None:
        """当横幅样式改变时，隐藏对当前样式无效的配置项，并检查渲染后端限制

        Args:
            style_text: 当前选择的样式文本
        """
        logger.debug(f"横幅样式改变为: {style_text}")
        # 获取当前选择的样式数据
        current_style = self.banner_style_combo.currentData()

        # 应用样式相关的显示/隐藏逻辑
        self.ui_manager.apply_banner_style_visibility(current_style)

        # 检查渲染后端限制（样式改变后可能需要重新检查透明度和GPU选项可用性）
        # 确保 rendering_backend_combo 已存在
        if hasattr(self, 'rendering_backend_combo'):
            self.logic_handler.on_rendering_backend_changed(self.rendering_backend_combo.currentIndex())

    def _load_keyword_rules(self) -> None:
        """加载关键字替换规则"""
        try:
            logger.debug("加载关键字替换规则")
            from typing import cast
            config_rules = self.config.get("keyword_replacements", [])
            # 确保rules是列表类型
            if not isinstance(config_rules, list):
                config_rules = []

            # 明确指定config_rules的类型
            typed_rules = cast(List[Dict[str, Union[str, float, int, bool, None]]], config_rules)

            self.keyword_rules_list.clear()
            for rule_item in typed_rules:
                # 确保rule_data是字典类型
                if not hasattr(rule_item, 'items'):
                    continue

                # 明确指定rule_data的类型
                typed_rule_data: Dict[str, Union[str, float, int, bool, None]] = rule_item
                # 创建列表项
                item_text = str(typed_rule_data.get("pattern", ""))
                if not item_text:
                    item_text = "[空模式]"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, typed_rule_data)
                self.keyword_rules_list.addItem(item)

            logger.debug(f"已加载 {self.keyword_rules_list.count()} 条规则")
        except Exception as e:
            logger.error(f"加载关键字替换规则时出错: {e}", exc_info=True)

    def _add_rule(self) -> None:
        """添加新规则"""
        try:
            logger.debug("添加新规则")
            dialog = KeywordRuleDialog(parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                rule_data: Dict[str, Union[str, float, int, bool, None, Dict[str, Union[str, float, int, bool, None]]]] = dialog.get_rule_data()
                item_text: str = str(rule_data.get("pattern", ""))
                if not item_text:
                    item_text = "[空模式]"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, rule_data)
                self.keyword_rules_list.addItem(item)
                logger.debug(f"已添加新规则: {item_text}")
        except Exception as e:
            logger.error(f"添加新规则时出错: {e}", exc_info=True)

    def _edit_rule(self) -> None:
        """编辑选中的规则"""
        try:
            logger.debug("编辑选中的规则")
            current_item = self.keyword_rules_list.currentItem()
            if not current_item:
                logger.debug("未选中任何规则")
                return

            rule_data = current_item.data(Qt.ItemDataRole.UserRole)
            dialog = KeywordRuleDialog(rule_data, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_rule_data: Dict[str, Union[str, float, int, bool, None, Dict[str, Union[str, float, int, bool, None]]]] = dialog.get_rule_data()
                item_text: str = str(new_rule_data.get("pattern", ""))
                if not item_text:
                    item_text = "[空模式]"
                current_item.setText(item_text)
                current_item.setData(Qt.ItemDataRole.UserRole, new_rule_data)
                logger.debug(f"已编辑规则: {item_text}")
        except Exception as e:
            logger.error(f"编辑规则时出错: {e}", exc_info=True)

    def _get_keyword_rules(self) -> List[Dict[str, Union[str, float, int, bool, None]]]:
        """获取关键字规则列表"""
        rules: List[Dict[str, Union[str, float, int, bool, None]]] = []
        for i in range(self.keyword_rules_list.count()):
            item = self.keyword_rules_list.item(i)
            rule_data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(rule_data, dict):
                rules.append(rule_data)  # type: ignore
        return rules

    def _delete_rule(self) -> None:
        """删除选中的规则"""
        try:
            logger.debug("删除选中的规则")
            current_row = self.keyword_rules_list.currentRow()
            if current_row >= 0:
                self.keyword_rules_list.takeItem(current_row)
                logger.debug("已删除选中的规则")
        except Exception as e:
            logger.error(f"删除规则时出错: {e}", exc_info=True)

    def _move_rule_up(self) -> None:
        """上移选中的规则"""
        try:
            logger.debug("上移选中的规则")
            current_row = self.keyword_rules_list.currentRow()
            if current_row > 0:
                current_item = self.keyword_rules_list.takeItem(current_row)
                self.keyword_rules_list.insertItem(current_row - 1, current_item)
                self.keyword_rules_list.setCurrentRow(current_row - 1)
                logger.debug("已上移选中的规则")
        except Exception as e:
            logger.error(f"上移规则时出错: {e}", exc_info=True)

    def _move_rule_down(self) -> None:
        """下移选中的规则"""
        try:
            logger.debug("下移选中的规则")
            current_row = self.keyword_rules_list.currentRow()
            if 0 <= current_row < self.keyword_rules_list.count() - 1:
                current_item = self.keyword_rules_list.takeItem(current_row)
                self.keyword_rules_list.insertItem(current_row + 1, current_item)
                self.keyword_rules_list.setCurrentRow(current_row + 1)
                logger.debug("已下移选中的规则")
        except Exception as e:
            logger.error(f"下移规则时出错: {e}", exc_info=True)

    def _on_select_icon(self) -> None:
        """处理选择图标事件"""
        self.logic_handler.on_select_icon()

    def _on_clear_icon(self) -> None:
        """处理清除图标事件"""
        self.logic_handler.on_clear_icon()

    def _on_icon_changed(self, text: str) -> None:
        """处理图标文本变化事件

        Args:
            text (str): 新的图标文件名
        """
        self.logic_handler.on_icon_changed(text)

    def _update_icon_preview(self) -> None:
        """更新图标预览"""
        self.logic_handler.update_icon_preview()

    def _on_qt_quick_changed(self, state: Qt.CheckState) -> None:
        """当 Qt Quick 选项改变时，根据状态显示/隐藏渲染后端设置和透明度设置

        Args:
            state: Qt Quick 复选框的状态
        """
        self.logic_handler.on_qt_quick_changed(state)

    def _on_qt_quick_state_changed(self, state: int) -> None:
        """Qt Quick 复选框状态改变处理函数

        Args:
            state: Qt Quick 复选框的状态
        """
        self.logic_handler.on_qt_quick_state_changed(state)

    def _on_rendering_backend_changed(self, index: int) -> None:
        """当渲染后端改变时，根据是否为GPU模式控制透明度设置的可见性，
        并根据是否为默认样式和GPU模式控制GPU选项的可用性。

        Args:
            index: 渲染后端选择框的新索引
        """
        self.logic_handler.on_rendering_backend_changed(index)

    def _on_accept(self) -> None:
        """处理确定事件"""
        self.logic_handler.on_accept()

    def _on_cancel(self) -> None:
        """处理取消事件"""
        self.logic_handler.on_cancel()

    def _on_reset(self) -> None:
        """处理恢复默认事件"""
        self.logic_handler.on_reset()

    def _update_ui_from_config(self) -> None:
        """根据当前配置更新UI控件"""
        self.logic_handler.update_ui_from_config()