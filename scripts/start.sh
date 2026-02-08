#!/bin/bash
# Dashboard 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# 固定端口配置
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo "🚀 启动 Personal Dashboard..."
echo "   后端端口: $BACKEND_PORT"
echo "   前端端口: $FRONTEND_PORT"

# 检查环境
check_env() {
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        echo "❌ 错误: 找不到 .env 文件"
        echo "请复制 .env.example 到 .env 并配置环境变量"
        exit 1
    fi
}

# 启动后端
start_backend() {
    echo "📦 启动后端服务..."
    cd "$BACKEND_DIR"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo "创建 Python 虚拟环境..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # 安装依赖
    pip install -q -r requirements.txt
    
    # 启动服务
    echo "🌐 后端运行在 http://localhost:$BACKEND_PORT"
    uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/dashboard_backend.pid
}

# 启动前端
start_frontend() {
    echo "🎨 启动前端服务..."
    cd "$FRONTEND_DIR"
    
    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        echo "安装前端依赖..."
        npm install
    fi
    
    echo "🌐 前端运行在 http://localhost:$FRONTEND_PORT"
    npm run dev -- --port $FRONTEND_PORT &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/dashboard_frontend.pid
}

# 停止服务
stop() {
    echo "🛑 停止服务..."
    if [ -f /tmp/dashboard_backend.pid ]; then
        kill $(cat /tmp/dashboard_backend.pid) 2>/dev/null || true
        rm /tmp/dashboard_backend.pid
    fi
    if [ -f /tmp/dashboard_frontend.pid ]; then
        kill $(cat /tmp/dashboard_frontend.pid) 2>/dev/null || true
        rm /tmp/dashboard_frontend.pid
    fi
    echo "✅ 服务已停止"
}

# Cloudflare Tunnel 配置
setup_tunnel() {
    echo "🌐 配置 Cloudflare Tunnel..."
    
    # 检查 cloudflared
    if ! command -v cloudflared &> /dev/null; then
        echo "安装 cloudflared..."
        brew install cloudflared 2>/dev/null || {
            echo "请手动安装 cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation"
            exit 1
        }
    fi
    
    # 创建配置文件
    mkdir -p ~/.cloudflared
    
    cat > ~/.cloudflared/dashboard.yml << EOF
tunnel: dashboard-tunnel
credentials-file: ~/.cloudflared/dashboard-tunnel.json

ingress:
  # API 路由
  - hostname: dashboard.mosbiic.com
    path: /api
    service: http://localhost:8000
  
  # 前端静态文件
  - hostname: dashboard.mosbiic.com
    service: http://localhost:5173
  
  # 默认回退
  - service: http_status:404
EOF

    echo "✅ Tunnel 配置已创建: ~/.cloudflared/dashboard.yml"
    echo ""
    echo "下一步:"
    echo "1. 登录 Cloudflare: cloudflared tunnel login"
    echo "2. 创建隧道: cloudflared tunnel create dashboard-tunnel"
    echo "3. 启动隧道: cloudflared tunnel run dashboard-tunnel"
}

# 命令处理
case "${1:-start}" in
    start)
        check_env
        stop 2>/dev/null || true
        start_backend
        sleep 2
        start_frontend
        echo ""
        echo "✅ Dashboard 已启动!"
        echo "📱 前端: http://localhost:$FRONTEND_PORT"
        echo "🔌 API: http://localhost:$BACKEND_PORT"
        echo ""
        echo "按 Ctrl+C 停止服务"
        wait
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        $0 start
        ;;
    tunnel)
        setup_tunnel
        ;;
    *)
        echo "用法: $0 {start|stop|restart|tunnel}"
        exit 1
        ;;
esac
