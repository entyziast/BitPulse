from fastapi import APIRouter, Request, Depends
from crud.users import save_chat_id, delete_chat_id
from crud.alerts import set_alert_status, delete_alert, get_alert
from schemas.alerts import AlertStatus
from exceptions.alert_exceptions import AlertNotFoundException
from worker.tasks import send_telegram_message
from database.models import UserModel
from dependencies.users import get_current_user
from database.database import get_session
from exceptions.alert_exceptions import (
    AlertNotificationAlreadyEnabledException, 
    AlertNotificationAlreadyDisabledException
)
from database.redis import get_redis
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis
from typing import Annotated
import os
import uuid
import httpx


router = APIRouter(
    tags=['telegram', 'alerts', ],
)


UserMeDep = Annotated[UserModel, Depends(get_current_user)]
RedisDep = Annotated[Redis, Depends(get_redis)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    '/alerts/enable_tg_notifications',
    summary='Enable Telegram notifications',
)
async def enable_tg_notifications(
    user: UserMeDep,
    redis: RedisDep,
):
    if user.tg_chat_id is not None:
        raise AlertNotificationAlreadyEnabledException()

    secret_token = str(uuid.uuid4())[:8]
    await redis.set(f'tg_secret_token:{secret_token}', user.id, ex=300)

    BOT_USERNAME = os.getenv('BOT_USERNAME')

    tg_link = f"https://t.me/{BOT_USERNAME}?start={secret_token}"
    return {
        'message': 'To enable Telegram notifications, please click the link below.',
        'tg_link': tg_link
    }


@router.delete(
    '/alerts/disable_tg_notifications',
    summary='Disable Telegram notifications',
)
async def disable_tg_notifications(
    user: UserMeDep,
    db: SessionDep
):
    if user.tg_chat_id is None:
        raise AlertNotificationAlreadyDisabledException()

    await delete_chat_id(db, user.id)

    return {
        'message': 'Telegram notifications have been disabled.'
    }


async def callback_answer(callback_id: int):
    TELEGRAM_BOT_TOKEN=os.getenv('TELEGRAM_BOT_TOKEN')
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                json={
                    "callback_query_id": callback_id,
                    "text": "Готово!"
                }
            )
        except Exception as e:
            print(f"Error answering callback: {e}")


@router.post(
    '/telegram/webhook',
    include_in_schema=False,
)
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if 'message' in data:

        message = data.get("message")
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text.startswith("/start"):
            parts = text.split()
            if len(parts) > 1:
                try:
                    redis = await get_redis()
                    secret_token = parts[1]
                    user_id_bytes = await redis.get(f'tg_secret_token:{secret_token}')
                    if user_id_bytes is None:
                        send_telegram_message.delay(chat_id, "❌ Неверный или истекший токен. Получите новый токен в приложении.")
                        return {"status": "ok"}
                    await redis.delete(f'tg_secret_token:{secret_token}')

                    async for db in get_session():
                        user_id = int(user_id_bytes)
                        await save_chat_id(db, user_id, chat_id)
                        send_telegram_message.delay(chat_id, "✅ Telegram подключен! Теперь вы будете получать уведомления о срабатывании ваших алертов.")
                        break
                except ValueError:
                    send_telegram_message.delay(chat_id, "❌ Неверный формат команды. Пожалуйста, используйте /start <user_id>.")
            else:
                send_telegram_message.delay(chat_id, "❌ Не указан user_id. Пожалуйста, используйте /start <user_id>.")
            return {"status": "ok"}
        else:
            send_telegram_message.delay(chat_id, "❌ Неизвестная команда. Пожалуйста, используйте /start <user_id> для подключения Telegram.")
            return {"status": "ok"}
    elif 'callback_query' in data:
        callback = data['callback_query']
        callback_id = callback['id']
        chat_id = callback['message']['chat']['id']
        callback_data = callback['data']

        action, alert_id = callback_data.split(':')

        async for db in get_session():
            try:
                alert = await get_alert(db, int(alert_id))
            except AlertNotFoundException:
                send_telegram_message.delay(chat_id, '❌ Алерт не найден!')

            if action == 'reactivate_alert':
                await set_alert_status(db, alert, AlertStatus.ACTIVE)
                send_telegram_message.delay(chat_id, '✅ Алерт снова активен!')
            elif action == 'delete_alert':
                await delete_alert(db, alert)
                send_telegram_message.delay(chat_id, '🗑️ Алерт удален.')

        await callback_answer(callback_id)

        return {"status": "ok"}

    return {"status": "ok"}


