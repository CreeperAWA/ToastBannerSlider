import QtQuick 2.15
import QtQuick.Window 2.15

Item {
    id: root
    width: 1920
    height: 140
    opacity: 1.0
    
    property string bannerText: ""
    property int stripeOffset: 0
    property int maxScrolls: 0
    property real scrollSpeed: 0.0
    property int rightSpacing: 0
    property int bannerSpacing: 10  // 横幅间距
    property int scrollCount: 0
    property var textAnimation: null  // 添加动画变量定义
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
    
    // 背景红色矩形
    Rectangle {
        id: background
        anchors.fill: parent
        color: "#b3080a"  // 红色背景
        opacity: bannerOpacity  // 使用配置的横幅透明度
        // 注意: bannerSpacing 用于控制多个横幅组件之间的垂直间距，
        // 应由父级容器(如Column)使用，而不是作为内部边距
        // 启用层渲染以提高性能
        layer.enabled: true
        layer.smooth: true
    }
    
    // 条纹图案
    Repeater {
        id: stripeCanvasRepeater
        model: 2  // 顶部和底部条纹
        
        Canvas {
            id: stripeCanvas
            anchors.fill: parent
            // 启用抗锯齿和层渲染以提高性能
            antialiasing: true
            layer.enabled: true
            layer.smooth: true
            renderTarget: Canvas.FramebufferObject
            renderStrategy: Canvas.Threaded
            
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);
                
                // 确定Y坐标 (0为顶部，height-32为底部)
                var y = (index === 0) ? 0 : parent.height - 32;
                
                // 绘制黄色条纹
                ctx.fillStyle = "#ccffde59"; // 带透明度的黄色
                
                for (var x = -40; x < width + 40; x += 32) {
                    ctx.beginPath();
                    ctx.moveTo(x - stripeOffset, y + 32);
                    ctx.lineTo(x + 16 - stripeOffset, y);
                    ctx.lineTo(x + 32 - stripeOffset, y);
                    ctx.lineTo(x + 16 - stripeOffset, y + 32);
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
        
        Text {
            id: messageText
            // 初始位置在右侧
            x: textContainer.width
            y: (parent.height - paintedHeight) / 2
            text: bannerText ? bannerText : "默认文本"
            font.pixelSize: 48  // 增大字体大小从24到48
            font.bold: true
            color: "#FFDE59"
            font.family: "Microsoft YaHei UI"
            // 启用层渲染和抗锯齿以提高性能和显示质量
            layer.enabled: true
            layer.smooth: true
            antialiasing: true
            renderType: Text.QtRendering
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            // 添加文本渲染优化属性，解决长文本截断问题
            textFormat: Text.PlainText
            elide: Text.ElideNone
            wrapMode: Text.NoWrap
        }
    }
    
    // 条纹动画 - 使用连续动画替代定时器
    Behavior on stripeOffset {
        NumberAnimation {
            duration: 16
            easing.type: Easing.Linear
        }
    }

    // 启动条纹动画的定时器（只执行一次）
    Timer {
        id: stripeAnimationTimer
        interval: 16
        repeat: true
        running: true
        onTriggered: {
            stripeOffset = (stripeOffset + 1) % 32;
            // 触发所有条纹重绘
            for (var i = 0; i < stripeCanvasRepeater.count; i++) {
                var canvas = stripeCanvasRepeater.itemAt(i);
                if (canvas) {
                    canvas.requestPaint();
                }
            }
        }
    }
    
    // 文本滚动动画
    function startScrollingText() {
        // 通过Python端记录日志
        bannerObject.logDebug("开始滚动文本，当前滚动次数: " + scrollCount + " 最大滚动次数: " + maxScrolls);
        bannerObject.logDebug("滚动模式: " + scrollMode);
        
        // 根据滚动模式决定是否滚动
        if (scrollMode === "never") {
            bannerObject.logDebug("滚动模式为never，不滚动文本");
            // 文本居中显示
            messageText.x = (textContainer.width - messageText.paintedWidth) / 2;
            return;
        }
        
        // 如果是auto模式，检查文本是否需要滚动
        if (scrollMode === "auto" && messageText.paintedWidth <= textContainer.width) {
            bannerObject.logDebug("滚动模式为auto且文本宽度小于窗口宽度，不滚动文本");
            // 文本居中显示
            messageText.x = (textContainer.width - messageText.paintedWidth) / 2;
            return;
        }
        
        // 如果已经达到了最大滚动次数，则通知关闭
        if (scrollCount >= maxScrolls && maxScrolls > 0) {
            bannerObject.logDebug("达到最大滚动次数，准备关闭横幅");
            // 调用Python对象的方法
            bannerObject.close_banner_slot();
            return;
        }
        
        // 增加滚动计数（在动画开始前增加）
        scrollCount++;
        bannerObject.logDebug("增加滚动计数，当前计数: " + scrollCount);
        
        // 计算滚动终点 - 文本完全通过容器并消失
        var endX = -(messageText.paintedWidth + rightSpacing);
        
        // 设置动画持续时间 (基于速度 px/s)，并四舍五入为整数
        // 修复计算方式，使用textContainer.width而不是root.width
        var scrollDistance = textContainer.width + messageText.paintedWidth + rightSpacing;
        var duration = Math.round((scrollDistance / scrollSpeed) * 1000);
        bannerObject.logDebug("动画参数 - 持续时间: " + duration + " 终点: " + endX);
        
        // 如果已经有动画在运行，停止它
        if (textAnimation != null) {
            if (textAnimation.running) {
                textAnimation.stop();
            }
            textAnimation.destroy();
        }
        
        // 创建新的动画
        // 修复动画起始位置，使用textContainer.width而不是root.width
        textAnimation = Qt.createQmlObject('import QtQuick 2.15; NumberAnimation { target: messageText; property: "x"; from: ' + textContainer.width + '; to: ' + endX + '; duration: ' + duration + '; easing.type: Easing.Linear; }', root);
        
        textAnimation.finished.connect(function() {
            bannerObject.logDebug("文本动画完成，重新开始");
            // 当动画完成时，重新开始
            // 修复重新开始位置，使用textContainer.width而不是root.width
            messageText.x = textContainer.width;
            startScrollingText();
        });
        
        textAnimation.start();
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
    
    // 用于销毁动画对象的清理函数
    function cleanup() {
        if (textAnimation != null) {
            if (textAnimation.running) {
                textAnimation.stop();
            }
            textAnimation.destroy();
            textAnimation = null;
        }
    }
    
    // 延迟启动文本动画的定时器
    Timer {
        id: startTextAnimationTimer
        interval: 100
        repeat: false
        onTriggered: {
            startScrollingText();
        }
    }
}