from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import secrets

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # XSS Mitigation: Content Security Policy
        # Restrict scripts, styles, and images to self. Adjust as needed for production.
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: https://fastapi.tiangolo.com; "
            "connect-src 'self' http://localhost:5173;"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enforce HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Cross-Site Scripting (XSS) filter
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response
