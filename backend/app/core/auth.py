"""API Token 认证模块 - 支持 Cloudflare Access SSO"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
import os

security = HTTPBearer(auto_error=False)

# Cloudflare Access 配置
CF_ACCESS_ENABLED = os.getenv("CF_ACCESS_ENABLED", "false").lower() == "true"


class TokenAuth:
    """Token 认证类"""
    
    def __init__(self):
        # 从环境变量获取 token，如果没有则使用默认值（仅开发环境）
        self.api_token = os.getenv("DASHBOARD_API_TOKEN", "")
        self.enabled = bool(self.api_token) and not CF_ACCESS_ENABLED
    
    def verify_token(self, token: str) -> bool:
        """验证 token"""
        if not self.enabled and not CF_ACCESS_ENABLED:
            return True  # 未启用认证时允许访问
        return token == self.api_token
    
    async def __call__(self, request: Request) -> bool:
        """FastAPI 依赖调用"""
        # 1. 优先检查 Cloudflare Access Headers (SSO 模式)
        cf_email = request.headers.get("CF-Access-Authenticated-User-Email")
        if cf_email:
            # Cloudflare Access 认证成功
            return True
        
        # 2. 检查本地 Token (开发模式或 fallback)
        if not self.enabled:
            return True
        
        # 从 header 获取 token
        auth_header = request.headers.get("Authorization", "")
        
        # 支持 "Bearer token" 或纯 token 格式
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = auth_header
        
        # 也支持从 query param 获取 (方便测试)
        if not token:
            token = request.query_params.get("token", "")
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="缺少访问 token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not self.verify_token(token):
            raise HTTPException(
                status_code=403,
                detail="无效的 token"
            )
        
        return True


# 全局实例
token_auth = TokenAuth()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> bool:
    """
    FastAPI 依赖 - 验证 token
    支持 Cloudflare Access 或本地 Token
    
    用法:
        @app.get("/protected")
        async def protected_route(authenticated: bool = Depends(verify_token)):
            return {"message": "Access granted"}
    """
    # 注意：这里需要在路由函数中获取 request 对象来检查 Cloudflare Headers
    # 简化版本：如果启用了 Cloudflare Access，跳过本地 token 验证
    if CF_ACCESS_ENABLED:
        return True
    
    if not token_auth.enabled:
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="缺少 Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not token_auth.verify_token(credentials.credentials):
        raise HTTPException(
            status_code=403,
            detail="无效的 token"
        )
    
    return True
