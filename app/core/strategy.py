from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.exc
from sqlalchemy.orm import joinedload, selectinload
import requests

from app import models, db
from app.core.config import base_config
from app.models import AutoState, ExchangeName, AutoStatus
from .exchange import (
    Exchange, BybitExchange, BinanceExchange,
    OrderSide, OrderStatus, OrderType,
    ExchangeInsufficientFunds
)

BASE_SYMBOL = "USDT"


def now_equal_price(bybit_profit: float, binance_profit: float, epsilon: float):
    """Check equal price"""
    if abs(bybit_profit - binance_profit) < epsilon:
        return True
    return False


def init_purchase(bybit_sym: str, binance_sym: str, bybit: BybitExchange, binance: BinanceExchange, bybit_price: float,
                  binance_price: float,
                  deposit: float, telegram_id: str):
    """Place two orders in bybit and binance to buy TARGET COIN """
    order_id_binance, order_status_binance = binance.place_order(symbol=binance_sym,
                                                                 side=OrderSide.BUY,
                                                                 order_type=OrderType.LIMIT,
                                                                 quantity=deposit,
                                                                 price=binance_price)

    order_id_bybit, order_status_bybit = bybit.place_order(symbol=bybit_sym,
                                                           side=OrderSide.BUY,
                                                           order_type=OrderType.LIMIT,
                                                           quantity=deposit,
                                                           price=bybit_price)

    if (bybit.order_status_map.get(order_status_bybit) != OrderStatus.REJECTED and
            binance.order_status_map.get(order_status_binance) != OrderStatus.REJECTED):
        return order_id_bybit, order_id_binance
    else:
        db.bot_sender.send_task('debug',
                                (telegram_id, "ERROR", f"\nОшибка при размещении ордера"))


def sell(symbol: str, quantity: float, price: float, exchange: Exchange,
         telegram_id: str):
    order_id, order_status = exchange.place_order(
        symbol=symbol,
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price
    )

    db.bot_sender.send_task('debug', (
        telegram_id, "INFO",
        f"\nРазмещен ордер на продажу <b>{quantity} {symbol}</b> на бирже {exchange.name}\n\nID оредра: <b>{order_id}</b>"))

    if exchange.order_status_map.get(order_status) != OrderStatus.REJECTED:
        return order_id
    else:
        db.bot_sender.send_task('debug',
                                (telegram_id, "ERROR", f"Ошибка при размещении ордера..."))


def buy(symbol: str, quantity: float, price: float, exchange: Exchange,
        telegram_id: str):
    order_id, order_status = exchange.place_order(
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price
    )

    db.bot_sender.send_task('debug', (
        telegram_id, "INFO",
        f"\nРазмещен ордер на покупку <b>{quantity} {symbol} </b> на бирже {exchange.name}\n ID оредра: <b> {order_id} </b>"))

    if exchange.order_status_map.get(order_status) != OrderStatus.REJECTED:
        return order_id
    else:
        db.bot_sender.send_task('debug',
                                (telegram_id, "ERROR", f"Ошибка при размещении ордера..."))


def check_sell(exchange: Exchange, ticker: str, quantity: float):
    target_balance, _ = exchange.get_balance(ticker)
    if target_balance < quantity:
        return False

    return True


def check_buy(exchange: Exchange, ticker: str, quantity: float, price: float):
    target_balance, _ = exchange.get_balance(ticker)
    if quantity > (target_balance * 1 / price):
        return False

    return True


def cancel_orders(symbol_binance, symbol_bybit, bybit, binance, order_id_binance, order_id_bybit, user_telegram_id):
    try:
        binance.cancel_order(symbol_binance, order_id_binance)
        db.bot_sender.send_task('debug', (
            user_telegram_id, "INFO", f"\nОрдер c ID: <b>{order_id_binance}</b> на бирже Binance отменен"))
    except:
        db.bot_sender.send_task('debug', (
            user_telegram_id, "INFO", f"\nОрдер на бирже Binance отсутсвует"))
    try:
        bybit.cancel_order(symbol_bybit, order_id_bybit)
        db.bot_sender.send_task('debug', (
            user_telegram_id, "INFO", f"\nОрдер c ID: <b>{order_id_bybit}</b> на бирже Bybit отменен"))
    except:
        db.bot_sender.send_task('debug', (
            user_telegram_id, "INFO", f"\nОрдер на бирже Bybit отсутсвует"))


def get_common_balance(bybit, binance, bybit_price, binance_price, target_ticker):
    usdt_balance_binance, _ = binance.get_balance(BASE_SYMBOL)
    usdt_balance_bybit, _ = bybit.get_balance(BASE_SYMBOL)
    target_balance_binance, _ = binance.get_balance(target_ticker)
    target_balance_bybit, _ = bybit.get_balance(target_ticker)

    return (usdt_balance_binance + target_balance_binance * binance_price) + (
            usdt_balance_bybit + target_balance_bybit * bybit_price)


def stop(user):
    user.current_state = AutoState.ON_STOP
    user.auto = False


