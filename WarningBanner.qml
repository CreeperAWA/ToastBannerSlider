import QtQuick 2.15
import QtQuick.Window 2.15

Item {
    id: root
    width: 1920
    height: 140
    opacity: 1.0
    
    property string bannerText: ""
    // stripeOffset 每帧变更会导致 Canvas 重绘；改为移动更大的 Canvas 节省重绘开销
    property int stripeAnimX: 0
    property int maxScrolls: 0
    property real scrollSpeed: 0.0
    property int rightSpacing: 0
    property int bannerSpacing: 10  // 横幅间距
    property int scrollCount: 0
    // 复用的文本滚动动画（见下方 textScrollAnim）
    property real textOffset: 0
    property real bannerOpacity: 0.9  // 横幅透明度
    property string scrollMode: "always"  // 滚动模式
    
    // 组件加载完成后输出调试信息
    Component.onCompleted: {
        // 延迟一小段时间以确保属性已更新
        startupTimer.start();
    }
    
    Timer {
        id: startupTimer
        interval: 10
        repeat: false
        onTriggered: {
            // 通过Python端记录日志
            bannerObject.logDebug("QML配置参数:");
            bannerObject.logDebug("  maxScrolls: " + maxScrolls);
            bannerObject.logDebug("  scrollSpeed: " + scrollSpeed);
            bannerObject.logDebug("  rightSpacing: " + rightSpacing);
            bannerObject.logDebug("  bannerSpacing: " + bannerSpacing);
            bannerObject.logDebug("  bannerText: " + bannerText);
            bannerObject.logDebug("  bannerOpacity: " + bannerOpacity);
            bannerObject.logDebug("  scrollMode: " + scrollMode);
            // 延迟启动文本动画
            startTextAnimationTimer.start();
        }
    }
    
    // 背景红色矩形（恢复被意外移除的背景）
    Rectangle {
        id: background
        anchors.fill: parent
        color: "#b3080a"
        opacity: bannerOpacity
        layer.enabled: true
        layer.smooth: true
    }

    // 延迟启动文本动画的定时器（在 startupTimer 触发后启动）
    Timer {
        id: startTextAnimationTimer
        interval: 100
        repeat: false
        onTriggered: {
            var src = root.bannerText ? root.bannerText : "";
            if (src.indexOf("<span style=") !== -1 && src.indexOf("</span>") !== -1) {
                messageText1.text = messageText2.text = src;
            } else if (src.indexOf("<") !== -1 || src.indexOf(">") !== -1) {
                messageText1.text = messageText2.text = src;
            } else {
                var escapedText = src.replace(/&/g, "&amp;")
                                     .replace(/</g, "&lt;")
                                     .replace(/>/g, "&gt;")
                                     .replace(/\"/g, "&quot;")
                                     .replace(/'/g, "&#039;");
                messageText1.text = messageText2.text = escapedText;
            }
            Qt.callLater(startScrollingText);
        }
    }
    
    // 条纹图案
    Repeater {
        id: stripeCanvasRepeater
        model: 2  // 顶部和底部条纹

        // 改为绘制比容器更宽的 Canvas，然后通过移动 Canvas 的 x 来创建循环条纹效果，避免每帧重绘
        Canvas {
            id: stripeCanvas
            // 宽度比视口略大以便循环时拼接无缝
            width: parent.width + 64
            height: 32
            x: stripeAnimX
            y: (index === 0) ? 0 : parent.height - 32
            antialiasing: true
            layer.enabled: true
            layer.smooth: true
            renderTarget: Canvas.FramebufferObject
            renderStrategy: Canvas.Cooperative

            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);

                // 绘制黄色条纹（静态纹理）
                ctx.fillStyle = "#ccffde59";
                for (var x = -40; x < width + 40; x += 32) {
                    ctx.beginPath();
                    ctx.moveTo(x, height);
                    ctx.lineTo(x + 16, 0);
                    ctx.lineTo(x + 32, 0);
                    ctx.lineTo(x + 16, height);
                    ctx.closePath();
                    ctx.fill();
                }
            }
        }
    }
    
    // 分割线
    Repeater {
        model: 2  // 顶部和底部线条
        
        Rectangle {
            id: separatorLine
            height: 4
            color: "#ccffde59"  // 带透明度的黄色
            width: parent.width
            y: (index === 0) ? 32 : parent.height - 32 - 4
            // 启用抗锯齿和层渲染以提高性能
            antialiasing: true
            layer.enabled: true
            layer.smooth: true
        }
    }
    
    // 文本容器
    Item {
        id: textContainer
        x: 0  // 移除左边距
        y: 0
        width: parent.width
        height: parent.height
        clip: true  // 启用裁剪，确保文字在区域内显示
        
        // 使用两个并排的 Text，以实现平滑无跳动的循环滚动
        Text {
            id: messageText1
            x: textOffset
            y: (parent.height - paintedHeight) / 2
            text: bannerText ? bannerText : "默认文本"
            font.pixelSize: 48
            font.bold: true
            color: "#FFDE59"
            layer.enabled: true
            layer.smooth: true
            antialiasing: true
            renderType: Text.QtRendering
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            textFormat: Text.RichText
            elide: Text.ElideNone
            wrapMode: Text.NoWrap
        }

        Text {
            id: messageText2
            // 紧跟在第一个文本之后
            x: textOffset + (messageText1.paintedWidth ? messageText1.paintedWidth : 0) + rightSpacing
            y: (parent.height - paintedHeight) / 2
            text: bannerText ? bannerText : "默认文本"
            font.pixelSize: 48
            font.bold: true
            color: "#FFDE59"
            layer.enabled: true
            layer.smooth: true
            antialiasing: true
            renderType: Text.QtRendering
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            textFormat: Text.RichText
            elide: Text.ElideNone
            wrapMode: Text.NoWrap
            visible: false // 默认不可见，只有当需要循环滚动时才显示
        }
    }
    
    // 条纹动画驱动（以每帧移动 Canvas 的 x 来模拟滚动，避免每帧重绘）
    Timer {
        id: stripeDriveTimer
        interval: 16
        repeat: true
        running: true
        onTriggered: {
            // 向左移动 1px；当偏移达到 -32 时复位为 0（图案周期为32px）
            stripeAnimX = stripeAnimX - 1;
            if (stripeAnimX <= -32) {
                stripeAnimX = 0;
            }
        }
    }
    
    // 文本滚动动画
    function startScrollingText() {
        // 通过Python端记录日志
        bannerObject.logDebug("开始滚动文本，计数: " + scrollCount + ", 模式: " + scrollMode);
        
        // 根据滚动模式决定是否滚动
        if (scrollMode === "never") {
            bannerObject.logDebug("滚动模式为never，不滚动文本");
            // 文本居中显示
            messageText1.x = (textContainer.width - messageText1.paintedWidth) / 2;
            messageText2.visible = false;
            if (textDriveTimer.running) textDriveTimer.stop();
            return;
        }

        // 如果是auto模式，检查文本是否需要滚动
        if (scrollMode === "auto" && messageText1.paintedWidth <= textContainer.width) {
            bannerObject.logDebug("滚动模式为auto且文本宽度小于窗口宽度，不滚动文本");
            // 文本居中显示
            messageText1.x = (textContainer.width - messageText1.paintedWidth) / 2;
            messageText2.visible = false;
            if (textDriveTimer.running) textDriveTimer.stop();
            return;
        }
        
        // 如果已经达到了最大滚动次数，则通知关闭（在开始前检测）
        if (maxScrolls > 0 && scrollCount >= maxScrolls) {
            bannerObject.logDebug("达到最大滚动次数，准备关闭横幅");
            bannerObject.close_banner_slot();
            return;
        }
        
    // 计算滚动终点 - 文本完全通过容器并消失
    var endX = -(messageText1.paintedWidth + rightSpacing);

    // 设置动画持续时间 (基于速度 px/s)，并四舍五入为整数
    // 使用更精确的滚动距离计算，确保文本完全滚动
    var effectiveSpeed = scrollSpeed > 0 ? scrollSpeed : 80; // 默认为80px/s，避免除以0
    var scrollDistance = messageText1.paintedWidth + textContainer.width + rightSpacing;
    var duration = Math.round((scrollDistance / effectiveSpeed) * 1000);
        bannerObject.logDebug("动画参数 - 持续时间: " + duration + " 终点: " + endX + " 距离: " + scrollDistance);
        
        // 使用基于定时器的驱动 (textDriveTimer) 来实现平滑循环滚动
        // 初始化偏移，使第一条文本从右侧进入
        textOffset = textContainer.width;
        // 设置文本内容并决定是否启用第二个副本
        messageText1.text = messageText2.text = messageText1.text ? messageText1.text : bannerText;
        // 当文本宽度超出容器宽度时启用循环副本
        if (messageText1.paintedWidth > textContainer.width) {
            messageText2.visible = true;
        } else {
            messageText2.visible = false;
        }
        // 启动定时器
        if (!textDriveTimer.running) {
            textDriveTimer.start();
        }
    }

    // 基于每帧更新的文本驱动定时器（比动态 NumberAnimation 更可控以避免跳帧/抽搐）
    Timer {
        id: textDriveTimer
        interval: 16
        repeat: true
        running: false
        onTriggered: {
            // 以 scrollSpeed(px/s) 驱动偏移
            // 以 16ms 近似每帧时间计算位移（与 timer.interval 保持一致）
            var delta = scrollSpeed * 16 / 1000.0;
            if (delta <= 0) delta = 1; // 防止为0导致无法移动
            textOffset -= delta;
            var cycle = messageText1.paintedWidth + rightSpacing;
            if (cycle <= 0) return;
            // 当偏移超出周期，说明完成一次完整滚动周期
            if (textOffset <= -cycle) {
                // 完成一次循环
                // 先回环到屏幕右侧以准备下一次滚动
                textOffset = textContainer.width;
                // 若配置了最大滚动次数，则在每次完整循环后增加计数并检测是否达到上限
                if (maxScrolls > 0) {
                    scrollCount = scrollCount + 1;
                    bannerObject.logDebug("已完成完整滚动次数: " + scrollCount);
                    if (scrollCount >= maxScrolls) {
                        bannerObject.logDebug("达到最大滚动次数，停止滚动并关闭横幅");
                        // 停止定时器并触发 Python 的关闭流程
                        if (textDriveTimer.running) textDriveTimer.stop();
                        bannerObject.close_banner_slot();
                        return;
                    }
                }
            }
        }
    }
    
    // 淡入动画
    NumberAnimation on opacity {
        id: fadeInAnimation
        from: 0.0
        to: 1.0
        duration: 1500
        easing.type: Easing.InOutQuad
        running: true  // 默认启动
    }
    
    // 淡出动画（默认不运行）
    NumberAnimation {
        id: fadeOutAnimation
        target: root
        property: "opacity"
        from: 1.0
        to: 0.0
        duration: 1500
        easing.type: Easing.InOutQuad
        running: false
        onFinished: {
            bannerObject.logDebug("淡出动画完成");
            // 调用Python对象的方法
            bannerObject.handleFadeOutFinished();
        }
    }
    
    function startFadeIn() {
        // QML中默认启动了淡入动画
    }
    
    function startFadeOut() {
        bannerObject.logDebug("开始淡出动画");
        // 停止淡入动画（如果正在运行）
        if (fadeInAnimation.running) {
            fadeInAnimation.stop();
        }
        // 启动淡出动画
        fadeOutAnimation.start();
    }

    // 清理函数：供 Python 在销毁 QML 前调用
    function cleanup() {
        // 停止定时器和动画，清理临时资源
        if (textDriveTimer.running) {
            textDriveTimer.stop();
        }
        if (stripeDriveTimer.running) {
            stripeDriveTimer.stop();
        }
    }

}