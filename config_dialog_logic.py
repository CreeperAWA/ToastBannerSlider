"""配置对话框逻辑模块

该模块提供配置对话框的核心业务逻辑处理功能。
"""

from PySide6.QtWidgets import (QWidget, QListWidgetItem, QPushButton, QFileDialog, QMessageBox, QLabel, QLineEdit,
                              QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox)
from PySide6.QtCore import (QObject, Qt, QEvent, QAbstractItemModel)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtGui import QStandardItemModel
from logger_config import logger
from config import save_config, get_config_path, DEFAULT_CONFIG
from icon_manager import load_icon, get_resource_path, save_custom_icon
import os
import typing
from typing import List, Dict, Union


class TrayIconUpdateEvent(QEvent):
    """托盘图标更新事件"""
    def __init__(self) -> None:
        super().__init__(QEvent.Type(QEvent.registerEventType()))


# 定义ConfigDialog类型，避免循环导入
class ConfigDialog(QWidget):
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
    banner_opacity_label: QLabel
    banner_opacity_spinbox: QDoubleSpinBox
    scroll_mode_combo: QComboBox
    log_level_combo: QComboBox
    ignore_duplicate_checkbox: QCheckBox
    dnd_checkbox: QCheckBox
    rendering_backend_combo: QComboBox
    banner_style_combo: QComboBox
    icon_edit: QLineEdit
    icon_preview_label: QLabel
    enable_qt_quick_checkbox: QCheckBox
    keyword_rules_list: QListWidgetItem
    
    # 按钮属性
    ok_button: QPushButton
    cancel_button: QPushButton
    reset_button: QPushButton
    
    def __init__(self) -> None:
        pass
    
    def setWindowIcon(self, icon: Union[QIcon, QPixmap]) -> None:
        pass
    
    def accept(self) -> None:
        pass
    
    def reject(self) -> None:
        pass
    
    def parent(self) -> QObject:
        return QObject()
    
    def _on_icon_changed(self, text: str) -> None:
        pass
    
    def _on_accept(self) -> None:
        pass
    
    def _on_cancel(self) -> None:
        pass
    
    def _on_rendering_backend_changed(self, index: int) -> None:
        pass
    
    def _update_icon_preview(self) -> None:
        pass
    
    def _get_keyword_rules(self) -> List[Dict[str, Union[str, float, int, bool, None]]]:
        return []
    
    def _update_ui_from_config(self) -> None:
        pass
    
    def _load_keyword_rules(self) -> None:
        pass
    
    def _on_qt_quick_changed(self, state: Qt.CheckState) -> None:
        pass


