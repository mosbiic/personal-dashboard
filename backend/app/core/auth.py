"""API Token 认证模块 - 只支持 Cloudflare Access SSO"""
from fastapi import Request, HTTPException, Depends
from functools import wraps
import os

# Cloudflare Access 是否启用（生产环境自动启用）
CF_ACCESS_ENABLED = os.getenv("CF_ACCESS_ENABLED", "true").lower() == "true"

class CloudflareAccessAuth:
    """Cloudflare Access 认证类 - 优先检查 IP 白名单，然后 CF Headers"""
    
    async def __call__(self, request: Request) -> bool:
        """FastAPI 依赖调用 - 优先检查 IP 白名单，然后 Cloudflare Access Headers"""
        # 1. 检查 IP 白名单（本地开发自动通过）
        client_ip = request.client.host if request.client else None
        if client_ip in ("127.0.0.1", "localhost", "::1"):
            return True
        
        # 2. 检查 Cloudflare Access Headers (SSO 模式)
        cf_email = request.headers.get("CF-Access-Authenticated-User-Email")
        
        if cf_email:
            # Cloudflare Access 认证成功
            return True
        
        # 3. 生产环境必须通过 Cloudflare Access
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please access via https://*.mosbiic.com with Cloudflare Access."
        )


# 全局实例
cf_auth = CloudflareAccessAuth()


async def verify_auth(request: Request) -> bool:
    """
    FastAPI 依赖 - 验证 Cloudflare Access
    
    用法:
        @app.get("/protected")
        async def protected_route(authenticated: bool = Depends(verify_auth)):
            return {"message": "Access granted"}
    """
    return await cf_auth(request)
