"""生成RSA密钥对用于许可证签名和验证"""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def generate_key_pair():
    """生成RSA密钥对"""
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
    
    print("密钥对生成成功！")
    print("私钥已保存到 private.pem")
    print("公钥已保存到 public.pem")


if __name__ == "__main__":
    generate_key_pair()