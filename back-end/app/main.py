import os

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.fair import admin_router as saved_fares_router
from app.fair import router as fair_router
from app.fare_matrices import router as fare_matrices_router
from app.monitoring import router as monitoring_router
from app.monitoring.model import record_admin_action
from app.routes import router as routes_router
from app.stops import router as stops_router

app = FastAPI(title="Commute.ph API", description="Jeepney fare checker for Marikina City", version="1.0.0")

# Browsers may call the API only from these origins (comma-separated in CORS_ORIGINS)
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
# Browsers send the origin without a trailing slash, so "https://site.app/" would never match
origins_list = [origin.strip().rstrip("/") for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    # allow_origins doesn't match wildcards; on preview deployments also allow any *.vercel.app site
    allow_origin_regex=r"https://[a-z0-9-]+\.vercel\.app" if os.getenv("VERCEL_ENV") == "preview" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sent with every API response. The API only returns JSON, so the CSP allows nothing; the
# interactive docs (/docs, /redoc) load Swagger from a CDN and are left out
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
}
DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


@app.middleware("http")
async def security_and_audit(request: Request, call_next):
    response = await call_next(request)
    response.headers.update(SECURITY_HEADERS)
    if not request.url.path.startswith(DOCS_PATHS):
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

    # Every admin change is written to the audit log, including refused ones (4xx)
    admin = getattr(request.state, "admin", None)
    if admin and request.method not in ("GET", "HEAD", "OPTIONS"):
        await run_in_threadpool(record_admin_action, admin, request.method, request.url.path, response.status_code)
    return response


@app.get("/health", tags=["health"])
def health():
    """Basic liveness check for the host's health probe."""
    return {"status": "ok"}


app.include_router(routes_router.router)
app.include_router(stops_router.router)
app.include_router(stops_router.admin_router)
app.include_router(fair_router.router)
app.include_router(fare_matrices_router.router)
app.include_router(saved_fares_router.router)
app.include_router(monitoring_router.router)

# Vercel handler
handler = Mangum(app)
