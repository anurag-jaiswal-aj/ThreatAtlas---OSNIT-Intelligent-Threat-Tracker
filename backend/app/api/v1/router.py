from fastapi import APIRouter
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.raw_posts import router as raw_posts_router
from app.api.v1.endpoints.intelligence import router as intelligence_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.websockets import router as websockets_router
from app.api.v1.endpoints.webhooks import router as webhooks_router

v1_router = APIRouter()

v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
v1_router.include_router(events_router, prefix="/events", tags=["Events"])
v1_router.include_router(raw_posts_router, prefix="/raw-posts", tags=["Raw Posts"])
v1_router.include_router(intelligence_router, prefix="/intelligence", tags=["Intelligence"])
v1_router.include_router(websockets_router, prefix="/ws", tags=["WebSockets"])
v1_router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
