"""
Модуль схем арбитражной ситуации.
"""
from datetime import datetime

from app.schemas.base import APIBase
from app.schemas.bundle import BundleInDb
from app.schemas.coin import CoinInDb


class ArbiEventInDb(APIBase):
    id: int

    start: datetime
    end: datetime | None

    bundle: BundleInDb

    min_profit: float
    max_profit: float
    current_price1: float
    current_price2: float
    used_base_coin: CoinInDb
    used_threshold: float
    used_volume: float