class ConfigDialogLogic:
    """配置对话框逻辑处理器"""

    def __init__(self, dialog: ConfigDialog, config: Dict[str, Union[str, float, int, bool, None]]) -> None:
        """
        初始化配置对话框逻辑处理器

        Args:
            dialog: 父级对话框实例
            config: 配置数据
        """
        self.dialog = dialog
        self.config = config

    def set_window_icon(self) -> None:
        """设置配置对话框窗口图标"""
        try:
            logger.debug("设置配置对话框窗口图标")

            # 加载图标
            icon = load_icon(self.config)
            if not icon.isNull():
                self.dialog.setWindowIcon(icon)
                logger.debug("配置对话框窗口图标设置成功")
            else:
                logger.warning("配置对话框窗口图标为空")
        except Exception as e:
            logger.error(f"设置配置对话框窗口图标时出错: {e}")

    def connect_signals(self) -> None:
        """连接信号"""
        try:
            logger.debug("连接配置对话框信号")

            # 连接图标选择相关信号
            if hasattr(self.dialog, 'icon_edit') and self.dialog.icon_edit:
                self.dialog.icon_edit.textChanged.connect(self.dialog._on_icon_changed)

            # 连接确定按钮
            self.dialog.ok_button.clicked.connect(self.dialog._on_accept)  # 修复方法名不匹配问题

            # 连接取消按钮
            self.dialog.cancel_button.clicked.connect(self.dialog._on_cancel)

            # 连接渲染后端选择框变化信号
            self.dialog.rendering_backend_combo.currentIndexChanged.connect(self.dialog._on_rendering_backend_changed)

            logger.debug("配置对话框信号连接完成")
        except Exception as e:
            logger.error(f"连接配置对话框信号时出错: {e}", exc_info=True)

    def on_select_icon(self) -> None:
        """处理选择图标事件"""
        try:
            logger.debug("处理选择图标事件")

            # 打开文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self.dialog,
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
                    self.dialog.icon_edit.setText(str(saved_filename))

                    # 更新图标预览
                    self.dialog._update_icon_preview()

                    logger.debug(f"图标文件已保存并重命名为: {saved_filename}")
                else:
                    logger.error("保存图标文件失败")
                    QMessageBox.critical(self.dialog, "错误", "保存图标文件失败")
            else:
                logger.debug("未选择图标文件")
        except Exception as e:
            logger.error(f"处理选择图标事件时出错: {e}")
            QMessageBox.critical(self.dialog, "错误", f"选择图标文件时出错: {e}")

    def on_clear_icon(self) -> None:
        """处理清除图标事件"""
        try:
            logger.debug("处理清除图标事件")

            # 只清除编辑框，不立即删除文件
            self.dialog.icon_edit.clear()

            logger.debug("图标已清除")
        except Exception as e:
            logger.error(f"处理清除图标事件时出错: {e}")
            QMessageBox.critical(self.dialog, "错误", f"清除图标文件时出错: {e}")

    def on_icon_changed(self, text: str) -> None:
        """处理图标文本变化事件

        Args:
            text (str): 新的图标文件名
        """
        try:
            logger.debug(f"处理图标文本变化事件: {text}")
            self.dialog._update_icon_preview()
        except Exception as e:
            logger.error(f"处理图标文本变化事件时出错: {e}")

    def update_icon_preview(self) -> None:
        """更新图标预览"""
        try:
            logger.debug("更新图标预览")

            icon_text = self.dialog.icon_edit.text().strip()
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
                            available_sizes = icon.availableSizes()
                            if available_sizes:
                                pixmap = icon.pixmap(available_sizes[0])
                            else:
                                pixmap = QPixmap(48, 48)
                                pixmap.fill(Qt.GlobalColor.transparent)  # 使用透明背景
                        # 缩放到预览框大小，使用平滑变换
                        pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.dialog.icon_preview_label.setPixmap(pixmap)
                        logger.debug(f"图标预览已更新: {icon_path}")
                        return

            # 使用默认图标预览
            logger.debug("使用默认图标预览")
            # 尝试加载notification_icon.ico
            resource_icon_path = get_resource_path("notification_icon.ico")
            logger.debug(f"尝试加载ICO图标: {resource_icon_path}")
            if os.path.exists(resource_icon_path):
                icon = QIcon(resource_icon_path)
                if not icon.isNull():
                    pixmap = icon.pixmap(48, 48, QIcon.Mode.Normal, QIcon.State.On)
                    available_sizes = icon.availableSizes()
                    if pixmap.isNull() and available_sizes:
                        pixmap = icon.pixmap(available_sizes[0])
                    if not pixmap.isNull():
                        # 缩放到预览框大小，使用平滑变换
                        pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.dialog.icon_preview_label.setPixmap(pixmap)
                        logger.debug("已显示notification_icon.ico默认图标")
                        return

            # 尝试加载notification_icon.png
            resource_icon_path = get_resource_path("notification_icon.png")
            logger.debug(f"尝试加载PNG图标: {resource_icon_path}")
            if os.path.exists(resource_icon_path):
                icon = QIcon(resource_icon_path)
                if not icon.isNull():
                    pixmap = icon.pixmap(48, 48, QIcon.Mode.Normal, QIcon.State.On)
                    available_sizes = icon.availableSizes()
                    if pixmap.isNull() and available_sizes:
                        pixmap = icon.pixmap(available_sizes[0])
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.dialog.icon_preview_label.setPixmap(pixmap)
                        logger.debug("已显示notification_icon.png默认图标")
                        return

            # 如果所有尝试都失败了，创建一个简单的默认图像
            pixmap = QPixmap(48, 48)
            pixmap.fill(Qt.GlobalColor.transparent)  # 使用透明背景
            self.dialog.icon_preview_label.setPixmap(pixmap)
            logger.debug("使用透明背景作为默认图标")
        except Exception as e:
            logger.error(f"更新图标预览时出错: {e}")
            # 出错时显示一个简单的默认图像
            try:
                pixmap = QPixmap(48, 48)
                pixmap.fill(Qt.GlobalColor.transparent)  # 使用透明背景
                self.dialog.icon_preview_label.setPixmap(pixmap)
            except Exception as e2:
                logger.error(f"设置默认图标预览时出错: {e2}")

    def on_qt_quick_changed(self, state: Qt.CheckState) -> None:
        """当 Qt Quick 选项改变时，根据状态显示/隐藏渲染后端设置和透明度设置

        Args:
            state: Qt Quick 复选框的状态
        """
        logger.debug(f"Qt Quick 选项改变，状态: {state}")
        if state == Qt.CheckState.Checked:
            # 启用 Qt Quick 时隐藏渲染后端设置，但显示透明度设置
            self.dialog.rendering_backend_combo.hide()
            # 查找渲染后端标签并隐藏它
            label = self.dialog.rendering_backend_combo.parent().findChild(QLabel, "rendering_backend_label")
            if label:
                label.hide()

            # 显示透明度设置（QML渲染需要透明度设置）
            self.dialog.banner_opacity_spinbox.show()
            self.dialog.banner_opacity_label.show()

            logger.debug("隐藏渲染后端设置，显示透明度设置")
        else:
            # 禁用 Qt Quick 时显示渲染后端设置，透明度设置的显示由渲染后端决定
            self.dialog.rendering_backend_combo.show()
            # 查找渲染后端标签并显示它
            label = self.dialog.rendering_backend_combo.parent().findChild(QLabel, "rendering_backend_label")
            if label:
                label.show()

            # 透明度设置的显示由渲染后端决定
            self.dialog._on_rendering_backend_changed(self.dialog.rendering_backend_combo.currentIndex())

            logger.debug("显示渲染后端设置，透明度设置由渲染后端决定")

    def on_qt_quick_state_changed(self, state: int) -> None:
        """Qt Quick 复选框状态改变处理函数

        Args:
            state: Qt Quick 复选框的状态
        """
        self.on_qt_quick_changed(Qt.CheckState(state))

    def update_gpu_options_enabled(self) -> None:
        """根据当前横幅样式更新GPU选项的启用/禁用状态"""
        current_style = self.dialog.banner_style_combo.currentData()
        gpu_items = ["opengl", "opengles"]

        # 获取模型
        model: QAbstractItemModel = self.dialog.rendering_backend_combo.model()

        if current_style == "default":
            # 使用默认横幅样式时不允许选择GPU渲染
            for i in range(self.dialog.rendering_backend_combo.count()):
                item_data = self.dialog.rendering_backend_combo.itemData(i)
                if item_data in gpu_items:
                    index = model.index(i, 0)
                    item = model.data(index, Qt.ItemDataRole.UserRole)
                    if index.isValid():
                        flags = model.flags(index)
                        # 移除启用标志
                        flags = flags & ~Qt.ItemFlag.ItemIsEnabled
                        # 通过模型索引获取项并设置标志
                        item = typing.cast(QStandardItemModel, model).itemFromIndex(index)
                        if hasattr(item, 'setFlags'):
                            item.setFlags(flags)
                        logger.debug(f"禁用GPU选项: {item_data}")
        else:
            # 使用警告样式时，GPU选项可用
            for i in range(self.dialog.rendering_backend_combo.count()):
                item_data = self.dialog.rendering_backend_combo.itemData(i)
                if item_data in gpu_items:
                    index = model.index(i, 0)
                    item = model.data(index, Qt.ItemDataRole.UserRole)
                    if index.isValid():
                        flags = model.flags(index)
                        # 添加启用标志
                        flags = flags | Qt.ItemFlag.ItemIsEnabled
                        # 通过模型索引获取项并设置标志
                        item = typing.cast(QStandardItemModel, model).itemFromIndex(index)
                        if hasattr(item, 'setFlags'):
                            item.setFlags(flags)
                        logger.debug(f"启用GPU选项: {item_data}")

    def on_rendering_backend_changed(self, index: int) -> None:
        """当渲染后端改变时，根据是否为GPU模式控制透明度设置的可见性，
        并根据是否为默认样式和GPU模式控制GPU选项的可用性。

        Args:
            index: 渲染后端选择框的新索引
        """
        logger.debug(f"渲染后端改变，索引: {index}")
        current_backend = self.dialog.rendering_backend_combo.currentData()
        is_gpu = current_backend in ["opengl", "opengles"]

        # 控制透明度设置的可见性
        # 移除隐藏透明度设置的逻辑，始终显示透明度设置
        # if is_gpu:
        #     # 使用GPU模式渲染时隐藏透明度设置
        #     self.dialog.banner_opacity_spinbox.hide()
        #     self.dialog.banner_opacity_label.hide()
        #     logger.debug("隐藏透明度设置")
        # else:
        #     # 非GPU模式时显示透明度设置
        #     self.dialog.banner_opacity_spinbox.show()
        #     self.dialog.banner_opacity_label.show()
        #     logger.debug("显示透明度设置")
        
        # 始终显示透明度设置
        self.dialog.banner_opacity_spinbox.show()
        self.dialog.banner_opacity_label.show()
        logger.debug("显示透明度设置")

        # 更新GPU选项的启用/禁用状态
        self.update_gpu_options_enabled()

        # 检查当前是否为GPU模式，如果是且样式为默认，则强制切换回默认渲染后端
        current_style = self.dialog.banner_style_combo.currentData()
        if current_style == "default" and is_gpu:
            default_index = self.dialog.rendering_backend_combo.findData("default")
            if default_index >= 0:
                self.dialog.rendering_backend_combo.setCurrentIndex(default_index)
                logger.debug("因默认样式，强制切换回默认渲染后端")
                # 重新调用此函数以更新透明度显示状态和选项可用性
                # 注意：这里重新调用后，is_gpu 会变为 False，因此不会再进入这个分支
                self.on_rendering_backend_changed(default_index)

    def on_accept(self) -> None:
        """处理确定事件"""
        try:
            logger.debug("处理确定事件")

            # 保存当前配置（用于比较图标是否变化）
            old_icon = self.config.get("custom_icon")

            # 构建新配置
            new_config: Dict[str, Union[str, float, int, bool, List[Dict[str, Union[str, float, int, bool, None]]], None]] = {
                # 基本设置
                "notification_title": self.dialog.title_edit.text(),
                "scroll_speed": self.dialog.speed_spinbox.value(),
                "scroll_count": self.dialog.scroll_count_spinbox.value(),
                "click_to_close": self.dialog.click_close_spinbox.value(),

                # 显示设置
                "label_spacing": self.dialog.spacing_spinbox.value(),
                "font_size": self.dialog.font_size_spinbox.value(),
                "left_margin": self.dialog.left_margin_spinbox.value(),
                "right_margin": self.dialog.right_margin_spinbox.value(),
                "icon_scale": self.dialog.icon_scale_spinbox.value(),
                "label_offset_x": self.dialog.label_offset_x_spinbox.value(),
                "window_height": self.dialog.window_height_spinbox.value(),
                "label_mask_width": self.dialog.label_mask_width_spinbox.value(),
                "banner_spacing": self.dialog.banner_spacing_spinbox.value(),
                "base_vertical_offset": self.dialog.base_vertical_offset_spinbox.value(),
                "banner_opacity": self.dialog.banner_opacity_spinbox.value(),
                "scroll_mode": self.dialog.scroll_mode_combo.currentData(),
                "banner_style": self.dialog.banner_style_combo.currentData(),

                # 动画设置
                "shift_animation_duration": self.dialog.shift_duration_spinbox.value(),
                "fade_animation_duration": self.dialog.fade_duration_spinbox.value(),

                # 高级设置
                "log_level": self.dialog.log_level_combo.currentData(),
                "ignore_duplicate": self.dialog.ignore_duplicate_checkbox.isChecked(),
                "do_not_disturb": self.dialog.dnd_checkbox.isChecked(),
                "rendering_backend": self.dialog.rendering_backend_combo.currentData(),
                "enable_qt_quick": self.dialog.enable_qt_quick_checkbox.isChecked(),

                # 图标设置
                "custom_icon": self.dialog.icon_edit.text() or None,

                # 关键字替换
                "keyword_replacements": self.dialog._get_keyword_rules()
            }

            # 转换配置类型以匹配 save_config 函数的期望类型
            save_config_data: Dict[str, Union[str, float, int, bool, None]] = {}
            for key, value in new_config.items():
                if key != "keyword_replacements":
                    save_config_data[key] = value  # type: ignore
            save_config_data["keyword_replacements"] = new_config["keyword_replacements"]  # type: ignore

            # 保存新配置
            if save_config(save_config_data):
                logger.info("配置已保存")

                # 更新当前配置
                self.config = save_config_data  # type: ignore

                # 重新加载关键字替换规则
                try:
                    from keyword_replacer import reload_keyword_rules
                    reload_keyword_rules()
                    logger.debug("关键字替换规则已重新加载")
                except Exception as e:
                    logger.error(f"重新加载关键字替换规则时出错: {e}")

                # 如果图标发生变化，删除旧图标文件（如果不再使用）
                new_icon = self.config.get("custom_icon")
                if old_icon and isinstance(old_icon, str) and old_icon != new_icon:
                    # 检查旧图标是否还在使用
                    if not self._is_icon_in_use(old_icon):
                        # 删除旧图标文件
                        config_dir = os.path.dirname(get_config_path())
                        icons_dir = os.path.join(config_dir, "icons")
                        old_icon_path = os.path.join(icons_dir, old_icon)
                        if os.path.exists(old_icon_path):
                            try:
                                os.remove(old_icon_path)
                                logger.debug(f"已删除旧图标文件: {old_icon_path}")
                            except Exception as e:
                                logger.error(f"删除旧图标文件失败: {old_icon_path}, 错误: {e}")

                # 如果图标发生变化，通知主程序更新托盘图标
                if (old_icon is None and new_icon is not None) or \
                   (old_icon is not None and new_icon is None) or \
                   (old_icon != new_icon):
                    if hasattr(self.dialog, 'parent') and self.dialog.parent() and hasattr(self.dialog.parent(), 'update_config'):
                        try:
                            self.dialog.parent().update_config()  # type: ignore
                        except Exception:
                            pass
                self.dialog.accept()
            else:
                logger.error("保存配置失败")
                QMessageBox.critical(self.dialog, "错误", "保存配置失败")
        except Exception as e:
            logger.error(f"处理确定事件时出错: {e}", exc_info=True)
            QMessageBox.critical(self.dialog, "错误", f"保存配置时出错: {e}")

    def _is_icon_in_use(self, icon_filename: str) -> bool:
        """检查图标文件是否还在使用中
        
        Args:
            icon_filename: 图标文件名
            
        Returns:
            bool: 如果图标还在使用中返回True，否则返回False
        """
        # 检查当前配置是否还在使用这个图标
        current_icon = self.config.get("custom_icon")
        if current_icon == icon_filename:
            return True
            
        # 检查关键字规则中是否使用了这个图标
        keyword_rules = self.dialog._get_keyword_rules()
        for rule in keyword_rules:
            # 如果将来关键字规则中可以设置图标，可以在这里检查
            pass
            
        return False

    def on_cancel(self) -> None:
        """处理取消事件"""
        try:
            logger.debug("处理取消事件")
            # 拒绝对话框
            self.dialog.reject()
        except Exception as e:
            logger.error(f"处理取消事件时出错: {e}", exc_info=True)

    def on_reset(self) -> None:
        """处理恢复默认事件"""
        try:
            logger.debug("处理恢复默认事件")

            # 弹出确认对话框
            msg_box = QMessageBox(self.dialog)
            msg_box.setWindowTitle("确认")
            msg_box.setText("确定要恢复所有设置为默认值吗？")
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)

            # 设置按钮文本为中文
            yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
            if yes_button:
                yes_button.setText("是")

            no_button = msg_box.button(QMessageBox.StandardButton.No)
            if no_button:
                no_button.setText("否")

            reply = msg_box.exec()
            logger.debug(f"用户选择: {reply}")

            if reply == QMessageBox.StandardButton.Yes:
                logger.debug("用户确认恢复默认设置")

                # 临时保存当前图标设置，因为图标文件需要特殊处理
                current_icon = self.config.get("custom_icon")

                # 恢复默认配置
                self.config = DEFAULT_CONFIG.copy()

                # 保留当前图标设置
                if current_icon:
                    self.config["custom_icon"] = current_icon

                # 更新UI控件
                self.dialog._update_ui_from_config()

                logger.debug("默认设置已恢复")
            else:
                logger.debug("用户取消恢复默认设置")
                return  # 直接返回，避免继续执行
        except Exception as e:
            logger.error(f"处理恢复默认事件时出错: {e}", exc_info=True)
            QMessageBox.critical(self.dialog, "错误", f"恢复默认设置时出错: {e}")

    def update_ui_from_config(self) -> None:
        """根据当前配置更新UI控件"""
        try:
            logger.debug("根据配置更新UI控件")

            # 基本设置
            self.dialog.title_edit.setText(str(self.config.get("notification_title", "911 呼唤群")))
            self.dialog.speed_spinbox.setValue(float(self.config.get("scroll_speed", 200.0) or 200.0))
            self.dialog.scroll_count_spinbox.setValue(int(self.config.get("scroll_count", 3) or 3))
            self.dialog.click_close_spinbox.setValue(int(self.config.get("click_to_close", 3) or 3))

            # 显示设置
            current_style = self.config.get("banner_style", "default")
            style_index = self.dialog.banner_style_combo.findData(current_style)
            if style_index >= 0:
                self.dialog.banner_style_combo.setCurrentIndex(style_index)

            self.dialog.spacing_spinbox.setValue(int(self.config.get("right_spacing", 150) or 150))
            self.dialog.font_size_spinbox.setValue(float(self.config.get("font_size", 48.0) or 48.0))
            self.dialog.left_margin_spinbox.setValue(int(self.config.get("left_margin", 93) or 93))
            self.dialog.right_margin_spinbox.setValue(int(self.config.get("right_margin", 93) or 93))
            self.dialog.icon_scale_spinbox.setValue(float(self.config.get("icon_scale", 1.0) or 1.0))
            self.dialog.label_offset_x_spinbox.setValue(int(self.config.get("label_offset_x", 0) or 0))
            self.dialog.window_height_spinbox.setValue(int(self.config.get("window_height", 128) or 128))
            self.dialog.label_mask_width_spinbox.setValue(int(self.config.get("label_mask_width", 305) or 305))
            self.dialog.banner_spacing_spinbox.setValue(int(self.config.get("banner_spacing", 10) or 10))
            self.dialog.base_vertical_offset_spinbox.setValue(int(self.config.get("base_vertical_offset", 50) or 50))
            self.dialog.banner_opacity_spinbox.setValue(float(self.config.get("banner_opacity", 0.9) or 0.9))

            current_mode = self.config.get("scroll_mode", "always")
            mode_index = self.dialog.scroll_mode_combo.findData(current_mode)
            if mode_index >= 0:
                self.dialog.scroll_mode_combo.setCurrentIndex(mode_index)

            # 动画设置
            self.dialog.shift_duration_spinbox.setValue(int(self.config.get("shift_animation_duration", 100) or 100))
            self.dialog.fade_duration_spinbox.setValue(int(self.config.get("fade_animation_duration", 1500) or 1500))

            # 高级设置
            current_level = self.config.get("log_level", "INFO")
            level_index = self.dialog.log_level_combo.findData(current_level)
            if level_index >= 0:
                self.dialog.log_level_combo.setCurrentIndex(level_index)

            self.dialog.ignore_duplicate_checkbox.setChecked(bool(self.config.get("ignore_duplicate", False)))
            self.dialog.dnd_checkbox.setChecked(bool(self.config.get("do_not_disturb", False)))
            qt_quick_enabled = bool(self.config.get("enable_qt_quick", False))
            self.dialog.enable_qt_quick_checkbox.setChecked(qt_quick_enabled)  # 添加 Qt Quick 选项

            current_backend = self.config.get("rendering_backend", "default")
            backend_index = self.dialog.rendering_backend_combo.findData(current_backend)
            if backend_index >= 0:
                self.dialog.rendering_backend_combo.setCurrentIndex(backend_index)
            else:
                # 如果找不到对应的数据，设置为默认值
                default_index = self.dialog.rendering_backend_combo.findData("default")
                if default_index >= 0:
                    self.dialog.rendering_backend_combo.setCurrentIndex(default_index)

            # 将Qt Quick的状态更新移到最后，确保所有依赖于此的UI都已更新
            self.dialog._on_qt_quick_changed(self.dialog.enable_qt_quick_checkbox.checkState())

            # 图标设置
            current_icon = self.config.get("custom_icon")
            if current_icon:
                self.dialog.icon_edit.setText(str(current_icon))
            else:
                self.dialog.icon_edit.clear()

            # 更新图标预览
            self.dialog._update_icon_preview()

            # 更新关键字规则
            self.dialog._load_keyword_rules()

            logger.debug("UI控件更新完成")
        except Exception as e:
            logger.error(f"根据配置更新UI控件时出错: {e}", exc_info=True)