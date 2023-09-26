"""
Модуль модели настроек пользователя
"""
import sqlalchemy as sa
import sqlalchemy.orm

from app import db
from app.core.config import db_config


class Coin(db.Base):
    """Модель таблицы монет.

    :id: Уникальный идентификатор монеты.

    :coin_name: Имя монеты
    """
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)

    name = sa.Column(sa.String(50), nullable=False, unique=True)
    ticker = sa.Column(sa.String(10), nullable=False, unique=True)

    def __repr__(self):
        return f'Coin id: {self.id}, Coin name: {self.coin_name}, Coin ticker: {self.coin_ticker}'
