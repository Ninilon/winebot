import time
from typing import Any, Awaitable, Callable, Dict, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, InlineQuery

class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, msg_limit: float = 3.0, inline_limit: float = 0.5):
        self.msg_limit = msg_limit
        self.inline_limit = inline_limit
        self.storage = {}  # {user_id: last_time}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Union[Message, InlineQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, InlineQuery],
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        current_time = time.time()
        
        # Определяем лимит в зависимости от типа события
        limit = self.msg_limit if isinstance(event, Message) else self.inline_limit

        if user_id in self.storage:
            last_time = self.storage[user_id]
            if current_time - last_time < limit:
                # Если это сообщение — отвечаем текстом
                if isinstance(event, Message):
                    return await event.answer(f"⏳ Coomands Cooldown: {self.msg_limit}с.")
                # Если инлайн — просто игнорируем запрос (предотвращаем лишнюю нагрузку)
                return 

        self.storage[user_id] = current_time
        return await handler(event, data)
