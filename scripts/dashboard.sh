#!/bin/bash
# Dashboard 启动脚本

WORKSPACE_DIR="/Users/mosbii/.openclaw/workspace/personal-dashboard"
PID_FILE="/tmp/dashboard.pid"

case "$1" in
  start)
    echo "启动 Dashboard 服务..."
    
    # 启动后端 API
    cd "$WORKSPACE_DIR/backend"
    source venv/bin/activate
    nohup uvicorn main:app --host 0.0.0.0 --port 18000 > /tmp/dashboard_api.log 2>&1 &
    echo $! > "$PID_FILE.api"
    
    # 启动前端静态服务器
    cd "$WORKSPACE_DIR/frontend/dist"
    nohup python3 -m http.server 13002 > /tmp/dashboard_web.log 2>&1 &
    echo $! > "$PID_FILE.web"
    
    echo "Dashboard 已启动"
    echo "- API: http://localhost:18000"
    echo "- Web: http://localhost:13002"
    echo "- 公网: https://dashboard.mosbiic.com"
    ;;
    
  stop)
    echo "停止 Dashboard 服务..."
    if [ -f "$PID_FILE.api" ]; then
      kill $(cat "$PID_FILE.api") 2>/dev/null
      rm "$PID_FILE.api"
    fi
    if [ -f "$PID_FILE.web" ]; then
      kill $(cat "$PID_FILE.web") 2>/dev/null
      rm "$PID_FILE.web"
    fi
    echo "Dashboard 已停止"
    ;;
    
  restart)
    $0 stop
    sleep 2
    $0 start
    ;;
    
  status)
    echo "=== Dashboard 服务状态 ==="
    if curl -s http://localhost:18000/health > /dev/null 2>&1; then
      echo "✅ API (port 18000): 运行中"
    else
      echo "❌ API (port 18000): 未运行"
    fi
    
    if curl -s http://localhost:13002/ > /dev/null 2>&1; then
      echo "✅ Web (port 13002): 运行中"
    else
      echo "❌ Web (port 13002): 未运行"
    fi
    
    echo ""
    echo "=== 公网访问测试 ==="
    if curl -s https://dashboard.mosbiic.com/health > /dev/null 2>&1; then
      echo "✅ https://dashboard.mosbiic.com: 可访问"
    else
      echo "❌ https://dashboard.mosbiic.com: 无法访问"
    fi
    ;;
    
  logs)
    echo "=== API 日志 (最近 20 行) ==="
    tail -20 /tmp/dashboard_api.log 2>/dev/null || echo "暂无日志"
    echo ""
    echo "=== Web 日志 (最近 20 行) ==="
    tail -20 /tmp/dashboard_web.log 2>/dev/null || echo "暂无日志"
    ;;
    
  *)
    echo "用法: $0 {start|stop|restart|status|logs}"
    exit 1
    ;;
esac
