import os
import qrcode
import uuid
import io
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Router, types, html, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, InlineQueryResultCachedPhoto
from utils.language_manager import language_manager

router = Router()

@router.message(Command("qr"))
async def cmd_qr(message: types.Message, command: CommandObject):
    if not command.args:
        error_text = language_manager.get_text('error', message.from_user.id)
        return await message.answer(f"⚠️ {error_text}: Please provide text or link for QR code: `/qr Hello World`", parse_mode="Markdown")

    data_to_encode = command.args
    
    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4,
    )
    qr.add_data(data_to_encode)
    qr.make(fit=True)

    img: Image.Image = qr.make_image(fill_color="black", back_color="white")
    
    # Save image to temporary file
    temp_file_path = f"qr_code_{message.from_user.id}.png"
    img.save(temp_file_path)
    
    try:
        # Use types.FSInputFile and pass PATH to file, not open object
        success_text = language_manager.get_text('qr_created', message.from_user.id)
        await message.answer_photo(
            photo=types.FSInputFile(temp_file_path), 
            caption=f"✅ {success_text}: {html.code(data_to_encode[:50]) + ('...' if len(data_to_encode) > 50 else '')}",
            parse_mode="HTML"
        )
    except Exception as e:
        error_text = language_manager.get_text('error', message.from_user.id)
        await message.answer(f"❌ {error_text}: {e}")
    finally:
        # Always delete temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.inline_query(F.query.startswith("qr "))
async def inline_qr_gen(inline_query: types.InlineQuery):
    data = inline_query.query[3:].strip()
    if not data:
        return

    # Generate QR code
    qr = qrcode.make(data)
    bio = io.BytesIO()
    qr.save(bio, format="PNG")
    bio.seek(0)
    file_bytes = bio.read()

    # Send to dump channel to get file_id
    DUMP_CHANNEL_ID = -1003674095314  # Change this to your channel ID
    
    try:
        temp_msg = await inline_query.bot.send_photo(
            chat_id=DUMP_CHANNEL_ID,
            photo=BufferedInputFile(file_bytes, filename="qr.png")
        )
        file_id = temp_msg.photo[-1].file_id
        
        # Return result via cached photo
        await inline_query.answer([
            types.InlineQueryResultCachedPhoto(
                id=str(uuid.uuid4()),
                photo_file_id=file_id,
                caption="✅ QR Code Generated"
            )
        ], is_personal=True, cache_time=60)
        
    except Exception as e:
        print(f"Dump channel error: {e}")  # Falls here if bot is not admin in channel
