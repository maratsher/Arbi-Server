"""
Модуль API coins.
"""
import typing
import sqlalchemy as sa
from fastapi import Depends, APIRouter

from app import schemas, models, db


router = APIRouter()


@router.get("", response_model=typing.List[schemas.CoinInDb])
async def read_coins(session: db.AsyncSession = Depends(db.get_session)):
    """
    API получения всех монет.
    """
    coins = (await session.scalars(sa.select(models.Coin))).all()

    return coins
