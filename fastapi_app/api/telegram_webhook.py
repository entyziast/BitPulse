from fastapi import APIRouter, Request
from crud.users import save_chat_id
from worker.tasks import send_telegram_message


router = APIRouter(
    prefix='/telegram',
)


@router.post('/webhook')
async def telegram_webhook(request: Request):
    data = await request.json()
    
    message = data.get("message")
    if not message:
        return {"status": "ok"}
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.startswith("/start"):
        parts = text.split()
        if len(parts) > 1:
            try:
                user_id = int(parts[1])
                from database.database import get_session

                async for db in  get_session():
                    await save_chat_id(db, user_id, chat_id)
                    send_telegram_message.delay(chat_id, "✅ Telegram подключен!")
                    break
            except ValueError:
                send_telegram_message.delay(chat_id, "❌ Неверный формат команды. Пожалуйста, используйте /start <user_id>.")
        else:
            send_telegram_message.delay(chat_id, "❌ Не указан user_id. Пожалуйста, используйте /start <user_id>.")
        return {"status": "ok"}


    return {"status": "ok"}


