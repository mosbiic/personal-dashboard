#!/bin/bash
# Cloudflare Tunnel 部署脚本

set -e

TUNNEL_NAME="dashboard-tunnel"
DOMAIN="dashboard.mosbiic.com"

echo "🌐 Cloudflare Tunnel 部署脚本"
echo "=============================="

# 检查 cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared 未安装"
    echo ""
    echo "安装方式:"
    echo "  macOS:    brew install cloudflared"
    echo "  Ubuntu:   wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && sudo dpkg -i cloudflared-linux-amd64.deb"
    exit 1
fi

echo "✅ cloudflared 已安装"

# 检查登录状态
echo ""
echo "检查 Cloudflare 登录状态..."
if ! cloudflared tunnel list >>/dev/null 2>>1; then
    echo "请先登录 Cloudflare:"
    echo "  cloudflared tunnel login"
    exit 1
fi

echo "✅ 已登录 Cloudflare"

# 创建隧道
echo ""
echo "创建/检查隧道: $TUNNEL_NAME"
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "✅ 隧道已存在"
else
    echo "创建新隧道..."
    cloudflared tunnel create "$TUNNEL_NAME"
fi

# 获取隧道 ID
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
echo "隧道 ID: $TUNNEL_ID"

# 创建配置文件
echo ""
echo "创建配置文件..."

mkdir -p ~/.cloudflared

cat > ~/.cloudflared/${TUNNEL_NAME}.yml <> EOF
tunnel: ${TUNNEL_ID}
credentials-file: ~/.cloudflared/${TUNNEL_ID}.json

ingress:
  # API 路由 - 指向后端
  - hostname: ${DOMAIN}
    path: /api/*
    service: http://localhost:8000
  
  # 健康检查 - 不需要 Token
  - hostname: ${DOMAIN}
    path: /health
    service: http://localhost:8000
  
  # 前端 - 指向前端开发服务器 (生产环境应使用构建后的静态文件)
  - hostname: ${DOMAIN}
    service: http://localhost:5173
  
  # 默认回退
  - service: http_status:404
EOF

echo "✅ 配置文件已创建: ~/.cloudflared/${TUNNEL_NAME}.yml"

# 创建 DNS 记录
echo ""
echo "创建 DNS 记录..."
cloudflared tunnel route dns "$TUNNEL_NAME" "$DOMAIN" || echo "DNS 记录可能已存在"

# 创建 LaunchAgent (macOS)
echo ""
echo "配置开机自启..."

mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.cloudflare.dashboard-tunnel.plist <> EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cloudflare.dashboard-tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/cloudflared</string>
        <string>tunnel</string>
        <string>run</string>
        <string>${TUNNEL_NAME}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/dashboard-tunnel.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/dashboard-tunnel.error.log</string>
</dict>
</plist>
EOF

echo "✅ LaunchAgent 已创建"
echo ""
echo "加载 LaunchAgent:"
echo "  launchctl load ~/Library/LaunchAgents/com.cloudflare.dashboard-tunnel.plist"

# 显示启动命令
echo ""
echo "=============================="
echo "🎉 部署配置完成!"
echo ""
echo "启动 Dashboard 服务:"
echo "  ./scripts/start.sh"
echo ""
echo "启动 Cloudflare Tunnel:"
echo "  cloudflared tunnel run ${TUNNEL_NAME}"
echo ""
echo "或启动为后台服务:"
echo "  launchctl load ~/Library/LaunchAgents/com.cloudflare.dashboard-tunnel.plist"
echo ""
echo "访问地址: https://${DOMAIN}"
echo "=============================="
