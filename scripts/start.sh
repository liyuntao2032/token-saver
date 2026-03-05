#!/bin/bash
# Token节约大师 V2.0 - 快速启动脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "======================================================================"
echo "🚀 Token节约大师 V2.0 - 快速启动"
echo "======================================================================"
echo ""
echo "选择启动模式:"
echo "  1) 启动后台服务（推荐）"
echo "  2) 启动交互式监控"
echo "  3) 查看统计仪表盘"
echo "  4) 查看服务状态"
echo "  5) 停止服务"
echo ""
read -p "请选择 (1-5): " choice

case $choice in
  1)
    echo ""
    echo "启动后台服务..."
    python3 "$SCRIPT_DIR/service.py" start
    ;;
  2)
    echo ""
    echo "启动交互式监控..."
    echo "按 Ctrl+C 停止"
    python3 "$SCRIPT_DIR/monitor.py" --monitor
    ;;
  3)
    echo ""
    python3 "$SCRIPT_DIR/dashboard.py"
    ;;
  4)
    echo ""
    python3 "$SCRIPT_DIR/service.py" status
    ;;
  5)
    echo ""
    python3 "$SCRIPT_DIR/service.py" stop
    ;;
  *)
    echo "无效选择"
    ;;
esac
