import time
from collections import defaultdict, deque
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analytics, auth, health, platform, tickets

app = FastAPI(title="TicketSense API", version="0.1.0")

_request_windows: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def enterprise_security(request: Request, call_next):
    now = time.monotonic(); client = request.client.host if request.client else "unknown"
    window = _request_windows[client]
    while window and now - window[0] > 60: window.popleft()
    if len(window) >= 180:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    window.append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(analytics.router)
app.include_router(platform.router)
