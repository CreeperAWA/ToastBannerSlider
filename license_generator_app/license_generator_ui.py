#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立许可证生成器
用于生成软件许可证的图形界面工具。
"""
import sys
import os
from datetime import datetime, timedelta
import wmi
import hashlib
import struct
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QDateEdit, QSpinBox, QTextEdit,
                               QMessageBox, QGroupBox, QFormLayout, QFrame, QScrollArea)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend


class ModernButton(QPushButton):
    """现代化按钮样式"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(44)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2a6496;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

    def setPrimaryStyle(self):
        """主按钮样式"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2a6496;
            }
        """)

    def setSecondaryStyle(self):
        """次要按钮样式"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #c0c0c0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)

    def setDangerStyle(self):
        """危险按钮样式（红色）"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)


class ModernLineEdit(QLineEdit):
    """现代化输入框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                color: #333333;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
                border-width: 2px;
                padding: 9px 15px;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
                color: #999999;
            }
        """)


class ModernTextEdit(QTextEdit):
    """现代化文本编辑框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                color: #333333;
            }
            QTextEdit:focus {
                border-color: #4a90e2;
                border-width: 2px;
                padding: 9px 15px;
            }
            QTextEdit:disabled {
                background-color: #f5f5f5;
                color: #999999;
            }
        """)


class ModernSpinBox(QSpinBox):
    """现代化数字输入框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                color: #333333;
            }
            QSpinBox:focus {
                border-color: #4a90e2;
                border-width: 2px;
                padding: 9px 15px;
            }
            QSpinBox:disabled {
                background-color: #f5f5f5;
                color: #999999;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 30px;
                border: none;
            }
            QSpinBox::up-button {
                subcontrol-position: top right;
                margin: 1px;
            }
            QSpinBox::down-button {
                subcontrol-position: bottom right;
                margin: 1px;
            }
        """)


class ModernDateEdit(QDateEdit):
    """现代化日期编辑框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setCalendarPopup(True)
        self.setStyleSheet("""
            QDateEdit {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                color: #333333;
            }
            QDateEdit:focus {
                border-color: #4a90e2;
                border-width: 2px;
                padding: 9px 15px;
            }
            QDateEdit:disabled {
                background-color: #f5f5f5;
                color: #999999;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #d0d0d0;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
                width: 0;
                height: 0;
            }
        """)


class ModernGroupBox(QGroupBox):
    """现代化分组框"""
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                margin-top: 2ex;
                background-color: rgba(255, 255, 255, 0.95);
                padding: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #4a90e2;
                font-size: 16px;
                font-weight: 600;
            }
        """)


class ModernLabel(QLabel):
    """现代化标签"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 14px;
                font-weight: 500;
            }
        """)


