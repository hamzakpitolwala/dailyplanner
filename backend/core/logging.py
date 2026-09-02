import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class LoggerFactory:
    """Factory for creating and configuring structured loggers."""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            # Add basic stream handler if no handlers exist
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)
            cls._loggers[name] = logger
        return cls._loggers[name]

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = LoggerFactory.get_logger("api_access")

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            process_time = time.time() - start_time
            
            user_id = "unknown"
            if hasattr(request.state, "user") and request.state.user:
                user_id = request.state.user.id

            self.logger.info(
                f"method={request.method} route={request.url.path} "
                f"status={status_code} latency={process_time:.4f}s user_id={user_id}"
            )
            
        return response
