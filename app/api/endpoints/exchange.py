"""
Модуль API exchange.
"""
import typing
import sqlalchemy as sa
from fastapi import Depends, APIRouter

from app import schemas, models, db


router = APIRouter()


@router.get("/{exchange_id}", response_model=schemas.ExchangeInDb)
async def read_exchange(exchange_id: int, session: db.AsyncSession = Depends(db.get_session)):
    """
    API получения всех бирж.
    """
    exchange = await session.scalar(sa.select(models.Exchange).where(models.Exchange.id == exchange_id))

    return exchange


@router.get("", response_model=typing.List[schemas.ExchangeInDb])
async def read_exchanges(session: db.AsyncSession = Depends(db.get_session)):
    """
    API получения всех бирж.
    """
    exchanges = (await session.scalars(sa.select(models.Exchange))).all()

    return exchanges
