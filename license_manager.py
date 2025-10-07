"""许可证管理模块

该模块负责处理软件许可证验证，包括硬件信息获取、多重哈希验证和许可证管理。
"""

import hashlib
import os
import sys
import struct
from datetime import datetime
from typing import Dict, Optional, Any, List
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from logger_config import logger
from config import load_config
from icon_manager import load_icon

# wmi库缺少类型提示，忽略类型检查
import wmi  # type: ignore

def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径，采用与配置文件相同的策略"""
    base_dir: str
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Nuitka单文件模式，资源在临时目录中
        base_dir = str(sys._MEIPASS)  # type: ignore
    elif getattr(sys, 'frozen', False):
        # 其他打包模式
        base_dir = str(os.path.dirname(sys.executable))
    else:
        # 开发环境，使用__file__获取当前文件目录
        base_dir = str(os.path.dirname(os.path.abspath(__file__)))
        
    # 确保relative_path是字符串类型
    relative_path_str: str = str(relative_path)
    return os.path.join(base_dir, relative_path_str)


def get_executable_dir() -> str:
    """获取可执行文件所在目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的程序
        return os.path.dirname(sys.executable)
    else:
        # 开发环境，使用sys.argv[0]而不是__file__
        return os.path.dirname(os.path.abspath(sys.argv[0]))


class LicenseManager:
    """许可证管理器"""
    
    def __init__(self) -> None:
        """初始化许可证管理器"""
        self.license_file = "License.key"
        self.public_key_file = get_resource_path("public.pem")
        self.custom_public_key_file = os.path.join(get_executable_dir(), "CustomPublicKey.pem")
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
            c: Any = wmi.WMI()  # type: ignore
            
            # 获取CPU序列号
            try:
                processors: List[Any] = c.Win32_Processor()  # type: ignore
                for processor in processors: # type: ignore
                    # 通过类型注释明确指定processor类型以避免Pylance警告
                    proc: Any = processor  # type: ignore
                    # 使用类型注释明确指定getattr返回值类型
                    processor_id: Optional[str] = getattr(proc, 'ProcessorId', None)  # type: ignore
                    if processor_id:
                        processor_id_str: str = processor_id.strip()  # type: ignore
                        logger.info(f"获取到CPU序列号: {processor_id_str}")
                        hardware_info["cpu"] = processor_id_str
                        break
            except Exception as e:
                logger.warning(f"获取CPU序列号失败: {e}")
            
            # 获取硬盘序列号
            try:
                disks: List[Any] = c.Win32_DiskDrive()  # type: ignore
                for disk in disks: # type: ignore
                    # 通过类型注释明确指定disk类型以避免Pylance警告
                    d: Any = disk  # type: ignore
                    # 使用类型注释明确指定getattr返回值类型
                    serial_number: Optional[str] = getattr(d, 'SerialNumber', None)  # type: ignore
                    if serial_number:
                        serial_number_str: str = serial_number.strip()  # type: ignore
                        logger.info(f"获取到硬盘序列号: {serial_number_str}")
                        hardware_info["disk"] = serial_number_str
                        break
            except Exception as e:
                logger.warning(f"获取硬盘序列号失败: {e}")
            
            # 获取主板序列号
            try:
                boards: List[Any] = c.Win32_BaseBoard()  # type: ignore
                for board in boards: # type: ignore
                    # 通过类型注释明确指定board类型以避免Pylance警告
                    b: Any = board  # type: ignore
                    # 使用类型注释明确指定getattr返回值类型
                    serial_number: Optional[str] = getattr(b, 'SerialNumber', None)  # type: ignore
                    if serial_number:
                        serial_number_str: str = serial_number.strip()  # type: ignore
                        logger.info(f"获取到主板序列号: {serial_number_str}")
                        hardware_info["motherboard"] = serial_number_str
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
    
    def load_public_key(self) -> Any:
        """加载公钥
        
        Returns:
            公钥对象
        """
        try:
            # 检查自定义公钥文件是否存在，如果存在则优先使用
            public_key_path = self.public_key_file
            if os.path.exists(self.custom_public_key_file):
                logger.info("检测到自定义公钥文件，将优先使用")
                public_key_path = self.custom_public_key_file
            
            with open(public_key_path, "rb") as key_file:
                public_key = serialization.load_pem_public_key(
                    key_file.read(),
                    backend=default_backend()
                )
            return public_key
        except Exception as e:
            logger.error(f"加载公钥失败: {e}")
            return None
    
    def load_private_key(self) -> Any:
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
            
            # 检查公钥文件是否存在（自定义公钥优先）
            public_key_path = self.public_key_file # type: ignore
            if os.path.exists(self.custom_public_key_file):
                logger.info("使用自定义公钥文件进行验证")
                public_key_path = self.custom_public_key_file # type: ignore
            elif not os.path.exists(self.public_key_file):
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
                logger.error("许可证格式无效：无法解析授权对象长度")
                return False
                
            licensee_length = struct.unpack('<I', license_content[offset:offset+4])[0]
            offset += 4
            
            if len(license_content) < offset + licensee_length:
                logger.error("许可证格式无效：无法解析授权对象内容")
                return False
                
            # 直接使用licensee变量，移除无用的占位符
            licensee = license_content[offset:offset+licensee_length].decode('utf-8') # type: ignore
            offset += licensee_length
            
            # 解析过期时间
            if len(license_content) < offset + 8:
                logger.error("许可证格式无效：无法解析过期时间")
                return False
                
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


