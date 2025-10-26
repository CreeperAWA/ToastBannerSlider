import QtQuick 2.15
import QtQuick.Window 2.15

Item {
    id: root
    width: 1920
    height: 128
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
    property real iconScale: 1.0  // 图标缩放比例
    property int leftMargin: 93   // 左边距
    property int rightMargin: 93  // 右边距
    property int labelMaskWidth: 305  // 标签遮罩宽度
    property real fontSize: 48.0  // 字体大小
    property int labelOffsetX: 0  // 标签文本x轴偏移
    property string iconPath: ""  // 图标路径
    property int fadeAnimationDuration: 1500  // 淡入淡出动画时间
    
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
            bannerObject.logDebug("  iconScale: " + iconScale);
            bannerObject.logDebug("  leftMargin: " + leftMargin);
            bannerObject.logDebug("  rightMargin: " + rightMargin);
            bannerObject.logDebug("  labelMaskWidth: " + labelMaskWidth);
            bannerObject.logDebug("  fontSize: " + fontSize);
            bannerObject.logDebug("  labelOffsetX: " + labelOffsetX);
            bannerObject.logDebug("  iconPath: " + iconPath);
            bannerObject.logDebug("  fadeAnimationDuration: " + fadeAnimationDuration);
            
            // 延迟启动文本动画
            startTextAnimationTimer.start();
        }
    }
    
    // 背景深灰色矩形
    Rectangle {
        id: background
        anchors.fill: parent
        color: "#1e1e1e"  // 深灰色背景
        opacity: bannerOpacity  // 使用配置的横幅透明度
        layer.enabled: true
        layer.smooth: true
    }
    
    // 标签区域遮罩 - 透明遮罩，用于覆盖文字
    Item {
        id: labelMask
        x: leftMargin
        y: 0
        width: labelMaskWidth
        height: parent.height
        // 透明遮罩，用于覆盖滚动文字
    }
    
    // 标签图标和文本容器
    Item {
        id: labelContainer
        x: leftMargin
        y: 0
        width: labelMaskWidth
        height: parent.height
        
        // 喇叭图标 - 使用图片而不是文本符号
        Image {
            id: iconImage
            x: 10 * iconScale
            anchors.verticalCenter: parent.verticalCenter
            width: 32 * iconScale
            height: 32 * iconScale
            source: iconPath ? "file:///" + iconPath : ""
            fillMode: Image.PreserveAspectFit
            visible: iconPath && iconPath !== ""
            
            // 如果图标路径无效，则显示文本图标
            Text {
                id: iconLabel
                anchors.centerIn: parent
                text: "🔊"
                font.pixelSize: 32 * iconScale
                color: "#ffffff"
                renderType: Text.NativeRendering
                antialiasing: true
                visible: !iconImage.visible
            }
        }
        
        // 标签文本
        Text {
            id: labelText
            anchors.left: iconImage.right
            anchors.leftMargin: 10 + labelOffsetX
            anchors.verticalCenter: parent.verticalCenter
            text: "消息提醒:"
            font.pixelSize: fontSize / 2
            font.bold: true
            color: "#3b9fdc"  // 蓝色
            renderType: Text.NativeRendering
            antialiasing: true
        }
    }
    
    // 文本显示区域
    Item {
        id: textContainer
        x: leftMargin + labelMaskWidth
        y: 0
        width: parent.width - leftMargin - labelMaskWidth - rightMargin
        height: parent.height
        clip: true  // 启用裁剪，确保文字在区域内显示
        
        Text {
            id: messageText
            // 初始位置在右侧
            x: textContainer.width
            y: (parent.height - paintedHeight) / 2
            text: bannerText ? bannerText : "默认文本"
            font.pixelSize: fontSize / 2
            font.bold: true
            color: "#ffffff"
            font.family: "Microsoft YaHei UI"
            layer.enabled: true
            layer.smooth: true
            antialiasing: true
            renderType: Text.NativeRendering
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
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
        
        // 计算可用宽度（屏幕宽度减去左右边距和标签遮罩宽度）
        var availableWidth = parent.width - leftMargin - labelMaskWidth - rightMargin;
        
        // 计算滚动终点 - 文本完全通过容器并消失
        var endX = -(messageText.paintedWidth + rightSpacing);
        
        // 计算滚动距离和持续时间
        var scrollDistance = availableWidth + messageText.paintedWidth + rightSpacing;
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
        textAnimation = Qt.createQmlObject('import QtQuick 2.15; NumberAnimation { target: messageText; property: "x"; from: ' + availableWidth + '; to: ' + endX + '; duration: ' + duration + '; easing.type: Easing.Linear; }', root);
        
        textAnimation.finished.connect(function() {
            bannerObject.logDebug("文本动画完成，重新开始");
            // 当动画完成时，重新开始
            messageText.x = availableWidth;
            startScrollingText();
        });
        
        textAnimation.start();
    }
    
    // 淡入动画
    NumberAnimation on opacity {
        id: fadeInAnimation
        from: 0.0
        to: 1.0
        duration: fadeAnimationDuration
        easing.type: Easing.InOutQuad
        running: true
    }
    
    // 淡出动画（默认不运行）
    NumberAnimation {
        id: fadeOutAnimation
        target: root
        property: "opacity"
        from: 1.0
        to: 0.0
        duration: fadeAnimationDuration
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