async def auto_mode():
    async with db.session.Session() as session:

        users = (await session.scalars(sa.select(models.User).options(
            joinedload(models.User.target_coin),
            selectinload(models.User.user_exchanges).options(
                joinedload(models.UserExchange.exchange)
            )
        ))).all()

        for user in users:

            try:

                if user.status == AutoStatus.STOPPED or user.current_state is None:
                    continue

                if user.debug_mode:
                    db.bot_sender.send_task('debug', (user.telegram_id, "INFO",
                                                      f"\nПользователь c состоянием <b>{user.current_state.name}</b> в режиме <b>{user.status.name}</b>"))
                # Create correct symbols for user
                SYMBOL_BYBIT = BybitExchange.make_symbol(user.target_coin.ticker, BASE_SYMBOL)
                SYMBOL_BINANCE = BinanceExchange.make_symbol(user.target_coin.ticker, BASE_SYMBOL)

                # Init bybit and binance exchange
                bybit, binance = None, None
                for user_exchange in user.user_exchanges:
                    try:
                        if user_exchange.exchange.name == ExchangeName.BYBIT:
                            bybit = BybitExchange(
                                api_key=user_exchange.api_key,
                                api_secret=user_exchange.api_secret,
                                test=base_config.TEST_API
                            )
                        if user_exchange.exchange.name == ExchangeName.BINANCE:
                            binance = BinanceExchange(
                                api_key=user_exchange.api_key,
                                api_secret=user_exchange.api_secret,
                                test=base_config.TEST_API
                            )
                    except Exception as e:
                        db.bot_sender.send_task('debug',
                                                (user.telegram_id, "ERROR", f"Ошибка при подключении к бирже: {e}"))

                if bybit and binance:

                    # connect to db
                    bybit.connect()
                    binance.connect()

                    # get current price from exchanges
                    try:
                        bybit_price = bybit.get_price(symbol=SYMBOL_BYBIT)
                        binance_price = binance.get_price(symbol=SYMBOL_BINANCE)
                        if user.debug_mode:
                            db.bot_sender.send_task('debug', (user.telegram_id, "INFO",
                                                              f"\nЦена на binance: <b>{binance_price} {BASE_SYMBOL}</b>\nЦена на Bybit: <b>{bybit_price} {BASE_SYMBOL}</b>\nПотенциальный профит <b>{abs(binance_price * user.volume - bybit_price * user.volume)}</b>"))
                    except Exception as e:
                        db.bot_sender.send_task('debug', (user.telegram_id, "WARNING", f"Cant get price. Reconnect..."))
                        continue

                    # stopping auto trade
                    if user.current_state == AutoState.ON_STOP:
                        cancel_orders(SYMBOL_BINANCE, SYMBOL_BYBIT, bybit, binance, user.order_id_binance,
                                      user.order_id_bybit, user.telegram_id)
                        db.bot_sender.send_task('stop_auto', (user.telegram_id,))
                        user.status = AutoStatus.STOPPED
                    # initial process
                    elif user.current_state == AutoState.INITIAL and now_equal_price(bybit_price, binance_price,
                                                                                     user.epsilon):

                        order_id_bybit, order_id_binance = init_purchase(SYMBOL_BYBIT, SYMBOL_BINANCE, bybit, binance,
                                                                         bybit_price, binance_price,
                                                                         user.init_volume, user.telegram_id)
                        user.current_state = AutoState.WAIT_FILLED
                        user.order_id_bybit = order_id_bybit
                        user.order_id_binance = order_id_binance
                        user.order_time_bybit = datetime.now()
                        user.order_time_binance = datetime.now()
                        user.status = AutoStatus.STARTED
                        db.bot_sender.send_task('debug', (user.telegram_id, "INFO",
                                                          f"\nЗавершена стартавая закупка\nРазмещены ордеры на покупку <b>{user.volume} {user.target_coin.ticker}</b> на биржак bybit и bibnance.\nID ордера Binance <b>{order_id_binance}</b>\nID ордера на Bybit: <b>{order_id_bybit}</b>\n"))

                    elif user.current_state == AutoState.WAIT_FILLED:

                        bybit_status = bybit.check_order(symbol=SYMBOL_BYBIT, order_id=user.order_id_bybit)
                        binance_status = binance.check_order(symbol=SYMBOL_BINANCE, order_id=user.order_id_binance)

                        if user.debug_mode:
                            db.bot_sender.send_task('debug', (user.telegram_id, "INFO",
                                                              f"\nОжидание исполнения ордеров\nТекущие статусы: \nСтатус ордера на Binance: <b>{binance_status}</b>\nСтатус ордера на Bybit: <b>{bybit_status}</b>"))

                        if (bybit_status == OrderStatus.FILLED and
                                binance_status == OrderStatus.FILLED):
                            user.current_state = AutoState.IN_PROGRESS
                            user.order_id_bybit = None
                            user.order_id_binance = None

                            if user.debug_mode:
                                db.bot_sender.send_task('debug', (user.telegram_id, "INFO",
                                                                  f"\n🎉Оба ордера успешно выполнились!🎉"))
                            if user.status == AutoStatus.STARTED:
                                user.profit = get_common_balance(bybit, binance, bybit_price, binance_price,
                                                                 user.target_coin.ticker)

                                if user.debug_mode:
                                    db.bot_sender.send_task('debug', (user.telegram_id, "INFO",
                                                                      f"\nОбщий баланс на момент старта алгоритма равен: <b>{user.profit} {BASE_SYMBOL}</b>"))
                            elif user.status == AutoStatus.PLAY:
                                profit = get_common_balance(bybit, binance, bybit_price, binance_price,
                                                            user.target_coin.ticker) - user.profit

                                db.bot_sender.send_task('profit', (user.telegram_id, f"{profit} {BASE_SYMBOL}"))


                        else:
                            if ((datetime.now() - user.order_time_bybit).seconds // 60 > user.wait_order_minutes) or (
                                    (datetime.now() - user.order_time_binance).seconds // 60 > user.wait_order_minutes):

                                if user.status == AutoStatus.STARTED:
                                    # db.bot_sender.send_task('debug',
                                    #                         (user.telegram_id, "WARNING", f"Не получилось совершить стартовую закупку"))
                                    # user.current_state = AutoState.INITIAL
                                    pass
                                elif user.status == AutoStatus.PLAY:
                                    cancel_orders(SYMBOL_BINANCE, SYMBOL_BYBIT, bybit, binance, user.order_id_binance,
                                                  user.order_id_bybit, user.telegram_id)
                                    user.current_state = AutoState.IN_PROGRESS
                                    db.bot_sender.send_task('orders_canceled', (user.telegram_id,))

                    # an arbitration situation occurred
                    elif (user.current_state == AutoState.IN_PROGRESS) \
                            and (abs(user.volume * bybit_price - user.volume * binance_price) >= user.threshold):

                        if user.debug_mode:
                            db.bot_sender.send_task('debug', (user.telegram_id, "INFO",
                                                              f"\nПроизошла арбитражная ситуация:\nЦена на Bybit: <b>{bybit_price} {BASE_SYMBOL} </b> \nЦена на Binance <b>{binance_price} {user.target_coin.ticker}</b>\nПотенциальный профит <b>{abs(user.volume * bybit_price - user.volume * binance_price)} {BASE_SYMBOL}</b>"))

                        user.status = AutoStatus.PLAY

                        # bybit > binance
                        if bybit_price >= binance_price:
                            try:
                                if check_sell(bybit, user.target_coin.ticker, user.volume) and check_buy(
                                        binance, BASE_SYMBOL, user.volume, binance_price):

                                    order_id_bybit = sell(SYMBOL_BYBIT, user.volume,
                                                          bybit_price,
                                                          bybit,
                                                          user.telegram_id)

                                    order_id_binance = buy(SYMBOL_BINANCE, user.volume, binance_price, binance,
                                                           user.telegram_id)

                                    user.current_state = AutoState.WAIT_FILLED
                                    user.order_id_bybit = order_id_bybit
                                    user.order_id_binance = order_id_binance
                                    user.order_time_bybit = datetime.now()
                                    user.order_time_binance = datetime.now()
                                else:
                                    raise ExchangeInsufficientFunds()
                            except ExchangeInsufficientFunds:
                                db.bot_sender.send_task('need_transfer', (user.telegram_id,))


                        # binance > bybit
                        else:
                            try:
                                if check_sell(binance, user.target_coin.ticker, user.volume) and check_buy(
                                        bybit, BASE_SYMBOL, user.volume, bybit_price):

                                    order_id_binance = sell(SYMBOL_BINANCE, user.volume,
                                                            binance_price,
                                                            binance,
                                                            user.telegram_id)
                                    order_id_bybit = buy(SYMBOL_BYBIT, user.volume, bybit_price, bybit,
                                                         user.telegram_id)

                                    user.current_state = AutoState.WAIT_FILLED
                                    user.order_id_bybit = order_id_bybit
                                    user.order_id_binance = order_id_binance
                                    user.order_time_bybit = datetime.now()
                                    user.order_time_binance = datetime.now()
                                else:
                                    raise ExchangeInsufficientFunds()


                            except ExchangeInsufficientFunds:
                                db.bot_sender.send_task('need_transfer', (user.telegram_id,))

            except requests.exceptions.ProxyError:
                db.bot_sender.send_task('debug',
                                        (user.telegram_id, "WARNING", f"\nReconnect..."))
                
            except requests.exceptions.HTTPError:
                db.bot_sender.send_task('debug',
                                        (user.telegram_id, "WARNING", f"\nReconnect..."))

            except Exception as e:
                db.bot_sender.send_task('debug',
                                        (user.telegram_id, "ERROR", f"\nCritical error {e}"))

                # stop auto mode
                stop(user)

            try:
                await session.commit()
            except sa.exc.DBAPIError as e:
                db.bot_sender.send_task('debug',
                                        (user.telegram_id, "ERROR", f"\nError {e}"))

                await session.rollback()
