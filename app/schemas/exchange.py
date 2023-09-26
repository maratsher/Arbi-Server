"""
Модуль схем бирж.
"""
from app.schemas.base import APIBase
from app.models import ExchangeName


class ExchangeInDb(APIBase):
    id: int

    name: ExchangeName
