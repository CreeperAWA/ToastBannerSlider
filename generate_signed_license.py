"""生成带数字签名的许可证"""

import sys
import os
from license_manager import LicenseManager


def generate_signed_license(licensee: str, expiration_days: int = 365) -> None:
    """生成带数字签名的许可证文件
    
    Args:
        licensee: 授权对象
        expiration_days: 授权天数
    """
    try:
        # 创建许可证管理器实例
        license_manager = LicenseManager()
        
        # 检查私钥文件是否存在
        if not os.path.exists(license_manager.private_key_file):
            print("错误：未找到私钥文件 private.pem，请先运行 generate_keys.py 生成密钥对")
            return
        
        # 获取硬件信息
        hardware_key = license_manager.generate_hardware_key()
        
        # 计算过期时间
        from datetime import datetime, timedelta
        expiration_date = datetime.now().replace(microsecond=0) + timedelta(days=expiration_days)
        
        # 创建许可证数据
        license_info = {
            "licensee": licensee,
            "expiration": expiration_date.isoformat(),
            "hardware_key": hardware_key
        }
        
        # 转换为JSON
        license_data = json.dumps(license_info, ensure_ascii=False).encode('utf-8')
        print(f"许可证数据: {license_data.decode('utf-8')}")
        
        # 加载私钥
        private_key = license_manager.load_private_key()
        if not private_key:
            print("错误：无法加载私钥")
            return
        
        # 对许可证数据进行签名
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        
        signature = private_key.sign(
            license_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA512()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA512()
        )
        
        # 创建包含签名的许可证数据
        signed_license = {
            "data": license_data.decode('utf-8'),
            "signature": signature.hex()
        }
        
        # 转换为JSON并编码
        final_data = json.dumps(signed_license, ensure_ascii=False).encode('utf-8')
        
        # 保存为十六进制文件
        with open("License.key", "wb") as f:
            f.write(final_data.hex().encode('utf-8'))
        
        print(f"带数字签名的许可证已生成并保存到 License.key")
        print(f"授权对象: {licensee}")
        print(f"过期时间: {expiration_date.isoformat()}")
        print(f"硬件标识: {hardware_key}")
        print(f"签名长度: {len(signature)} 字节")
        
        # 显示获取到的硬件信息
        hardware_info = license_manager.get_hardware_info()
        print(f"获取到的硬件信息:")
        print(f"  CPU序列号: {hardware_info['cpu']}")
        print(f"  硬盘序列号: {hardware_info['disk']}")
        print(f"  主板序列号: {hardware_info['motherboard']}")
        
    except Exception as e:
        print(f"生成带签名的许可证时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import json
    if len(sys.argv) > 1:
        licensee_name = sys.argv[1]
        days = 365
        if len(sys.argv) > 2:
            days = int(sys.argv[2])
        generate_signed_license(licensee_name, days)
    else:
        print("用法: python generate_signed_license.py <授权对象> [授权天数]")
        print("示例: python generate_signed_license.py \"张三\" 365")