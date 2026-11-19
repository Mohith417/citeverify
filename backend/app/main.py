from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (registers tables)
from .api import analysis, upload
from .config import settings
from .database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="CiteVerify API", version="0.3.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(upload.router)
app.include_router(analysis.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "ai_provider": settings.ai_provider,
        "gemini_configured": bool(settings.gemini_api_key and settings.gemini_model),
    }
