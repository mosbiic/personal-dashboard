"""API Token 认证模块 - 只支持 Cloudflare Access SSO"""
from fastapi import Request, HTTPException, Depends
from functools import wraps


class CloudflareAccessAuth:
    """Cloudflare Access 认证类 - 只使用 CF Headers"""
    
    async def __call__(self, request: Request) -> bool:
        """FastAPI 依赖调用 - 只检查 Cloudflare Access Headers"""
        # 检查 Cloudflare Access Headers (SSO 模式)
        cf_email = request.headers.get("CF-Access-Authenticated-User-Email")
        
        if cf_email:
            # Cloudflare Access 认证成功
            return True
        
        # 本地开发模式检测
        host = request.headers.get("Host", "")
        if "localhost" in host or "127.0.0.1" in host:
            raise HTTPException(
                status_code=401,
                detail="Local development mode. Please use Cloudflare Tunnel (https://*.mosbiic.com) or set up local CF Access headers for testing."
            )
        
        # 生产环境必须通过 Cloudflare Access
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
