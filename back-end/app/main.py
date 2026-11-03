from fastapi import FastAPI

from sqlalchemy.orm import DeclarativeBase
from app.db.database import engine
from app.routes import router

class Base(DeclarativeBase):
    pass

Base.metadata.create_all(bind=engine) 

app = FastAPI(title="Job Application Manager", description="A simple job application manager API", version="1.0.0")

app.include_router(router.router)