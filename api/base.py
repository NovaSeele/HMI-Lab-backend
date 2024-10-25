from fastapi import APIRouter
from .routes.hand_sign import router as hand_sign_router
from .routes.user import router as user_router

api_router = APIRouter()
api_router.include_router(hand_sign_router, tags=["hand_sign"])
api_router.include_router(user_router, tags=["user"])

