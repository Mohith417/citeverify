from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import models  # noqa: F401  (registers tables)
from .api import analysis, claims, references, reports, upload
from .config import settings
from .database import Base, engine
from .services import llm

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="CiteVerify API",
    version="1.0.0",
    description="Scientific claim and citation verification with evidence-backed verdicts.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(claims.router)
app.include_router(references.router)
app.include_router(reports.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": app.version,
        "ai_provider": llm.provider_label(),
        "ai_configured": llm.is_available(),
        "providers": {
            "semantic_scholar": settings.enable_semantic_scholar,
            "arxiv": settings.enable_arxiv,
            "unpaywall": bool(settings.unpaywall_email),
            "europe_pmc": True,
            "openalex": True,
            "crossref": True,
        },
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):  # pragma: no cover
    logging.getLogger(__name__).exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
