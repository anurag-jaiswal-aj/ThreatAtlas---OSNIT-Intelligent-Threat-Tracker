from fastapi import APIRouter
from app.api.ingestion import router as ingestion_router
from app.api.nlp import router as nlp_router
from app.api.v1.router import v1_router
from app.core.config import settings

api_router = APIRouter()

# Include routers
api_router.include_router(ingestion_router)
api_router.include_router(nlp_router, prefix="/nlp", tags=["NLP"])
api_router.include_router(v1_router)


@api_router.get("/health", status_code=200, tags=["Health"])
def health_check():
    """Simple health check endpoint returning server status."""
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
