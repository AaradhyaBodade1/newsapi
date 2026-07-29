from fastapi import APIRouter

from app.api.v1 import articles, auth, categories, credentials, dashboard, posts, prompts, settings, sources

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(sources.router)
api_router.include_router(articles.router)
api_router.include_router(prompts.router)
api_router.include_router(posts.router)
api_router.include_router(settings.router)
api_router.include_router(credentials.router)
api_router.include_router(dashboard.router)
