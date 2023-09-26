"""
Модуль схем монеты.
"""
from pydantic import Field, validator

from app.api import details
from app.core import security
from app.schemas.base import APIBase
from app.core.config import db_config


class CoinInDb(APIBase):
    id: int

    name: str
    ticker: str
