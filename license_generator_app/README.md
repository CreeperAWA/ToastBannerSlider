# 许可证生成器

这是一个独立的许可证生成工具，用于为 ToastBannerSlider 应用生成数字签名的许可证文件。

## 功能特点

- 生成 RSA-4096 密钥对
- 创建带数字签名的许可证文件
- 图形化用户界面，易于操作
- 硬件绑定验证（基于 CPU、硬盘、主板序列号）
- 多层哈希算法确保安全性

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行程序：
```bash
python license_generator_main.py
```

2. 点击"生成密钥对"按钮生成新的 RSA 密钥对（如果还没有的话）
3. 填写授权对象名称
4. 设置授权天数或选择过期日期
5. 输入硬件标识或点击"生成"按钮生成示例硬件标识
6. 点击"生成许可证"按钮创建许可证文件

## 注意事项

- 私钥文件 (private.pem) 必须妥善保管，不要泄露
- 公钥文件 (public.pem) 用于验证许可证，可以分发给客户端
- 生成的 License.key 文件是最终的许可证文件

## 打包发布

使用 Nuitka 将程序打包为独立的可执行文件：

```bash
cd license_generator_app
python -m nuitka --onefile --windows-console-mode="disable" --enable-plugins="pyside6" --windows-icon-from-ico="icon.ico" --product-name="ToastBannerSliderLicenseGenerator" --product-version="1.0.0" --file-description="ToastBannerSliderLicenseGenerator" --copyright="© 2025 CreeperAWA." --include-data-file=public.pem=public.pem --include-data-file=private.pem=private.pem license_generator_ui.py
```