"""许可证管理模块

该模块负责处理软件许可证验证，包括硬件信息获取、多重哈希验证和许可证管理。
"""

import hashlib
import hmac
import os
import sys
import json
import base64
import subprocess
import re
import uuid
import wmi
import struct
from datetime import datetime
from typing import Dict, Optional, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QTextEdit, QGroupBox, QGridLayout, QFrame, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPalette
from logger_config import logger


def get_resource_path(relative_path):
    """获取资源文件的绝对路径，采用与配置文件相同的策略"""
    if getattr(sys, 'frozen', False):
        # 打包后的程序
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境，使用sys.argv[0]而不是__file__
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
    return os.path.join(base_dir, relative_path)


class LicenseManager:
    """许可证管理器"""
    
    def __init__(self) -> None:
        """初始化许可证管理器"""
        self.license_file = "License.key"
        self.public_key_file = get_resource_path("public.pem")
        self.private_key_file = "private.pem"
        # 添加硬件信息缓存
        self._hardware_info: Optional[Dict[str, str]] = None
        self._hardware_key: Optional[str] = None
        
    def get_hardware_info(self) -> Dict[str, str]:
        """获取硬件信息
        
        Returns:
            Dict[str, str]: 包含CPU、硬盘和主板序列号的字典
        """
        # 如果已经缓存了硬件信息，直接返回
        if self._hardware_info is not None:
            return self._hardware_info
            
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
                        logger.info(f"获取到CPU序列号: {processor.ProcessorId.strip()}")
                        hardware_info["cpu"] = processor.ProcessorId.strip()
                        break
            except Exception as e:
                logger.warning(f"获取CPU序列号失败: {e}")
            
            # 获取硬盘序列号
            try:
                for disk in c.Win32_DiskDrive():
                    if disk.SerialNumber:
                        logger.info(f"获取到硬盘序列号: {disk.SerialNumber.strip()}")
                        hardware_info["disk"] = disk.SerialNumber.strip()
                        break
            except Exception as e:
                logger.warning(f"获取硬盘序列号失败: {e}")
            
            # 获取主板序列号
            try:
                for board in c.Win32_BaseBoard():
                    if board.SerialNumber:
                        logger.info(f"获取到主板序列号: {board.SerialNumber.strip()}")
                        hardware_info["motherboard"] = board.SerialNumber.strip()
                        break
            except Exception as e:
                logger.warning(f"获取主板序列号失败: {e}")
                
        except Exception as e:
            logger.error(f"使用WMI获取硬件信息时出错: {e}")
            
        # 打印获取到的硬件信息用于调试
        logger.info(f"最终硬件信息: CPU={hardware_info['cpu']}, 硬盘={hardware_info['disk']}, 主板={hardware_info['motherboard']}")
        
        # 缓存硬件信息
        self._hardware_info = hardware_info
        return hardware_info
    
    def generate_hardware_key(self) -> str:
        """生成硬件标识符
        
        Returns:
            str: 硬件标识符
        """
        # 如果已经缓存了硬件标识符，直接返回
        if self._hardware_key is not None:
            return self._hardware_key
            
        hardware_info = self.get_hardware_info()
        hardware_string = f"{hardware_info['cpu']}|{hardware_info['disk']}|{hardware_info['motherboard']}"
        hardware_key = self.multi_layer_hash(hardware_string)
        
        # 缓存硬件标识符
        self._hardware_key = hardware_key
        return hardware_key
    
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
    
    def load_public_key(self):
        """加载公钥
        
        Returns:
            公钥对象
        """
        try:
            with open(self.public_key_file, "rb") as key_file:
                public_key = serialization.load_pem_public_key(
                    key_file.read(),
                    backend=default_backend()
                )
            return public_key
        except Exception as e:
            logger.error(f"加载公钥失败: {e}")
            return None
    
    def load_private_key(self):
        """加载私钥
        
        Returns:
            私钥对象
        """
        try:
            with open(self.private_key_file, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            return private_key
        except Exception as e:
            logger.error(f"加载私钥失败: {e}")
            return None
    
    def verify_license(self) -> bool:
        """验证许可证
        
        Returns:
            bool: 许可证是否有效
        """
        try:
            # 检查许可证文件是否存在
            if not os.path.exists(self.license_file):
                logger.error("许可证文件不存在")
                return False
            
            # 检查公钥文件是否存在
            if not os.path.exists(self.public_key_file):
                logger.error("公钥文件不存在")
                return False
            
            # 读取二进制许可证文件
            with open(self.license_file, "rb") as f:
                license_data = f.read()
            
            # 解析二进制许可证数据
            # 格式: [license_data_bytes][signature_bytes]
            # 需要从后往前解析，因为签名长度固定为512字节（RSA-4096）
            if len(license_data) < 512:
                logger.error("许可证格式无效：数据长度不足")
                return False
                
            signature = license_data[-512:]  # 签名固定为512字节
            license_content = license_data[:-512]  # 剩余部分为许可证内容
            
            # 解析许可证内容
            # 格式: [licensee_length(4字节)][licensee_bytes][expiration_timestamp(8字节)][hardware_key_length(4字节)][hardware_key_bytes]
            offset = 0
            
            # 解析授权对象
            if len(license_content) < offset + 4:
                return {
                    "licensee": "许可证格式无效",
                    "status": "无效",
                    "expiration": "未知",
                    "hardware_key": "未知"
                }
                
            licensee_length = struct.unpack('<I', license_content[offset:offset+4])[0]
            offset += 4
            
            if len(license_content) < offset + licensee_length:
                return {
                    "licensee": "许可证格式无效",
                    "status": "无效",
                    "expiration": "未知",
                    "hardware_key": "未知"
                }
                
            licensee = license_content[offset:offset+licensee_length].decode('utf-8')
            offset += licensee_length
            
            # 解析过期时间
            if len(license_content) < offset + 8:
                return {
                    "licensee": "许可证格式无效",
                    "status": "无效",
                    "expiration": "未知",
                    "hardware_key": "未知"
                }
                
            expiration_timestamp = struct.unpack('<Q', license_content[offset:offset+8])[0]
            expiration_date = datetime.fromtimestamp(expiration_timestamp)
            offset += 8
            
            # 解析硬件标识符
            if len(license_content) < offset + 4:
                logger.error("许可证格式无效：无法解析硬件标识符长度")
                return False
                
            hardware_key_length = struct.unpack('<I', license_content[offset:offset+4])[0]
            offset += 4
            
            if len(license_content) < offset + hardware_key_length:
                logger.error("许可证格式无效：无法解析硬件标识符")
                return False
                
            hardware_key = license_content[offset:offset+hardware_key_length].decode('utf-8')
            offset += hardware_key_length
            
            # 创建license_info字典用于后续验证
            license_info = {
                "licensee": licensee,
                "expiration": expiration_date.isoformat(),
                "hardware_key": hardware_key
            }
            
            # 检查许可证是否过期
            if datetime.now() > expiration_date:
                logger.error("许可证已过期")
                return False
            
            # 验证硬件信息（使用缓存的硬件标识符）
            current_hardware_key = self.generate_hardware_key()
            if hardware_key != current_hardware_key:
                logger.error("硬件信息不匹配")
                logger.error(f"许可证中的硬件标识: {hardware_key}")
                logger.error(f"当前硬件标识: {current_hardware_key}")
                return False
            
            # 验证签名
            public_key = self.load_public_key()
            if not public_key:
                logger.error("无法加载公钥进行签名验证")
                return False
            
            try:
                # 验证签名
                public_key.verify(
                    signature,
                    license_content,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA512()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA512()
                )
                logger.info("许可证验证成功")
                return True
            except Exception as e:
                logger.error(f"许可证签名验证失败: {e}")
                return False
                
        except Exception as e:
            logger.error(f"许可证验证过程中发生错误: {e}")
            return False
    
    def create_license_info_dialog(self) -> 'LicenseInfoDialog':
        """创建许可证信息对话框
        
        Returns:
            LicenseInfoDialog: 许可证信息对话框实例
        """
        return LicenseInfoDialog(self)


class LicenseInfoDialog(QDialog):
    """许可证信息对话框"""
    
    def __init__(self, license_manager: LicenseManager, parent=None) -> None:
        """初始化许可证信息对话框
        
        Args:
            license_manager: 许可证管理器实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.license_manager = license_manager
        self.init_ui()
        self.set_window_properties()
        
    def init_ui(self) -> None:
        """初始化用户界面"""
        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("许可证信息")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        main_layout.addWidget(title_label)
        
        # 许可证信息卡片
        info_card = QFrame()
        info_card.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        info_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        info_layout = QGridLayout(info_card)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(15, 15, 15, 15)
        
        # 获取许可证信息
        license_info = self.get_license_info()
        
        # 授权对象
        licensee_label = QLabel("授权对象:")
        licensee_label.setStyleSheet("font-weight: bold; color: #34495e;")
        info_layout.addWidget(licensee_label, 0, 0, Qt.AlignLeft)
        
        self.licensee_value = QLabel(license_info.get("licensee", "未知"))
        self.licensee_value.setStyleSheet("color: #2c3e50;")
        self.licensee_value.setWordWrap(True)
        info_layout.addWidget(self.licensee_value, 0, 1, Qt.AlignLeft)
        
        # 状态
        status_label = QLabel("许可状态:")
        status_label.setStyleSheet("font-weight: bold; color: #34495e;")
        info_layout.addWidget(status_label, 1, 0, Qt.AlignLeft)
        
        self.status_value = QLabel(license_info.get("status", "未知"))
        status_color = "#27ae60" if license_info.get("status") == "有效" else "#e74c3c"
        self.status_value.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        info_layout.addWidget(self.status_value, 1, 1, Qt.AlignLeft)
        
        # 授权截止时间
        expiration_label = QLabel("授权截止:")
        expiration_label.setStyleSheet("font-weight: bold; color: #34495e;")
        info_layout.addWidget(expiration_label, 2, 0, Qt.AlignLeft)
        
        self.expiration_value = QLabel(license_info.get("expiration", "未知"))
        self.expiration_value.setStyleSheet("color: #2c3e50;")
        info_layout.addWidget(self.expiration_value, 2, 1, Qt.AlignLeft)
        
        # 硬件标识
        hardware_label = QLabel("硬件标识:")
        hardware_label.setStyleSheet("font-weight: bold; color: #34495e;")
        info_layout.addWidget(hardware_label, 3, 0, Qt.AlignLeft)
        
        # 显示硬件标识的前64个字符并添加省略号
        hardware_key = license_info.get("hardware_key", "未知")
        display_hardware = hardware_key[:64] + "..." if len(hardware_key) > 64 else hardware_key
        self.hardware_value = QLabel(display_hardware)
        self.hardware_value.setStyleSheet("color: #2c3e50;")
        self.hardware_value.setWordWrap(True)
        info_layout.addWidget(self.hardware_value, 3, 1, Qt.AlignLeft)
        
        main_layout.addWidget(info_card)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("关闭")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
    def get_license_info(self) -> Dict[str, str]:
        """获取许可证信息"""
        try:
            if not os.path.exists(self.license_manager.license_file):
                return {
                    "licensee": "未找到许可证文件",
                    "status": "无效",
                    "expiration": "未知",
                    "hardware_key": "未知"
                }
            
            # 读取二进制许可证文件
            with open(self.license_manager.license_file, "rb") as f:
                license_data = f.read()
            
            # 解析二进制许可证数据
            if len(license_data) < 512:
                return {
                    "licensee": "许可证格式无效",
                    "status": "无效",
                    "expiration": "未知",
                    "hardware_key": "未知"
                }
                
            signature = license_data[-512:]
            license_content = license_data[:-512]
            
            # 解析许可证内容
            offset = 0
            
            # 解析授权对象
            if len(license_content) < offset + 4:
                return {
                    "licensee": "解析失败",
                    "status": "无效",
                    "expiration": "未知",
                    "hardware_key": "未知"
                }
                
            licensee_length = struct.unpack('<I', license_content[offset:offset+4])[0]
            offset += 4
            
            if len(license_content) < offset + licensee_length:
                return {
                    "licensee": "解析失败",
                    "status": "无效",
                    "expiration": "未知",
                    "hardware_key": "未知"
                }
                
            licensee = license_content[offset:offset+licensee_length].decode('utf-8')
            offset += licensee_length
            
            # 解析过期时间
            if len(license_content) < offset + 8:
                return {
                    "licensee": "许可证格式无效",
                    "status": "无效",
                    "expiration": "未知",
                    "hardware_key": "未知"
                }
                
            expiration_timestamp = struct.unpack('<Q', license_content[offset:offset+8])[0]
            expiration_date = datetime.fromtimestamp(expiration_timestamp)
            offset += 8
            
            # 解析硬件标识符
            if len(license_content) < offset + 4:
                return {
                    "licensee": "许可证格式无效",
                    "status": "无效",
                    "expiration": "未知",
                    "hardware_key": "未知"
                }
                
            hardware_key_length = struct.unpack('<I', license_content[offset:offset+4])[0]
            offset += 4
            
            if len(license_content) < offset + hardware_key_length:
                return {
                    "licensee": "许可证格式无效",
                    "status": "无效",
                    "expiration": "未知",
                    "hardware_key": "未知"
                }
                
            hardware_key = license_content[offset:offset+hardware_key_length].decode('utf-8')
            offset += hardware_key_length
            
            # 检查是否过期
            is_expired = datetime.now() > expiration_date
            status = "已过期" if is_expired else "有效"
            
            return {
                "licensee": licensee,
                "status": status,
                "expiration": expiration_date.strftime('%Y-%m-%d %H:%M:%S'),
                "hardware_key": hardware_key
            }
            
        except Exception as e:
            return {
                "licensee": "无法解析许可证信息",
                "status": "无效",
                "expiration": "未知",
                "hardware_key": "未知"
            }
    
    def set_window_properties(self) -> None:
        """设置窗口属性"""
        self.setWindowTitle("许可证信息")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(500, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #ecf0f1;
            }
        """)
        
    def load_license_info(self) -> None:
        """加载许可证信息（保持原有逻辑以兼容其他地方的调用）"""
        pass
