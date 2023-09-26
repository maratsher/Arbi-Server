"""
Модуль модели арбитражной ситуации
"""
import typing

import sqlalchemy as sa
import sqlalchemy.orm

from app import db


if typing.TYPE_CHECKING:
    from .bundle import Bundle
    from .user import User
    from .coin import Coin


class ArbiEvent(db.Base):
    """Модель арбитражной ситуации

    :id: Уникальный идентификатор арбитражной ситуации.

    :bundle_id: Отслеживаемая связка
    :min_profit: Минимальная прибыль
    :max_profit: Максимальная прибыль

    """
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)

    start = sa.Column(sa.DateTime, nullable=False, default=sa.func.now())
    end = sa.Column(sa.DateTime, nullable=True)

    bundle_id = sa.Column(sa.Integer, sa.ForeignKey('bundle.id'), nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    min_profit = sa.Column(sa.Float, nullable=False)
    max_profit = sa.Column(sa.Float, nullable=False)
    current_price1 = sa.Column(sa.Float, nullable=False)
    current_price2 = sa.Column(sa.Float, nullable=False)

    used_base_coin_id = sa.Column(sa.Integer, sa.ForeignKey('coin.id'), nullable=True)
    used_threshold = sa.Column(sa.Float, nullable=False)
    used_volume = sa.Column(sa.Float, nullable=False)

    bundle: "Bundle" = sa.orm.relationship(
        'Bundle',
        lazy='raise_on_sql',
        viewonly=True,
        uselist=False
    )

    user: "User" = sa.orm.relationship(
        'User',
        lazy='raise_on_sql',
        viewonly=True,
        uselist=False
    )

    used_base_coin: "Coin" = sa.orm.relationship(
        'Coin',
        lazy='raise_on_sql',
        viewonly=True,
        uselist=False
    )

    def __repr__(self):
        return f'Bundle id: {self.bundle_id}, User id {self.user_id}'

