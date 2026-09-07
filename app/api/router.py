from fastapi import APIRouter
from app.api.routes import auth, clubs, health, memberships, users, watch_rooms

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(clubs.router, prefix="/clubs", tags=["clubs"])
api_router.include_router(memberships.router, tags=["memberships"])
api_router.include_router(watch_rooms.router, prefix="/watch-rooms", tags=["watch-rooms"])
