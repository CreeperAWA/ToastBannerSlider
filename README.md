# ToastBannerSlider

ToastBannerSlider 是一个 Windows 平台的通知监听和显示工具。它可以监听特定标题的 Windows Toast 通知，并以横幅形式在屏幕顶部显示，支持滚动动画和交互操作。

## 功能特性

- 监听 Windows Toast 通知
- 在屏幕顶部显示自定义横幅通知
- 文字滚动动画效果
- 支持多次点击关闭
- 系统托盘图标和菜单
- 开机自启功能
- 可配置的通知参数
- 手动发送测试通知

## 界面预览

![通知横幅示例](notification_icon.png)

## 安装依赖

```bash
pip install -r requirements.txt
```

依赖库：
- PyQt5: 用于构建图形用户界面
- loguru: 用于日志记录

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
- **开机自启**: 设置程序开机自动启动
- **退出**: 退出程序

双击系统托盘图标也可以显示最后一条通知。

### 配置说明

在配置设置中可以调整以下参数：

1. **通知标题**: 要监听的通知标题（默认为"911 呼唤群"）
2. **滚动速度**: 文字滚动速度，单位为像素/秒（默认为200）
3. **滚动次数**: 文字滚动循环次数（默认为3次）
4. **点击关闭次数**: 点击通知横幅关闭所需的次数（默认为3次）

### 通知横幅交互

- 点击通知横幅指定次数（默认3次）可关闭通知
- 通知横幅会在显示指定次数（默认3次）后自动消失

## 技术架构

### 核心组件

1. **监听模块** ([listener.py](./listener.py)):
   - 监听 Windows Toast 通知数据库
   - 解析通知内容
   - 筛选指定标题的通知

2. **显示模块** ([notice_slider.py](./notice_slider.py)):
   - 创建顶部通知横幅
   - 实现文字滚动动画
   - 处理用户交互

3. **配置模块** ([config.py](./config.py)):
   - 管理程序配置
   - 读写配置文件

4. **主程序** ([main.py](./main.py)):
   - 整合各模块功能
   - 管理系统托盘图标
   - 处理用户交互

### 工作原理

1. 程序启动后会在后台运行通知监听线程
2. 监听线程定期检查 Windows 通知数据库
3. 当发现匹配标题的通知时，通过回调函数传递给主程序
4. 主程序创建通知横幅窗口并显示通知内容
5. 通知横幅具有滚动动画和点击交互功能

## 编译为可执行文件

使用 Nuitka 编译：

```bash
pip install nuitka pillow
python -m nuitka --onefile --windows-icon-from-ico=notification_icon.ico --enable-plugin=pyqt5 main.py
```

## 许可证

本项目采用 [GNU General Public License 3.0](https://github.com/CreeperAWA/ToastBannerSlider/blob/main/LICENSE) 许可证。