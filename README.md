# ToastBannerSlider

ToastBannerSlider 是一个 Windows 平台的通知监听和显示工具。它可以监听特定标题的 Windows Toast 通知，并以横幅形式在屏幕顶部显示，支持滚动动画和交互操作。

<p align="center">
  <img src="./doc/Example_of_Notification_Banner.png" alt="通知横幅示例">
</p>

## 功能特性

- 监听 Windows Toast 通知
- 在屏幕顶部显示自定义横幅通知
- 文字滚动动画效果
- 支持多次点击关闭
- 系统托盘图标和菜单
- 开机自启功能
- 可配置的通知参数
- 手动发送通知
- 免打扰模式
- 重复通知过滤
- 日志等级设置
- 自定义图标支持
- 多种横幅样式（默认样式、警告样式）
- 多种渲染后端支持（CPU 渲染、OpenGL/GPU 渲染、QML 渲染）
- 关键字替换和正则表达式匹配功能
- 许可证管理机制
- 横幅堆叠显示（支持同时显示多个通知）
- 可配置的滚动模式（始终滚动、自动判断）
- 透明度和样式自定义

## 安装依赖

```bash
pip install -r requirements.txt
```

依赖库：
- PySide6: 用于构建图形用户界面
- loguru: 用于日志记录
- cryptography: 用于许可证系统加密功能
- WMI: 用于 Windows 管理接口访问
- regex: 用于高级正则表达式匹配
- Nuitka: 用于将Python代码编译为可执行文件

## 使用方法

### 运行程序

```bash
python main.py
```

程序启动后会在系统托盘中显示图标，不会弹出主窗口。

### 系统托盘菜单

右键点击系统托盘图标可打开菜单：

- **显示最后通知**: 显示最近一次接收到的通知
- **发送通知**: 手动发送测试通知
- **配置设置**: 配置监听参数
- **免打扰**: 不显示所有 Toasts 通知
- **开机自启**: 设置程序开机自动启动
- **退出**: 退出程序

双击系统托盘图标也可以显示最后一条通知。

### 配置说明

在配置设置中可以调整以下参数：

1. **通知标题**: 要监听的通知标题（默认为"911 呼唤群"）
2. **程序图标**: 自定义程序图标
3. **滚动速度**: 文字滚动速度，单位为像素/秒（默认为 200px/s）
4. **滚动次数**: 文字滚动循环次数（默认为 3 次）
5. **点击关闭次数**: 点击通知横幅关闭所需的次数（默认为 3 次）
6. **右侧间隔距离**: 横幅右侧与屏幕边缘的距离（默认为 150px）
7. **字体大小**: 通知文字的字体大小（默认为 48px）
8. **左侧边距**: 横幅左侧边距（默认为 93px）
9. **右侧边距**: 横幅右侧边距（默认为 93px）
10. **图标缩放倍数**: 通知图标缩放比例（默认为 1.0）
11. **标签文本x轴偏移**: 文字在横幅中的水平偏移量（默认为 0px）
12. **窗口高度**: 通知横幅窗口高度（默认为 128px）
13. **标签遮罩宽度**: 文字滚动区域的宽度（默认为 305px）
14. **横幅间隔**: 多个通知横幅之间的垂直间距（默认为 10px）
15. **基础垂直偏移量**: 通知横幅相对于屏幕顶部的垂直偏移量（默认为 50px）
16. **横幅透明度**: 通知横幅的透明度（默认为 0.9）
17. **上移动画持续时间**: 新通知出现时的上移动画时间（默认为 100ms）
18. **淡入淡出动画时间**: 通知显示和消失时的淡入淡出动画时间（默认为 1500ms）
19. **忽略重复通知**: 是否忽略5分钟内的重复通知（默认为否）
20. **滚动模式**: 选择"不论如何都滚动"或"可以展示完全的不滚动"（默认为总是滚动）
21. **日志等级**: 设置日志输出等级（默认为 INFO）
22. **横幅样式**: 选择默认样式或警告样式（默认为默认样式）
23. **免打扰模式**: 是否开启免打扰模式（默认为否）
24. **启用 Qt Quick**: 是否启用 Qt Quick (QML 渲染)（默认为否）
25. **渲染后端**: 选择渲染后端：默认(CPU 渲染)、OpenGL(GPU 渲染)等（默认为 CPU 渲染）

### 通知横幅交互

- 点击通知横幅指定次数（默认 3 次）可关闭通知
- 通知横幅会在显示指定次数（默认 3 次）后自动消失

## 许可证系统

ToastBannerSlider 使用基于硬件绑定的许可证系统来验证软件的合法使用。

### 许可证验证机制

- 许可证必须基于真实硬件信息（CPU SN、硬盘 SN、主板 SN）进行绑定
- 验证包括硬件绑定校验、时间有效期校验、多重哈希处理和 RSA 数字签名验证
- 程序启动时自动执行完整验证流程，验证失败将立即终止运行

