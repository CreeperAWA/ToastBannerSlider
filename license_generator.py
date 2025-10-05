"""许可证生成模块

该模块负责生成带数字签名的软件许可证。
"""

import os
import sys
import json
import struct
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import wmi
import hashlib
from typing import Dict


class LicenseGenerator:
    """许可证生成器"""
    
    def __init__(self, private_key_file: str = "private.pem") -> None:
        """初始化许可证生成器
        
        Args:
            private_key_file: 私钥文件路径
        """
        self.private_key_file = private_key_file
        self.license_file = "License.key"
        
    def get_hardware_info(self) -> Dict[str, str]:
        """获取硬件信息
        
        Returns:
            Dict[str, str]: 包含CPU、硬盘和主板序列号的字典
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
    
    def generate_hardware_key(self) -> str:
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
        
        # 第二层：再次SHA512
        double_sha512 = hashlib.sha512(sha512_hash.encode('utf-8')).hexdigest()
        
        # 第三层：MD5
        md5_hash = hashlib.md5(double_sha512.encode('utf-8')).hexdigest()
        
        # 第四层：SHA256
        final_hash = hashlib.sha256(md5_hash.encode('utf-8')).hexdigest()
        
        return final_hash
    
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
            print(f"加载私钥失败: {e}")
            return None
    
    def generate_license(self, licensee: str, expiration_days: int = 365) -> bool:
        """生成带数字签名的许可证文件
        
        Args:
            licensee: 授权对象
            expiration_days: 授权天数
            
        Returns:
            bool: 是否成功生成许可证
        """
        try:
            # 检查私钥文件是否存在
            if not os.path.exists(self.private_key_file):
                print(f"错误：未找到私钥文件 {self.private_key_file}")
                print("请确保已生成RSA密钥对")
                return False
            
            # 获取硬件信息
            hardware_key = self.generate_hardware_key()
            
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
            
            print(f"许可证数据大小: {len(license_data)} 字节")
            print(f"授权对象: {licensee}")
            print(f"过期时间: {expiration_date.isoformat()}")
            print(f"硬件标识: {hardware_key}")
            
            # 加载私钥
            private_key = self.load_private_key()
            if not private_key:
                print("错误：无法加载私钥")
                return False
            
            # 对许可证数据进行签名
            signature = private_key.sign(
                license_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA512()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA512()
            )
            
            # 构造二进制许可证文件: [license_data_bytes][signature_bytes]
            final_data = license_data + signature
            
            # 直接保存为二进制文件
            with open(self.license_file, "wb") as f:
                f.write(final_data)
            
            print(f"带数字签名的许可证已生成并保存到 {self.license_file}")
            print(f"签名长度: {len(signature)} 字节")
            
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


def main():
    """主函数"""
    if len(sys.argv) > 1:
        licensee_name = sys.argv[1]
        days = 365
        if len(sys.argv) > 2:
            days = int(sys.argv[2])
        
        generator = LicenseGenerator()
        success = generator.generate_license(licensee_name, days)
        if success:
            print("许可证生成成功！")
        else:
            print("许可证生成失败！")
            sys.exit(1)
    else:
        print("用法: python license_generator.py <授权对象> [授权天数]")
        print("示例: python license_generator.py \"张三\" 365")
        sys.exit(1)


if __name__ == "__main__":
    main()