from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from .routers.site import router as site_router
from .routers.verified_feedback import router as verified_feedback_router
from .config import settings

app = FastAPI(title=settings.app_name)

@app.on_event("startup")
def on_startup():
    init_db()

# CORS for frontend dev server
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(site_router)
app.include_router(verified_feedback_router)

@app.get("/")
def root():
    return {"name": settings.app_name, "status": "ok"}
