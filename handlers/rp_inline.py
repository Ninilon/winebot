import hashlib
from aiogram import Router, types, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

router = Router()

@router.inline_query(F.query.startswith("rp "))
async def rp_inline_handler(inline_query: InlineQuery):
    text = inline_query.query.strip()
    
    # Если в инлайне пусто, ничего не выводим
    if not text:
        return

    # Разбиваем: "обнял @username" -> action="обнял", target="@username"
    parts = text.split(maxsplit=1)
    action = parts[0]
    target = parts[1] if len(parts) > 1 else "воздух"

    # Тот самый @username человека, который ПИШЕТ инлайн
    sender_username = f"@{inline_query.from_user.username}" if inline_query.from_user.username else inline_query.from_user.first_name
    
    # Итоговый вывод: @sender_username обнял @username
    final_output = f"{sender_username} <b>{action}</b> {target}"
    
    result_id = hashlib.md5(text.encode()).hexdigest()
    
    item = InlineQueryResultArticle(
        id=result_id,
        title=f"Действие: {action}",
        description=f"{sender_username} {action} {target}",
        input_message_content=InputTextMessageContent(
            message_text=final_output,
            parse_mode="HTML"
        )
    )

    # is_personal=True ВАЖНО, чтобы для каждого юзера подставлялся ЕГО ник
    await inline_query.answer(results=[item], cache_time=1, is_personal=True)
