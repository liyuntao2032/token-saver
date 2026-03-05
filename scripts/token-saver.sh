#!/bin/bash
# Token节约大师 V2.1 - 管理脚本

PLIST_NAME="com.openclaw.token-saver"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
SERVICE_DIR="/Users/uknown/.openclaw-autoclaw/workspace/skills/token-saver-v2/scripts"
LOG_FILE="$SERVICE_DIR/token_saver.log"

case "$1" in
    start)
        echo "🚀 启动 Token节约大师 V2.1..."
        if launchctl list | grep -q "$PLIST_NAME"; then
            echo "⚠️  服务已在运行中"
        else
            launchctl load "$PLIST_PATH"
            sleep 1
            if launchctl list | grep -q "$PLIST_NAME"; then
                echo "✅ 服务启动成功！"
                echo "📋 PID: $(launchctl list | grep "$PLIST_NAME" | awk '{print $1}')"
                echo "📝 日志: $LOG_FILE"
            else
                echo "❌ 服务启动失败"
            fi
        fi
        ;;
    
    stop)
        echo "🛑 停止 Token节约大师 V2.1..."
        if launchctl list | grep -q "$PLIST_NAME"; then
            launchctl unload "$PLIST_PATH"
            echo "✅ 服务已停止"
        else
            echo "⚠️  服务未运行"
        fi
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        echo "📊 Token节约大师 V2.1 状态"
        echo "===================="
        if launchctl list | grep -q "$PLIST_NAME"; then
            PID=$(launchctl list | grep "$PLIST_NAME" | awk '{print $1}')
            echo "✅ 状态: 运行中"
            echo "📋 PID: $PID"
            echo ""
            
            # 显示最近日志
            if [ -f "$LOG_FILE" ]; then
                echo "📝 最近日志:"
                echo "--------------------"
                tail -10 "$LOG_FILE"
            fi
        else
            echo "❌ 状态: 未运行"
        fi
        ;;
    
    log)
        echo "📝 Token节约大师 V2.1 日志"
        echo "===================="
        if [ -f "$LOG_FILE" ]; then
            if [ "$2" = "-f" ]; then
                tail -f "$LOG_FILE"
            else
                tail -50 "$LOG_FILE"
            fi
        else
            echo "⚠️  日志文件不存在"
        fi
        ;;
    
    test)
        echo "🧪 测试压缩功能..."
        cd "$SERVICE_DIR"
        python3 service.py test
        ;;
    
    install)
        echo "📦 安装 Token节约大师 V2.1..."
        
        # 检查 plist 文件
        if [ ! -f "$PLIST_PATH" ]; then
            echo "❌ plist 文件不存在: $PLIST_PATH"
            exit 1
        fi
        
        # 加载服务
        launchctl load "$PLIST_PATH"
        sleep 1
        
        if launchctl list | grep -q "$PLIST_NAME"; then
            echo "✅ 安装成功！"
            echo ""
            echo "服务将在后台自动运行，每2分钟检查一次session大小"
            echo "当session超过10,000 tokens时自动压缩（70%压缩率）"
            echo ""
            echo "管理命令:"
            echo "  $0 status   - 查看状态"
            echo "  $0 log      - 查看日志"
            echo "  $0 stop     - 停止服务"
            echo "  $0 restart  - 重启服务"
        else
            echo "❌ 安装失败"
        fi
        ;;
    
    uninstall)
        echo "🗑️  卸载 Token节约大师 V2.1..."
        
        # 停止服务
        if launchctl list | grep -q "$PLIST_NAME"; then
            launchctl unload "$PLIST_PATH"
            echo "✅ 服务已停止"
        fi
        
        # 删除 plist 文件
        if [ -f "$PLIST_PATH" ]; then
            rm "$PLIST_PATH"
            echo "✅ plist 文件已删除"
        fi
        
        echo "✅ 卸载完成"
        ;;
    
    *)
        echo "Token节约大师 V2.1 - 管理脚本"
        echo ""
        echo "用法: $0 {start|stop|restart|status|log|test|install|uninstall}"
        echo ""
        echo "命令:"
        echo "  start     - 启动服务"
        echo "  stop      - 停止服务"
        echo "  restart   - 重启服务"
        echo "  status    - 查看状态"
        echo "  log       - 查看日志（使用 -f 实时监控）"
        echo "  test      - 测试压缩功能"
        echo "  install   - 安装为系统服务"
        echo "  uninstall - 卸载系统服务"
        exit 1
        ;;
esac
