"""
Модуль API bundles.
"""
import typing
import sqlalchemy as sa
from fastapi import Depends, APIRouter, Query
from sqlalchemy.orm import joinedload

from app import schemas, models, db
from app.core.config import db_config


router = APIRouter()


@router.get("", response_model=typing.List[schemas.BundleInDb])
async def read_bundles(
        coin_id: int | None = Query(None, ge=1, le=db_config.MAX_LEN_ID),
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API получения всех связок
    """
    bundles_query = sa.select(models.Bundle).options(
        joinedload(models.Bundle.coin),
        joinedload(models.Bundle.exchange1),
        joinedload(models.Bundle.exchange2)
    )

    if coin_id:
        bundles_query = bundles_query.where(models.Bundle.coin_id == coin_id)

    bundles = (await session.scalars(bundles_query)).all()

    return bundles