class LicenseInfoWorker(QThread):
    """许可证信息获取工作线程"""
    info_ready = Signal(dict)
    
    def __init__(self, license_manager: 'LicenseManager') -> None:
        super().__init__()
        self.license_manager = license_manager
    
    def run(self) -> None:
        try:
            license_info = self.get_license_info()
            self.info_ready.emit(license_info)
        except Exception as e:
            logger.error(f"获取许可证信息时出错: {e}")
            self.info_ready.emit({
                "licensee": "获取失败",
                "status": "无效",
                "expiration": "未知",
                "hardware_key": "未知"
            })
    
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
                
            # 直接提取签名和内容，移除无用的变量使用
            signature = license_data[-512:] # type: ignore
            license_content = license_data[:-512]
            
            # 解析许可证内容
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
            logger.error(f"解析许可证信息时出错: {e}")
            return {
                "licensee": "无法解析许可证信息",
                "status": "无效",
                "expiration": "未知",
                "hardware_key": "未知"
            }


class LicenseInfoDialog(QDialog):
    """许可证信息对话框"""
    
    def __init__(self, license_manager: LicenseManager, parent: Optional[Any] = None) -> None:
        """初始化许可证信息对话框
        
        Args:
            license_manager: 许可证管理器实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.license_manager = license_manager
        self.worker: Optional[LicenseInfoWorker] = None
        self.config = load_config()
        self.init_ui()
        self.set_window_properties()
        self._set_window_icon()
        self.load_license_info()
        
    def _set_window_icon(self) -> None:
        """设置许可证信息对话框窗口图标"""
        try:
            logger.debug("设置许可证信息对话框窗口图标")
            
            # 先确保配置已加载
            if not hasattr(self, 'config'):
                self.config = load_config()
                
            # 加载图标
            icon = load_icon(self.config)
            if not icon.isNull():
                self.setWindowIcon(icon)
                logger.debug("许可证信息对话框窗口图标设置成功")
            else:
                logger.warning("许可证信息对话框窗口图标为空")
        except Exception as e:
            logger.error(f"设置许可证信息对话框窗口图标时出错: {e}")
        
    def init_ui(self) -> None:
        """初始化用户界面"""
        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 整体居中
        
        # 标题
        title_label = QLabel("许可证信息")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        main_layout.addWidget(title_label)
        
        # 创建中心内容容器
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 使内容居中
        
        # 许可证信息卡片
        info_card = QFrame()
        info_card.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        info_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        info_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 信息布局
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 使信息内容居中
        
        # 设置统一的样式表用于信息标签
        info_label_style = """
            QLabel {
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 6px 8px;
                min-height: 25px;
                max-height: 80px;
            }
        """
        
        # 创建内部布局
        inner_layout = QVBoxLayout()
        inner_layout.setSpacing(8)
        inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 使内部内容居中
        
        # 授权对象
        licensee_layout = QHBoxLayout()
        licensee_layout.setSpacing(10)
        
        licensee_label = QLabel("授权对象:")
        licensee_label.setStyleSheet("font-weight: bold; color: #34495e; width: 120px; max-width: 120px; max-height: 80px;")
        licensee_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)
        licensee_layout.addWidget(licensee_label)
        
        self.licensee_value = QLabel("加载中...")
        self.licensee_value.setStyleSheet(info_label_style)
        self.licensee_value.setWordWrap(True)
        self.licensee_value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        licensee_layout.addWidget(self.licensee_value)
        
        inner_layout.addLayout(licensee_layout)
        
        # 状态
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        status_label = QLabel("许可状态:")
        status_label.setStyleSheet("font-weight: bold; color: #34495e; width: 120px; max-width: 120px; max-height: 80px;")
        status_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)
        status_layout.addWidget(status_label)
        
        self.status_value = QLabel("加载中...")
        self.status_value.setStyleSheet(f"""
            QLabel {{
                color: #7f8c8d;
                font-weight: bold;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 6px 8px;
                min-height: 25px;
                max-height: 80px;
            }}
        """)
        self.status_value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        status_layout.addWidget(self.status_value)
        
        inner_layout.addLayout(status_layout)
        
        # 授权截止时间
        expiration_layout = QHBoxLayout()
        expiration_layout.setSpacing(10)
        
        expiration_label = QLabel("授权截止:")
        expiration_label.setStyleSheet("font-weight: bold; color: #34495e; width: 120px; max-width: 120px; max-height: 80px;")
        expiration_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)
        expiration_layout.addWidget(expiration_label)
        
        self.expiration_value = QLabel("加载中...")
        self.expiration_value.setStyleSheet(info_label_style)
        self.expiration_value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        expiration_layout.addWidget(self.expiration_value)
        
        inner_layout.addLayout(expiration_layout)
        
        # 硬件标识
        hardware_layout = QHBoxLayout()
        hardware_layout.setSpacing(10)
        
        hardware_label = QLabel("硬件标识:")
        hardware_label.setStyleSheet("font-weight: bold; color: #34495e; width: 120px; max-width: 120px; max-height: 80px;")
        hardware_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)
        hardware_layout.addWidget(hardware_label)
        
        self.hardware_value = QLabel("加载中...")
        self.hardware_value.setStyleSheet(info_label_style)
        self.hardware_value.setWordWrap(True)
        self.hardware_value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        hardware_layout.addWidget(self.hardware_value)
        
        inner_layout.addLayout(hardware_layout)
        
        # 将内部布局添加到信息布局中
        info_layout.addLayout(inner_layout)
        
        # 添加弹性空间
        info_layout.addStretch(1)
        
        content_layout.addWidget(info_card)
        main_layout.addWidget(content_container)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        refresh_button = QPushButton("刷新")
        refresh_button.setStyleSheet("""
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
        refresh_button.clicked.connect(self.load_license_info)
        button_layout.addWidget(refresh_button)
        
        close_button = QPushButton("关闭")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
    def load_license_info(self) -> None:
        """加载许可证信息（异步加载）"""
        # 如果有正在运行的worker，先停止它
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        
        # 创建新的worker并启动
        self.worker = LicenseInfoWorker(self.license_manager)
        self.worker.info_ready.connect(self.update_license_info)
        self.worker.start()
        
        # 显示加载状态
        self.licensee_value.setText("加载中...")
        self.status_value.setText("加载中...")
        self.expiration_value.setText("加载中...")
        self.hardware_value.setText("加载中...")
        
    def update_license_info(self, license_info: Dict[str, str]) -> None:
        """更新许可证信息显示"""
        self.licensee_value.setText(license_info.get("licensee", "未知"))
        
        status = license_info.get("status", "未知")
        status_color = "#27ae60" if status == "有效" else "#e74c3c" if status == "已过期" else "#f39c12"
        self.status_value.setText(status)
        self.status_value.setStyleSheet(f"""
            QLabel {{
                color: {status_color};
                font-weight: bold;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 6px 8px;
                min-height: 25px;
                max-height: 80px;
            }}
        """)
        
        self.expiration_value.setText(license_info.get("expiration", "未知"))
        self.hardware_value.setText(license_info.get("hardware_key", "未知"))
        
    def set_window_properties(self) -> None:
        """设置窗口属性"""
        self.setWindowTitle("许可证信息")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.resize(980, 450)
        self.setFixedSize(980, 450)  # 固定大小
        self.setStyleSheet("""
            QDialog {
                background-color: #ecf0f1;
            }
        """)