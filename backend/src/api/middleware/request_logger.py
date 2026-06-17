import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.logger import logger

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        logger.info(f"Incoming Request: {request.method} {request.url.path}")
        
        try:
            response: Response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            logger.info(f"Completed Request: {request.method} {request.url.path} - Status: {response.status_code} - {process_time:.2f}ms")
            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"Failed Request: {request.method} {request.url.path} - Exception: {str(e)} - {process_time:.2f}ms")
            raise e
