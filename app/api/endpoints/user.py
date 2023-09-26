"""
Модуль API user.
"""
import typing
import sqlalchemy as sa
import sqlalchemy.exc
from sqlalchemy.orm import joinedload
from fastapi import Depends, APIRouter, status

from app import schemas, models, db
from app.api import helpers, details


router = APIRouter()


@router.post("", response_model=int)
async def create_user(
        data: schemas.UserCreate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API создания пользователя.
    """
    user_exists = await session.scalar(sa.select(sa.select(models.User).where(
        models.User.telegram_id == data.telegram_id
    ).exists()))
    if user_exists:
        helpers.abort(code=status.HTTP_400_BAD_REQUEST, detail=details.USER_ALREADY_EXISTS)

    user = models.User(telegram_id=data.telegram_id)
    session.add(user)
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return user.id


@router.post("/{telegram_id}/bundle", response_model=schemas.Status)
async def add_user_bundle(
        telegram_id: str,
        data: schemas.UserBundleAdd,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API добавления отлеживаемой связки пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id)
    try:
        session.add(models.UserBundle(user_id=user.id, bundle_id=data.bundle_id))
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.get("/{telegram_id}", response_model=schemas.UserInDb)
async def read_user(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API получения списка всех пользователей
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id, load_base_coin=True, load_target_coin=True)

    return user


@router.get("", response_model=typing.List[schemas.UserInDb])
async def read_users(session: db.AsyncSession = Depends(db.get_session)):
    """
    API получения списка всех пользователей
    """
    users = (await session.scalars(sa.select(models.User).options(
        joinedload(models.User.base_coin),
        joinedload(models.User.target_coin)
    ))).all()

    return users


@router.get("/{telegram_id}/base_coin_id", response_model=schemas.CoinInDb)
async def read_user_base_coin_id(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session) # noqa
):
    """
    API получения базовой монеты пользовтеля.
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id, load_base_coin=True)

    return user.base_coin


@router.get("/{telegram_id}/target_coin_id", response_model=schemas.CoinInDb)
async def read_user_target_coin_id(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session) # noqa
):
    """
    API получения целевой монеты пользовтеля.
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id, load_target_coin=True)

    return user.target_coin


@router.get("/{telegram_id}/volume", response_model=float)
async def read_user_volume(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)  # noqa
):
    """
    API получения порога пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id)

    return user.volume


@router.get("/{telegram_id}/threshold", response_model=float)
async def read_user_threshold(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)  # noqa
):
    """
    API получения порога пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id)

    return user.threshold


@router.get("/{telegram_id}/epsilon", response_model=float)
async def read_user_epsilon(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)  # noqa
):
    """
    API получения погрешности сравнения цен пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id)

    return user.epsilon


@router.get("/{telegram_id}/difference", response_model=float)
async def read_user_difference(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)  # noqa
):
    """
    API получения максимально допустимого процента различия балансов пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id)

    return user.difference


@router.get("/{telegram_id}/auto", response_model=bool)
async def read_user_auto(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)  # noqa
):
    """
    API получения автоматической торговли пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id)

    return user.auto


@router.get("/{telegram_id}/wait_order_minutes", response_model=bool)
async def read_user_wait_order_minutes(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)  # noqa
):
    """
    API получения времени на выполнение ордера пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id)

    return user.wait_order_minutes


@router.get("/{telegram_id}/test_api", response_model=bool)
async def read_user_test_api(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)  # noqa
):
    """
    API получения использования тестового режима автоматической торговли пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id)

    return user.test_api


@router.get("/{telegram_id}/bundles", response_model=typing.List[schemas.BundleInDb])
async def read_user_bundles(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)  # noqa
):
    """
    API получения отслеживаемых связок пользователя.
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id, load_bundles=True)

    return user.bundles


@router.get("/{telegram_id}/arbi_events", response_model=typing.List[schemas.ArbiEventInDb])
async def read_arbi_events(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)  # noqa
):
    """
    API получения арбитражных ситуаций пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id, load_bundles=True)

    arbi_events = (await session.scalars(sa.select(models.ArbiEvent).where(
        models.ArbiEvent.user_id == user.id,
        models.ArbiEvent.used_base_coin_id == user.base_coin_id,
        models.ArbiEvent.used_threshold == user.threshold,
        models.ArbiEvent.used_volume == user.volume,
        sa.func.date(models.ArbiEvent.start) == sa.func.date(sa.func.now()),
        models.ArbiEvent.bundle_id.in_(user.bundles_ids)
    ).options(
        joinedload(models.ArbiEvent.bundle).options(
            joinedload(models.Bundle.coin),
            joinedload(models.Bundle.exchange1),
            joinedload(models.Bundle.exchange2)
        ),
        joinedload(models.ArbiEvent.used_base_coin)
    ).order_by(sa.desc(models.ArbiEvent.max_profit)).limit(5))).all()

    return arbi_events


