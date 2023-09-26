"""
Модуль схем связок.
"""
from app.schemas.base import APIBase
from app.schemas.coin import CoinInDb
from app.schemas.exchange import ExchangeInDb


class BundleInDb(APIBase):
    id: int

    coin: CoinInDb
    exchange1: ExchangeInDb
    exchange2: ExchangeInDb




