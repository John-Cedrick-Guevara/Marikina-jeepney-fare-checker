from fastapi import FastAPI

from app.route_point import router as route_point_router
from app.routes import router as routes_router

app = FastAPI(title="Job Application Manager", description="A simple job application manager API", version="1.0.0")

app.include_router(routes_router.router)
app.include_router(route_point_router.router)