### 自定义公钥支持

程序支持使用自定义公钥文件进行许可证验证：

1. 在可执行文件目录下放置名为 `CustomPublicKey.pem` 的公钥文件
2. 程序将优先使用该文件进行许可证验证
3. 如果不存在该文件，则使用内置的公钥文件

这种方式允许在不重新编译程序的情况下更换验证公钥，提高了部署的灵活性。

### 许可证文件格式

许可证文件 (`License.key`) 采用二进制格式存储，包含以下信息：
- 授权对象信息
- 过期时间戳
- 硬件标识符
- RSA-4096 数字签名

## 技术架构

### 核心组件

1. **主程序** ([main.py](./main.py)):
   - 整合各模块功能
   - 管理系统托盘图标
   - 控制整个应用程序生命周期

2. **通知横幅** ([notice_slider.py](./notice_slider.py)):
   - 创建和显示顶部通知横幅
   - 实现文字滚动动画
   - 处理用户交互

3. **配置管理** ([config.py](./config.py)):
   - 加载和保存配置信息
   - 管理日志设置

4. **系统托盘管理** ([tray_manager.py](./tray_manager.py)):
   - 创建和管理系统托盘图标
   - 处理托盘菜单事件

5. **通知监听** ([notification_listener.py](./notification_listener.py)):
   - 监听 Windows Toast 通知数据库
   - 过滤匹配标题的通知

6. **配置对话框** ([config_dialog.py](./config_dialog.py)):
   - 提供图形化配置界面
   - 允许用户修改各种参数

7. **发送通知对话框** ([send_notification_dialog.py](./send_notification_dialog.py)):
   - 提供手动发送测试通知的界面

8. **图标管理** ([icon_manager.py](./icon_manager.py)):
   - 管理程序图标资源
   - 支持自定义图标加载

9. **许可证管理** ([license_manager.py](./license_manager.py)):
   - 管理软件许可证验证
   - 基于硬件信息进行许可证绑定
   - 支持自定义公钥文件验证

10. **横幅工厂** ([banner_factory.py](./banner_factory.py)):
    - 根据配置创建不同样式的横幅
    - 支持多种渲染方式（CPU/GPU/QML）

11. **关键字替换处理器** ([keyword_replacer.py](./keyword_replacer.py)):
    - 处理通知消息中的关键字替换
    - 支持正则表达式匹配和字体样式修改

12. **日志配置** ([logger_config.py](./logger_config.py)):
    - 统一管理应用程序的日志配置
    - 提供不同级别的日志输出

13. **QML通知横幅** ([notice_slider_qml.py](./notice_slider_qml.py)):
    - 默认样式横幅的 QML 实现版本
    - 提供更流畅的动画效果

14. **QML警告横幅** ([warning_banner_qml.py](./warning_banner_qml.py)):
    - 警告样式横幅的 QML 实现版本
    - 用于显示重要警告信息

15. **CPU渲染警告横幅** ([warning_banner_cpu.py](./warning_banner_cpu.py)):
    - 警告样式横幅的 CPU 渲染版本

16. **GPU渲染警告横幅** ([warning_banner_gpu.py](./warning_banner_gpu.py)):
    - 警告样式横幅的 GPU 渲染版本

17. **配置对话框逻辑** ([config_dialog_logic.py](./config_dialog_logic.py)):
    - 处理配置对话框的核心业务逻辑

18. **关键字规则对话框** ([keyword_rule_dialog.py](./keyword_rule_dialog.py)):
    - 提供关键字规则编辑界面

19. **图标提供者** ([icon_provider.py](./icon_provider.py)):
    - 为QML界面提供图标资源加载功能

### 工作流程

1. 程序启动时创建系统托盘图标和通知监听线程
2. 通知监听线程定期轮询 Windows Toast 通知数据库
3. 当发现匹配标题的通知时，触发回调函数
4. 主程序创建通知横幅实例并显示
5. 用户可以通过点击横幅或使用托盘菜单与程序交互

## 打包发布

使用 Nuitka 将程序打包为独立的可执行文件：

```bash
python -m nuitka --onefile --windows-console-mode="disable" --enable-plugins="pyside6" --include-qt-plugins="qml" --windows-icon-from-ico="notification_icon.ico" --product-name="ToastBannerSlider" --product-version="1.0.0" --file-description="ToastBannerSlider" --copyright="© 2025 CreeperAWA." --include-data-file=notification_icon.png=notification_icon.png --include-data-file=notification_icon.ico=notification_icon.ico --include-data-file=public.pem=public.pem --include-data-file=NoticeSlider.qml=NoticeSlider.qml --include-data-file=WarningBanner.qml=WarningBanner.qml main.py
```

## 开源许可

本项目采用 GNU General Public License v3.0 许可证。