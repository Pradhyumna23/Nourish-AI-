"""
Custom middleware for the FastAPI application.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
import traceback


class LoggingMiddleware:
    """Middleware for request/response logging."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Create request object
        request = Request(scope, receive)
        
        # Log request
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = None
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal response, status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            logger.error(f"Request {request_id} failed: {str(e)}")
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response {request_id}: {status_code} "
                f"({duration:.3f}s)"
            )


class ErrorHandlingMiddleware:
    """Middleware for global error handling."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        try:
            await self.app(scope, receive, send)
        except HTTPException:
            # Let FastAPI handle HTTP exceptions
            raise
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unhandled exception: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Create error response
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_type": type(e).__name__,
                    "timestamp": time.time()
                }
            )
            
            await response(scope, receive, send)


class CORSMiddleware:
    """Custom CORS middleware with detailed logging."""
    
    def __init__(self, app, allowed_origins=None, allowed_methods=None, allowed_headers=None):
        self.app = app
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or ["*"]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
            response.headers["Access-Control-Max-Age"] = "86400"
            
            await response(scope, receive, send)
            return
        
        # Add CORS headers to response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"access-control-allow-origin"] = (origin or "*").encode()
                headers[b"access-control-allow-credentials"] = b"true"
                message["headers"] = list(headers.items())
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


class RateLimitMiddleware:
    """Simple rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute=60):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        self.last_reset = time.time()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"
        
        # Reset counts every minute
        current_time = time.time()
        if current_time - self.last_reset > 60:
            self.request_counts.clear()
            self.last_reset = current_time
        
        # Check rate limit
        current_count = self.request_counts.get(client_ip, 0)
        if current_count >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": 60 - (current_time - self.last_reset)
                }
            )
            await response(scope, receive, send)
            return
        
        # Increment count
        self.request_counts[client_ip] = current_count + 1
        
        await self.app(scope, receive, send)


class SecurityHeadersMiddleware:
    """Middleware to add security headers."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Add security headers
                headers[b"x-content-type-options"] = b"nosniff"
                headers[b"x-frame-options"] = b"DENY"
                headers[b"x-xss-protection"] = b"1; mode=block"
                headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                headers[b"content-security-policy"] = b"default-src 'self'"
                
                message["headers"] = list(headers.items())
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


class RequestValidationMiddleware:
    """Middleware for request validation and sanitization."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            response = JSONResponse(
                status_code=413,
                content={"detail": "Request entity too large"}
            )
            await response(scope, receive, send)
            return
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data", "application/x-www-form-urlencoded")):
                logger.warning(f"Invalid content type: {content_type}")
        
        await self.app(scope, receive, send)


def setup_middleware(app):
    """Setup all middleware for the application."""
    
    # Add middleware in reverse order (last added is executed first)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    logger.info("Middleware setup completed")