@router.get("/{telegram_id}/exchanges", response_model=typing.List[schemas.ExchangeInDb])
async def read_user_exchanges(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)  # noqa
):
    """
    API получения арбитражных ситуаций пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id, load_exchanges=True)

    return user.exchanges


@router.put("/auto_state", response_model=schemas.Status)
async def update_user_auto_state(
        data: schemas.UserAutoStateUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API изменения текущего состояния торговли пользователя.
    """
    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)

    user.current_state = data.state
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.put("/exchange", response_model=schemas.Status)
async def update_user_exchanges(
        data: schemas.UserExchangeUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки данных биржи пользователя.
    """
    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)

    user_exchange = await session.scalar(sa.select(models.UserExchange).where(
        models.UserExchange.user_id == user.id,
        models.UserExchange.exchange_id == data.exchange_id
    ))
    if user_exchange:
        user_exchange.api_key = data.api_key
        user_exchange.api_secret = data.api_secret
    else:
        session.add(models.UserExchange(
            user_id=user.id,
            exchange_id=data.exchange_id,
            api_key=data.api_key,
            api_secret=data.api_secret
        ))
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.put("/base_coin_id", response_model=schemas.Status)
async def update_user_base_coin_id(
        data: schemas.UserBaseCoinUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки базовой монеты пользователя.
    """
    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)

    user.base_coin_id = data.base_coin_id
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.put("/target_coin_id", response_model=schemas.Status)
async def update_user_target_coin_id(
        data: schemas.UserTargetCoinUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки целевая монеты пользователя.
    """
    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)

    user.target_coin_id = data.target_coin_id
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.put("/threshold", response_model=schemas.Status)
async def update_user_threshold(
        data: schemas.UserThresholdUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки порога пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)

    user.threshold = data.threshold
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.put("/volume", response_model=schemas.Status)
async def update_user_volume(
        data: schemas.UserVolumeUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки объема торгов пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)

    user.volume = data.volume
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.put("/epsilon", response_model=schemas.Status)
async def update_user_epsilon(
        data: schemas.UserEpsilonUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки погрешности сравнения цен пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)

    user.epsilon = data.epsilon
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.put("/difference", response_model=schemas.Status)
async def update_user_difference(
        data: schemas.UserDifferenceUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки максимально допустимого процента различия балансов пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)

    user.difference = data.difference
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.put("/auto", response_model=schemas.Status)
async def update_user_auto(
        data: schemas.UserAutoUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки автоматической торговли пользователя
    """
    send_stop_message = False

    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)
    if user.auto:
        send_stop_message = True
        user.current_state = models.user.AutoState.ON_STOP
        user.auto = False
    else:
        user.auto = data.auto
        user.current_state = models.user.AutoState.INITIAL
        user.status = models.user.AutoStatus.STARTED
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    if send_stop_message:
        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=details.STOP_PROCESS_STARTED)

    return schemas.Status(status='success')


@router.put("/debug_mode", response_model=schemas.Status)
async def update_user_debug_mode(
        data: schemas.UserDebugUpdateUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки режима отладки пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)

    user.debug_mode = data.debug_mode
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.put("/wait_order_minutes", response_model=schemas.Status)
async def update_user_wait_order_minutes(
        data: schemas.UserWaitOrderMinutesUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки времени на выполнение ордера пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)

    user.wait_order_minutes = data.wait_order_minutes
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.put("/test_api", response_model=schemas.Status)
async def update_user_test_api(
        data: schemas.UserTestAPIUpdate,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API настройки использования тестового режима автоматической торговли пользователя
    """
    send_restart_message = False

    user = await helpers.get_user(session=session, telegram_id=data.telegram_id)
    if user.auto:
        send_restart_message = True
        user.status = models.user.AutoStatus.ON_RESTART
    else:
        # FIX
        user.test_api = data.test_api
        user.status = models.user.AutoStatus.PLAY
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    if send_restart_message:
        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=details.RESTART_PROCESS_STARTED)

    return schemas.Status(status='success')


@router.delete("/{telegram_id}/bundle", response_model=schemas.Status)
async def delete_user_bundle(
        telegram_id: str,
        bundle_id: int,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API удаления отлеживаемой связки пользователя
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id)

    await session.execute(sa.delete(models.UserBundle).where(
        models.UserBundle.user_id == user.id,
        models.UserBundle.bundle_id == bundle_id
    ))
    try:
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    return schemas.Status(status='success')


@router.delete("/{telegram_id}", response_model=schemas.Status)
async def delete_user(
        telegram_id: str,
        session: db.AsyncSession = Depends(db.get_session)
):
    """
    API удаления пользователя.
    """
    user = await helpers.get_user(session=session, telegram_id=telegram_id)

    try:
        await session.delete(user)
        await session.commit()
    except sa.exc.DBAPIError as e:
        await session.rollback()

        helpers.abort(code=status.HTTP_400_BAD_REQUEST, detail=helpers.error_detail(e))

    # For example
    # telegram_ids = (await session.scalars(sa.select(models.User.telegram_id)))
    # message = f'Удален пользователь с telegram_id = {telegram_id}'
    #
    # db.bot_sender.send_task('send_notification', (telegram_ids, message))

    return schemas.Status(status='success')
