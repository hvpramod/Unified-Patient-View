from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from app.routers import patients, summaries, conflicts, recommendations, audit, admin

log = structlog.get_logger()

app = FastAPI(
    title="UPV Gateway API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in prod via ingress
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    log.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(patients.router, prefix="/api/v1")
app.include_router(summaries.router, prefix="/api/v1")
app.include_router(conflicts.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway-api"}


@app.get("/api/v1")
async def api_root():
    return {"service": "Unified Patient View API", "version": "1.0.0"}
