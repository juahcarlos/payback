from fastapi import APIRouter

from app.api.v1 import system
from app.api.v1.admin import servers
from app.api.v1.vpn import buy, recovery
from app.api.v1.vpn.payment import cryptomus, payment


api_router = APIRouter()


api_router.include_router(recovery.router)
api_router.include_router(buy.router)
api_router.include_router(buy.router_lang)
api_router.include_router(payment.router)
api_router.include_router(payment.router_lang)
api_router.include_router(system.router)
api_router.include_router(cryptomus.router)
api_router.include_router(cryptomus.router_lang)
api_router.include_router(servers.router)
