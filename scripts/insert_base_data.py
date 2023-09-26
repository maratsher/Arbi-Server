"""
Скрипт заполнения БД основными данными.
"""
import os
import sys
import inspect

from itertools import product

from sqlalchemy.ext.asyncio import async_scoped_session
import sqlalchemy as sa

from data import coins, exchanges

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import asyncio

from app import models
from app.db.session import Session


session = async_scoped_session(Session, scopefunc=asyncio.current_task)


async def insert_coins():
    for c in coins:
        coin: models.Coin = await session.scalar(sa.select(models.Coin).where(models.Coin.ticker==c[1]))
        if coin:
            continue
        coin = models.Coin(name=c[0],ticker=c[1])
        session.add(coin)

    await session.commit()

    print('Монеты успешно добавлены!')


async def insert_exchanges():

    for e in exchanges:
        exchange: models.Exchange = await session.scalar(sa.select(models.Exchange).where(models.Exchange.name == e))
        if exchange:
            continue
        exchange = models.Exchange(name=e)
        session.add(exchange)

    await session.commit()

    print('Биржы успешно добавлены!')


async def generate_bundles():

    for coin, exchange1, exchange2 in product(coins, exchanges, exchanges):

        if exchange1 == exchange2:
            continue

        # получем id монеты по ее тикеру
        coin_id: int = (await session.scalar(
            sa.select(models.Coin.id).where(models.Coin.ticker == coin[1])
        ))

        # получем id бирж по их названиям
        exchange1_id = (await session.scalar(
            sa.select(models.Exchange.id).where(models.Exchange.name == exchange1)
        ))

        exchange2_id = (await session.scalar(
            sa.select(models.Exchange.id).where(models.Exchange.name == exchange2)
        ))

        bundle = await session.scalar(sa.select(models.Bundle).where(
            models.Bundle.coin_id == coin_id,
            sa.or_(
                sa.and_(models.Bundle.exchange1_id == exchange1_id, models.Bundle.exchange2_id == exchange2_id),
                sa.and_(models.Bundle.exchange1_id == exchange2_id, models.Bundle.exchange2_id == exchange1_id)
            )
        ))
        print(bundle)

        if bundle:
            continue

        bundle = models.Bundle(coin_id=coin_id, exchange1_id=exchange1_id, exchange2_id=exchange2_id)

        session.add(bundle)

        await session.commit()

    print("Связки успешно сгенерированы!")


async def main():
    await insert_coins()
    await insert_exchanges()
    await generate_bundles()
    await session.close()


if __name__ == '__main__':
    asyncio.run(main())
