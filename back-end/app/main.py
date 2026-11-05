import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.fair import router as fair_router
from app.route_point import router as route_point_router
from app.routes import router as routes_router

app = FastAPI(title="Commute.ph API", description="Jeepney fare checker for Marikina City", version="1.0.0")

# Configure CORS for production and development
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
origins_list = [origin.strip() for origin in cors_origins.split(",")]

# Add wildcard for Vercel preview deployments if needed
if os.getenv("VERCEL_ENV") == "preview":
    origins_list.append("https://*.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health():
    """Basic liveness check for the host's health probe."""
    return {"status": "ok"}


app.include_router(routes_router.router)
app.include_router(route_point_router.router)
app.include_router(fair_router.router)

# Vercel handler
handler = Mangum(app)
