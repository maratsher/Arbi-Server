import logging
import json
import sqlalchemy as sa
import sqlalchemy.exc
from sqlalchemy.orm import joinedload, selectinload
from fastapi import status

from app import models, db
from app.api import helpers
from app.core.exchanges_api import get_price


# logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


async def update_arbi_situations():
    async with db.session.Session() as session:
        try:
            users = (await session.scalars(sa.select(models.User).options(
                joinedload(models.User.base_coin),
                selectinload(models.User.bundles)
            ))).all()
            bundles = (await session.scalars(sa.select(models.Bundle).options(
                joinedload(models.Bundle.coin),
                joinedload(models.Bundle.exchange1),
                joinedload(models.Bundle.exchange2),
            ))).all()

            is_changed = False

            for user in users:
                for bundle in bundles:
                    if user.base_coin.ticker == bundle.coin.ticker:
                        continue

                    price1 = get_price(
                        coin_ticker=bundle.coin.ticker,
                        exchange_name=bundle.exchange1.name,
                        base_coin=user.base_coin.ticker,
                    )

                    price2 = get_price(
                        coin_ticker=bundle.coin.ticker,
                        exchange_name=bundle.exchange2.name,
                        base_coin=user.base_coin.ticker,
                    )

                    arbi_event_open = (await session.scalar(sa.select(models.ArbiEvent).where(
                        models.ArbiEvent.user_id == user.id,
                        models.ArbiEvent.bundle_id == bundle.id,
                        models.ArbiEvent.end == None
                    )))

                    profit = (abs(price1 - price2)*user.volume)
                    if profit > user.threshold:
                        if arbi_event_open:
                            if (arbi_event_open.current_price1 - arbi_event_open.current_price2)*(price1 - price2) > 0:
                                if arbi_event_open.min_profit > profit:
                                    arbi_event_open.min_profit = profit
                                elif arbi_event_open.max_profit <= profit:
                                    arbi_event_open.max_profit = profit
                            else:
                                arbi_event_open.end = sa.func.now()
                                new_arbi_event = models.ArbiEvent(
                                    start=sa.func.now(),
                                    bundle_id=bundle.id,
                                    user_id=user.id,
                                    min_profit=profit,
                                    max_profit=profit,
                                    current_price1=price1,
                                    current_price2=price2,
                                    used_base_coin_id=user.base_coin_id,
                                    used_threshold=user.threshold,
                                    used_volume=user.volume
                                )
                                session.add(new_arbi_event)

                                if bundle.id in user.bundles_ids:
                                    data = {
                                        "ticker": bundle.coin.ticker,
                                        "exchange1": bundle.exchange1.name,
                                        "exchange2": bundle.exchange2.name,
                                        "current_price1": price1,
                                        "current_price2": price2,
                                        "profit": profit,
                                        "base_coin_ticker": user.base_coin.ticker
                                    }
                                    db.bot_sender.send_task('new_event', ([user.telegram_id], json.dumps(data)))

                        else:
                            new_arbi_event = models.ArbiEvent(
                                start=sa.func.now(),
                                bundle_id=bundle.id,
                                user_id=user.id,
                                min_profit=profit,
                                max_profit=profit,
                                current_price1=price1,
                                current_price2=price2,
                                used_base_coin_id=user.base_coin_id,
                                used_threshold=user.threshold,
                                used_volume=user.volume
                            )
                            session.add(new_arbi_event)

                            if bundle.id in user.bundles_ids:
                                data = {
                                    "ticker": bundle.coin.ticker,
                                    "exchange1": bundle.exchange1.name,
                                    "exchange2": bundle.exchange2.name,
                                    "current_price1": price1,
                                    "current_price2": price2,
                                    "profit": profit,
                                    "base_coin_ticker": user.base_coin.ticker
                                }
                                db.bot_sender.send_task('new_event', ([user.telegram_id], json.dumps(data)))

                        is_changed = True
                    else:
                        if arbi_event_open:
                            arbi_event_open.end = sa.func.now()
                            is_changed = True
                        else:
                            continue

            try:
                if is_changed:
                    await session.commit()
            except sa.exc.DBAPIError as e:
                await session.rollback()

                helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))
        except Exception as e:
            pass
