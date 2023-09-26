"""
Модуль модели настроек пользователя
"""
from enum import Enum

import sqlalchemy as sa

from app import db


class ExchangeName(str, Enum):
    """Список констант для Exchange.name"""
    BINANCE = 'Binance'
    BYBIT = 'Bybit'

    @classmethod
    def to_dict(cls):
        return {e.name: e.value for e in cls}


class Exchange(db.Base):
    """Модель таблицы бирж.

    :id: Уникальный идентификатор биржы.

    :exchange_name: Имя биржы
    """
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)

    name = sa.Column(sa.Enum(ExchangeName), nullable=True)

    def __repr__(self):
        return f'Exchange id: {self.id}, Exchange name: {self.exchange_name}'
