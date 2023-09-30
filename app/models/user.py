"""
Модуль модели пользователя.
"""
import typing
from enum import IntEnum

import sqlalchemy as sa
import sqlalchemy.orm

from app import db

if typing.TYPE_CHECKING:
    from .coin import Coin
    from .bundle import Bundle
    from .exchange import Exchange


class AutoState(IntEnum):
    """Список констант для User.current_state"""
    INITIAL = 1
    WAIT_FILLED = 2
    IN_PROGRESS = 3
    ON_STOP = 4
    STOP = 5
    @classmethod
    def to_dict(cls):
        return {e.name: e.value for e in cls}


class AutoStatus(IntEnum):
    """Список констант для `User.status`"""
    STARTED = 1
    PLAY = 2
    STOPPED = 3

    @classmethod
    def to_dict(cls):
        return {e.name: e.value for e in cls}


class User(db.Base):
    """Модель таблицы пользователей.

    :id: Уникальный идентификатор пользователя.

    :telegram_id: Идентификатор telegram.

    :target_coin_id: Целевая монета.

    :threshold: Порог для определения арбитражной ситуации.
    :init_volume: Объем стартовой закупки.
    :volume: Объем торгов.
    :epsilon: Погрешность при сравнении цен.
    :wait_order_minutes: Время ожидания ордера.

    :auto: Автоматическая торговля.
    :current_state: Текущее состояние автоматической торговли.

    :profit: Профит.

    :debug_mode: Режим отладки.

    :order_id_binance: Идентификатор ордера на Binance.
    :order_id_bybit: Идентификатор ордера на Bybit.

    :order_time_binance: Время размещения ордера на Binance.
    :order_time_bybit: Время размещения ордера на Bybit.

    :executed_binance: Выполненная сумма ордера на Binance.
    :executed_bybit: Выполненная сумма ордера на Bybit.

    :created: Дата и время создания пользователя.
    """
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)

    telegram_id = sa.Column(sa.String, nullable=False, unique=True)

    target_coin_id = sa.Column(sa.Integer, sa.ForeignKey('coin.id'), nullable=False, default=2)

    threshold = sa.Column(sa.Float, nullable=False, default=4)
    init_volume = sa.Column(sa.Float, nullable=False, default=1000)
    volume = sa.Column(sa.Float, nullable=False, default=50)
    epsilon = sa.Column(sa.Float, nullable=False, default=0.1)
    wait_order_minutes = sa.Column(sa.Float, nullable=False, default=60)

    auto = sa.Column(sa.Boolean, nullable=False, default=False)
    current_state = sa.Column(sa.Enum(AutoState), nullable=True)

    profit = sa.Column(sa.Float, nullable=False, default=0)

    debug_mode = sa.Column(sa.Boolean, nullable=False, default=False)

    order_id_binance = sa.Column(sa.String, nullable=True)
    order_id_bybit = sa.Column(sa.String, nullable=True)

    order_time_binance = sa.Column(sa.DateTime, nullable=True)
    order_time_bybit = sa.Column(sa.DateTime, nullable=True)

    executed_binance = sa.Column(sa.Float, nullable=True)
    executed_bybit = sa.Column(sa.Float, nullable=True)

    status = sa.Column(sa.Enum(AutoStatus), nullable=True)

    created = sa.Column(sa.DateTime, nullable=False, default=sa.func.now())

    target_coin: "Coin" = sa.orm.relationship(
        'Coin',
        lazy='raise_on_sql',
        foreign_keys=[target_coin_id],
        viewonly=True,
        uselist=False
    )

    bundles: typing.List["Bundle"] = sa.orm.relationship(
        'Bundle',
        lazy='raise_on_sql',
        viewonly=True,
        uselist=True,
        secondary="join(UserBundle, Bundle, UserBundle.bundle_id == Bundle.id)",
        secondaryjoin="Bundle.id == UserBundle.bundle_id"
    )

    user_exchanges: typing.List["UserExchange"] = sa.orm.relationship(
        'UserExchange',
        lazy='raise_on_sql',
        viewonly=True,
        uselist=True
    )

    bundles_ids = property(lambda self: [bundle.id for bundle in self.bundles] if self.bundles else [])

    exchanges = property(
        lambda self: [user_exchange.exchange for user_exchange in self.user_exchanges] if self.user_exchanges else []
    )

    def __str__(self):
        return f'User #{self.id}'

    def __repr__(self):
        return f'User #{self.id}'


class UserBundle(db.Base):
    """Модель таблицы отслеживаемых связок пользователя.

    :user_id: Уникальный идентификатор пользователя.
    :bundle_id: Уникальный идентификатор связки.

    """
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), primary_key=True, nullable=False)
    bundle_id = sa.Column(sa.Integer, sa.ForeignKey('bundle.id'), primary_key=True, nullable=False)

    user: "User" = sa.orm.relationship('User', lazy='raise_on_sql', uselist=False)
    bundle: "Bundle" = sa.orm.relationship('Bundle', lazy='raise_on_sql', uselist=False)

    def __repr__(self):
        return f'User id: {self.user_id}, Bundle id: {self.bundle_id}'


class UserExchange(db.Base):
    """Модель таблицы данных бирж пользователя.

    :user_id: Уникальный идентификатор пользователя.
    :exchange_id: Уникальный идентификатор биржи.

    :api_token: API-токен пользователя для биржи.
    """
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), primary_key=True, nullable=False)
    exchange_id = sa.Column(sa.Integer, sa.ForeignKey('exchange.id'), primary_key=True, nullable=False)

    api_key = sa.Column(sa.String, nullable=False)
    api_secret = sa.Column(sa.String, nullable=False)

    user: "User" = sa.orm.relationship('User', lazy='raise_on_sql', uselist=False)
    exchange: "Exchange" = sa.orm.relationship('Exchange', lazy='raise_on_sql', uselist=False)

    def __repr__(self):
        return f'User id: {self.user_id}, Exchange id: {self.exchange_id}'
