import hashlib
import translators as ts
from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

router = Router()

@router.inline_query(F.query.startswith("tr"))
async def inline_translate(inline_query: InlineQuery):
    # Убираем префикс "tr" и пробелы
    query_text = inline_query.query[2:].strip()
    
    if not query_text:
        return

    try:
        # Перевод google (без ключей)
        translated = ts.translate_text(query_text=query_text, to_language='en', translator='google')
        
        result_id = hashlib.md5(query_text.encode()).hexdigest()
        
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    id=result_id,
                    title="Translate to English",
                    description=translated,
                    input_message_content=InputTextMessageContent(message_text=translated)
                )
            ],
            cache_time=300
        )
    except Exception:
        pass
