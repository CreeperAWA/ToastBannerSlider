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
- 手动发送测试通知
- 免打扰模式
- 重复通知过滤
- 日志等级设置
- 自定义图标支持

## 安装依赖

```bash
pip install -r requirements.txt
```

依赖库：
- PySide6: 用于构建图形用户界面
- loguru: 用于日志记录

## 使用方法

### 运行程序

```bash
python main.py
```

程序启动后会在系统托盘中显示图标，不会弹出主窗口。

你也可以使用以下参数启动：

```bash
python main.py
```

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
15. **上移动画持续时间**: 新通知出现时的上移动画时间（默认为 100ms）
16. **淡入淡出动画时间**: 通知显示和消失时的淡入淡出动画时间（默认为 1500ms）
17. **基础垂直偏移**: 通知横幅相对于屏幕顶部的垂直偏移量（默认为 50px）
18. **忽略重复通知**: 是否忽略5分钟内的重复通知（默认为否）
19. **滚动模式**: 选择"不论如何都滚动"或"可以展示完全的不滚动"（默认为总是滚动）
20. **日志等级**: 设置日志输出等级（默认为 INFO）

### 通知横幅交互

- 点击通知横幅指定次数（默认 3 次）可关闭通知
- 通知横幅会在显示指定次数（默认 3 次）后自动消失

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

### 工作流程

1. 程序启动时创建系统托盘图标和通知监听线程
2. 通知监听线程定期轮询 Windows Toast 通知数据库
3. 当发现匹配标题的通知时，触发回调函数
4. 主程序创建通知横幅实例并显示
5. 用户可以通过点击横幅或使用托盘菜单与程序交互

## 打包发布

使用 Nuitka 将程序打包为独立的可执行文件：

```bash
python -m nuitka --onefile --windows-console-mode="disable" --enable-plugins="pyside6" --main="main.py" --windows-icon-from-ico="notification_icon.ico" --product-name="ToastBannerSlider" --product-version="1.0.0" --file-description="ToastBannerSlider" --copyright="© 2025 CreeperAWA." --include-data-file=notification_icon.png=notification_icon.png --include-data-file=notification_icon.ico=notification_icon.ico --include-data-file=public.pem=public.pem main.py
```

## 开源许可

本项目采用 GNU General Public License v3.0 许可证。