class HeaderWidget(QWidget):
    """标题栏组件 - 更新为UI2的设计"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 15, 24, 15)
        layout.setSpacing(15)

        # 应用图标和标题
        title_layout = QHBoxLayout()
        title_layout.setSpacing(15)

        # 图标
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        # Base64 图标数据
        base64_data = """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"""
        # 将 base64 数据转换为 QPixmap
        from PySide6.QtCore import QByteArray
        pixmap = QPixmap()
        try:
            pixmap.loadFromData(QByteArray.fromBase64(base64_data.encode()))
            icon_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            print(f"加载图标失败: {e}")
            # 如果加载失败，可以设置一个默认图标或留空

        title_label = QLabel("许可证签发")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; font-weight: bold;")

        subtitle_label = QLabel("为 ToastBannerSlider 签发许可证")
        subtitle_label.setStyleSheet("color: #7f8c8d; font-size: 13px;")

        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        layout.addWidget(subtitle_label)


class StatusWidget(QWidget):
    """状态信息组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(180)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.title_label = ModernLabel("状态信息")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")

        self.status_text = ModernTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(120)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                color: #495057;
            }
        """)

        layout.addWidget(self.title_label)
        layout.addWidget(self.status_text)


class LicenseGenerator:
    """许可证生成器核心功能类"""
    def __init__(self, private_key_file: str = "private.pem") -> None:
        """初始化许可证生成器
        Args:
            private_key_file: 私钥文件路径
        """
        self.private_key_file = private_key_file
        self.license_file = "License.key"
        self.private_key = None

    def get_hardware_info(self):
        """获取硬件信息
        Returns:
            dict: 包含CPU、硬盘和主板序列号的字典
        """
        hardware_info = {
            "cpu": "unknown",
            "disk": "unknown",
            "motherboard": "unknown"
        }
        try:
            # 使用WMI获取准确的硬件信息
            c = wmi.WMI()
            # 获取CPU序列号
            try:
                for processor in c.Win32_Processor():
                    if processor.ProcessorId:
                        hardware_info["cpu"] = processor.ProcessorId.strip()
                        break
            except Exception as e:
                print(f"获取CPU序列号失败: {e}")
            # 获取硬盘序列号
            try:
                for disk in c.Win32_DiskDrive():
                    if disk.SerialNumber:
                        hardware_info["disk"] = disk.SerialNumber.strip()
                        break
            except Exception as e:
                print(f"获取硬盘序列号失败: {e}")
            # 获取主板序列号
            try:
                for board in c.Win32_BaseBoard():
                    if board.SerialNumber:
                        hardware_info["motherboard"] = board.SerialNumber.strip()
                        break
            except Exception as e:
                print(f"获取主板序列号失败: {e}")
        except Exception as e:
            print(f"使用WMI获取硬件信息时出错: {e}")

        return hardware_info

    def generate_hardware_key(self):
        """生成硬件标识符
        Returns:
            str: 硬件标识符
        """
        hardware_info = self.get_hardware_info()
        hardware_string = f"{hardware_info['cpu']}|{hardware_info['disk']}|{hardware_info['motherboard']}"
        return self.multi_layer_hash(hardware_string)

    def multi_layer_hash(self, data: str) -> str:
        """多层哈希计算
        Args:
            data: 输入数据
        Returns:
            str: 多层哈希结果
        """
        # 第一层：SHA512
        sha512_hash = hashlib.sha512(data.encode('utf-8')).hexdigest()
        # 第二层：SHA384
        sha384_hash = hashlib.sha384(sha512_hash.encode('utf-8')).hexdigest()
        # 第三层：SHA3_512
        sha3_512_hash = hashlib.sha3_512(sha384_hash.encode('utf-8')).hexdigest()
        # 第四层：SHA3_384
        final_hash = hashlib.sha3_384(sha3_512_hash.encode('utf-8')).hexdigest()
        return final_hash

    def load_private_key(self):
        """加载私钥"""
        try:
            if os.path.exists(self.private_key_file):
                with open(self.private_key_file, "rb") as f:
                    private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=default_backend()
                    )
                self.private_key = private_key
                return True
            return False
        except Exception as e:
            print(f"加载私钥失败: {e}")
            return False

    def generate_key_pair(self):
        """生成RSA密钥对"""
        try:
            # 检查是否已存在密钥文件
            if os.path.exists("private.pem") or os.path.exists("public.pem"):
                reply = QMessageBox.question(
                    None, 
                    "确认", 
                    "密钥文件已存在，是否覆盖？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return False

            # 生成私钥
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
                backend=default_backend()
            )
            
            # 获取公钥
            public_key = private_key.public_key()
            
            # 序列化私钥
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # 序列化公钥
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # 保存私钥
            with open("private.pem", "wb") as f:
                f.write(private_pem)
            
            # 保存公钥
            with open("public.pem", "wb") as f:
                f.write(public_pem)
            
            self.private_key = private_key
            return True
            
        except Exception as e:
            print(f"生成密钥对时出错: {str(e)}")
            return False

    def generate_license(self, licensee: str, hardware_key: str, expiration_days: int):
        """生成带数字签名的许可证文件
        Args:
            licensee: 授权对象
            hardware_key: 硬件标识
            expiration_days: 授权天数
        Returns:
            bool: 是否成功生成许可证
        """
        try:
            # 检查私钥是否已加载
            if not self.private_key:
                if not self.load_private_key():
                    print("错误：无法加载私钥")
                    return False

            # 计算过期时间
            expiration_date = datetime.now().replace(microsecond=0) + timedelta(days=expiration_days)

            # 创建许可证数据（纯二进制格式）
            # 格式: [licensee_length(4字节)][licensee_bytes][expiration_timestamp(8字节)][hardware_key_length(4字节)][hardware_key_bytes]
            licensee_bytes = licensee.encode('utf-8')
            licensee_length = len(licensee_bytes)
            # 将过期时间转换为时间戳
            expiration_timestamp = int(expiration_date.timestamp())
            hardware_key_bytes = hardware_key.encode('utf-8')
            hardware_key_length = len(hardware_key_bytes)

            # 构造许可证数据
            license_data = struct.pack('<I', licensee_length) + licensee_bytes
            license_data += struct.pack('<Q', expiration_timestamp)
            license_data += struct.pack('<I', hardware_key_length) + hardware_key_bytes

            # 对许可证数据进行签名
            signature = self.private_key.sign(
                license_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA512()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA512()
            )

            # 构造二进制许可证文件: [license_data_bytes][signature_bytes]
            final_data = license_data + signature

            print(f"许可证数据大小: {len(license_data)} 字节")
            print(f"完整许可证文件大小: {len(final_data)} 字节")
            print(f"授权对象: {licensee}")
            print(f"过期时间: {expiration_date.isoformat()}")
            print(f"硬件标识: {hardware_key}")
            print(f"签名长度: {len(signature)} 字节")

            # 直接保存为二进制文件
            with open(self.license_file, "wb") as f:
                f.write(final_data)

            print(f"带数字签名的许可证已生成并保存到 {self.license_file}")

            # 显示获取到的硬件信息
            hardware_info = self.get_hardware_info()
            print(f"获取到的硬件信息:")
            print(f"  CPU序列号: {hardware_info['cpu']}")
            print(f"  硬盘序列号: {hardware_info['disk']}")
            print(f"  主板序列号: {hardware_info['motherboard']}")
            
            return True

        except Exception as e:
            print(f"生成带签名的许可证时出错: {e}")
            import traceback
            traceback.print_exc()
            return False


class LicenseGeneratorUI(QMainWindow):
    """许可证生成器主界面"""
    def __init__(self):
        """初始化许可证生成器界面"""
        super().__init__()
        self.license_manager = LicenseGenerator()  # 使用实例
        self.init_ui()
        self.load_current_hardware_info()

    def init_ui(self):
        """初始化用户界面 - 现代化设计"""
        self.setWindowTitle("许可证生成器")
        self.setGeometry(100, 100, 850, 700)  # 减小默认高度从1000到700
        self.setMinimumSize(750, 600)  # 减小最小高度从900到600

        # 设置现代化样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # 创建中央滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setCentralWidget(scroll_area)

        # 创建内容部件
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # 标题栏
        header_widget = HeaderWidget()
        main_layout.addWidget(header_widget)

        # 主内容区域
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setSpacing(25)

        # 机器码输入区域
        hardware_group = ModernGroupBox("机器码信息")
        hardware_layout = QFormLayout()
        hardware_layout.setLabelAlignment(Qt.AlignLeft)
        hardware_layout.setHorizontalSpacing(25)
        hardware_layout.setVerticalSpacing(18)
        hardware_layout.setContentsMargins(25, 25, 25, 25)

        self.hardware_key_edit = ModernTextEdit()
        self.hardware_key_edit.setFixedHeight(100)
        self.hardware_key_edit.setPlaceholderText("请输入目标机器的硬件标识...")
        hardware_layout.addRow("硬件标识:", self.hardware_key_edit)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.current_machine_button = ModernButton("使用当前机器码")
        self.current_machine_button.setSecondaryStyle()
        self.current_machine_button.clicked.connect(self.load_current_hardware_info)
        button_layout.addWidget(self.current_machine_button)
        hardware_layout.addRow("", button_layout)

        hardware_group.setLayout(hardware_layout)
        content_layout.addWidget(hardware_group)

        # 授权信息区域
        license_group = ModernGroupBox("授权信息")
        license_layout = QFormLayout()
        license_layout.setLabelAlignment(Qt.AlignLeft)
        license_layout.setHorizontalSpacing(25)
        license_layout.setVerticalSpacing(18)
        license_layout.setContentsMargins(25, 25, 25, 25)

        # 授权对象
        self.licensee_edit = ModernLineEdit()
        self.licensee_edit.setPlaceholderText("请输入授权对象名称")
        license_layout.addRow("授权对象:", self.licensee_edit)

        # 有效期设置方式1：天数
        self.days_spinbox = ModernSpinBox()
        self.days_spinbox.setRange(1, 2912530)  # 8年左右
        self.days_spinbox.setValue(365)  # 默认1年
        self.days_spinbox.setSuffix(" 天")
        license_layout.addRow("授权天数:", self.days_spinbox)

        # 有效期设置方式2：截止日期
        self.expiration_date_edit = ModernDateEdit()
        self.expiration_date_edit.setDisplayFormat("yyyy年MM月dd日")
        self.expiration_date_edit.setDate(QDate.currentDate().addDays(365))  # 默认1年
        self.expiration_date_edit.setMinimumDate(QDate.currentDate().addDays(1))  # 最早不能早于明天
        license_layout.addRow("截止日期:", self.expiration_date_edit)

        # 同步天数和日期
        self.days_spinbox.valueChanged.connect(self.on_days_changed)
        self.expiration_date_edit.dateChanged.connect(self.on_date_changed)

        license_group.setLayout(license_layout)
        content_layout.addWidget(license_group)

        # 操作按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("background-color: transparent;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 15, 0, 15)
        button_layout.setSpacing(20)

        # 生成密钥对按钮
        self.generate_key_btn = ModernButton("生成密钥对")
        self.generate_key_btn.setSecondaryStyle()
        self.generate_key_btn.clicked.connect(self.generate_key_pair)

        self.generate_button = ModernButton("生成许可证")
        self.generate_button.setPrimaryStyle()
        self.generate_button.clicked.connect(self.generate_license)

        self.clear_button = ModernButton("清空")
        self.clear_button.setDangerStyle()
        self.clear_button.clicked.connect(self.clear_fields)

        button_layout.addWidget(self.generate_key_btn)  # 添加生成密钥对按钮
        button_layout.addStretch()
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()

        content_layout.addWidget(button_frame)

        # 状态信息区域
        self.status_widget = StatusWidget()
        content_layout.addWidget(self.status_widget)

        # 添加弹性空间
        content_layout.addStretch()
        main_layout.addWidget(content_area)

        # 设置状态栏
        self.statusBar().showMessage("就绪")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #2c3e50;
                color: white;
                font-size: 13px;
                padding: 8px;
            }
        """)

    def load_current_hardware_info(self):
        """加载当前机器的硬件信息"""
        try:
            hardware_key = self.license_manager.generate_hardware_key()  # 使用实例方法
            self.hardware_key_edit.setPlainText(hardware_key)
            self.statusBar().showMessage("已加载当前机器码")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法获取当前机器码: {str(e)}")

    def on_days_changed(self, days):
        """当授权天数改变时，同步更新截止日期"""
        current_date = QDate.currentDate()
        new_date = current_date.addDays(days)
        self.expiration_date_edit.setDate(new_date)

    def on_date_changed(self, date):
        """当截止日期改变时，同步更新授权天数"""
        current_date = QDate.currentDate()
        days = current_date.daysTo(date)
        if days > 0:
            self.days_spinbox.setValue(days)

    def generate_key_pair(self):
        """生成密钥对"""
        try:
            success = self.license_manager.generate_key_pair()
            if success:
                message = """密钥对生成成功！
私钥已保存到 private.pem
公钥已保存到 public.pem

请妥善保管私钥文件，不要泄露给他人。
公钥文件可以分发给客户端使用。"""
                self.status_widget.status_text.setPlainText(message)
                QMessageBox.information(self, "成功", "密钥对已生成并保存")
                self.statusBar().showMessage("密钥对生成成功")
            else:
                QMessageBox.critical(self, "错误", "密钥对生成失败")
                self.statusBar().showMessage("密钥对生成失败")
        except Exception as e:
            error_msg = f"生成密钥对时出错: {str(e)}"
            QMessageBox.critical(self, "错误", error_msg)
            self.status_widget.status_text.setPlainText(error_msg)
            self.statusBar().showMessage("密钥对生成失败")

    def generate_license(self):
        """生成许可证"""
        try:
            # 获取输入信息 - 使用UI输入的hardware_key
            hardware_key = self.hardware_key_edit.toPlainText().strip()
            licensee = self.licensee_edit.text().strip()
            days = self.days_spinbox.value()

            if not hardware_key:
                QMessageBox.warning(self, "警告", "请输入硬件标识")
                return
            if not licensee:
                QMessageBox.warning(self, "警告", "请输入授权对象")
                return

            # 生成许可证 - 直接使用UI输入的hardware_key
            success = self.license_manager.generate_license(licensee, hardware_key, days)
            if success:
                expiration_date = datetime.now() + timedelta(days=days)
                message = f"""许可证生成成功！
授权对象: {licensee}
授权天数: {days} 天
截止日期: {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}
硬件标识: {hardware_key[:50]}...
"""
                self.status_widget.status_text.setPlainText(message)
                QMessageBox.information(self, "成功", "许可证已生成并保存到 License.key")
                self.statusBar().showMessage("许可证生成成功")
            else:
                QMessageBox.critical(self, "错误", "许可证生成失败")
                self.statusBar().showMessage("许可证生成失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成许可证时出错: {str(e)}")
            self.statusBar().showMessage("许可证生成失败")

    def clear_fields(self):
        """清空所有输入字段"""
        self.hardware_key_edit.clear()
        self.licensee_edit.clear()
        self.days_spinbox.setValue(365)
        self.expiration_date_edit.setDate(QDate.currentDate().addYears(1))
        self.status_widget.status_text.clear()
        self.statusBar().showMessage("已清空所有字段")


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle("Fusion")

    # 设置调色板
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(248, 249, 250))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(248, 249, 250))
    palette.setColor(QPalette.ToolTipBase, QColor(44, 62, 80))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(51, 51, 51))
    palette.setColor(QPalette.Button, QColor(74, 144, 226))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(231, 76, 60))
    palette.setColor(QPalette.Link, QColor(74, 144, 226))
    palette.setColor(QPalette.Highlight, QColor(74, 144, 226))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    # 创建并显示主窗口
    window = LicenseGeneratorUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()