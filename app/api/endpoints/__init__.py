"""
Модуль импорта маршрутов API.
"""
from fastapi import APIRouter

from app.api.endpoints import (
    ping, user, bundle,
    coin, exchange, arbi_event
)


api_router = APIRouter(prefix='/api')

api_router.include_router(ping.router, prefix="/ping", tags=["ping"])
api_router.include_router(user.router, prefix="/users", tags=["user"])
api_router.include_router(coin.router, prefix="/coins", tags=["coin"])
api_router.include_router(exchange.router, prefix="/exchanges", tags=["exchange"])
api_router.include_router(bundle.router, prefix="/bundles", tags=["bundle"])
api_router.include_router(arbi_event.router, prefix="/arbi", tags=["arbi_event"])
