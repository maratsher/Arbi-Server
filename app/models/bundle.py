"""
Модуль модели связки
"""
import typing

import sqlalchemy as sa
import sqlalchemy.orm

from app import db


if typing.TYPE_CHECKING:
    from .coin import Coin
    from .exchange import Exchange


class Bundle(db.Base):
    """Модель таблицы связок.

    :id: Уникальный идентификатор связки.

    :coin_id: Отслеживаемая монета
    :bundle_holds: Список позиций для это связки

    """
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)

    coin_id = sa.Column(sa.Integer, sa.ForeignKey('coin.id'), nullable=False)
    exchange1_id = sa.Column(sa.Integer, sa.ForeignKey('exchange.id'), nullable=False)
    exchange2_id = sa.Column(sa.Integer, sa.ForeignKey('exchange.id'), nullable=False)

    exchange1: "Exchange" = sa.orm.relationship(
        'Exchange',
        foreign_keys=[exchange1_id],
        lazy='raise_on_sql',
        viewonly=True,
        uselist=False
    )
    exchange2: "Exchange" = sa.orm.relationship(
        'Exchange',
        foreign_keys=[exchange2_id],
        lazy='raise_on_sql',
        viewonly=True,
        uselist=False
    )

    coin: "Coin" = sa.orm.relationship(
        'Coin',
        lazy='raise_on_sql',
        viewonly=True,
        uselist=False
    )

    def __repr__(self):
        return f'Bundle id: {self.id}, coin id: {self.coin_id}, exc1: {self.exchange1_id} exc2: {self.exchange2_id}'
