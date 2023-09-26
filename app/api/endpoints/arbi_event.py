"""
Модуль API user.
"""
import typing
import sqlalchemy as sa
import sqlalchemy.exc
from fastapi import Depends, APIRouter, status
from sqlalchemy.orm import joinedload


from app import schemas, models, db
from app.api import helpers, details


router = APIRouter()


@router.get("", response_model=typing.List[schemas.ArbiEventInDb])
async def read_arbi_events(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API получения арбитражных ситуаций за день
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id, load_bundles=True)

    arbi_events = (await session.scalars(sa.select(models.ArbiEvent).where(
        models.ArbiEvent.user_id == user.id,
        models.ArbiEvent.used_base_coin_id == user.base_coin_id,
        models.ArbiEvent.used_threshold == user.threshold,
        models.ArbiEvent.used_volume == user.volume,
        sa.func.date(models.ArbiEvent.start) == sa.func.date(sa.func.now()),
    ).options(
        joinedload(models.ArbiEvent.bundle).options(
            joinedload(models.Bundle.coin),
            joinedload(models.Bundle.exchange1),
            joinedload(models.Bundle.exchange2)
        ),
        joinedload(models.ArbiEvent.used_base_coin)
    ).order_by(sa.desc(models.ArbiEvent.max_profit)))).all()

    return arbi_events
