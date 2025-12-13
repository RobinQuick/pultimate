from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# IP-based limiting for simplicity in V1
limiter = Limiter(key_func=get_remote_address)

def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )
