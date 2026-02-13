import sys
import os
import io
import time
import tempfile
import sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Router, types, F, html
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile
from utils.language_manager import language_manager
from PIL import Image

router = Router()
DATABASE_PATH = "users.db"
MAX_FILE_SIZE = 100 * 1024 * 1024
TEMP_CACHE_TTL = 300

AUDIO_PRESETS = {
    'low': '64k',
    'medium': '128k',
    'high': '192k',
    'max': '320k'
}

def init_conversion_cache():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversion_cache (
            file_hash TEXT PRIMARY KEY,
            converted_data BLOB,
            target_format TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_conversion_cache()

def get_cached_conversion(file_hash: str, target_format: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT converted_data FROM conversion_cache 
        WHERE file_hash = ? AND target_format = ?
    """, (file_hash, target_format))
    result = cur.fetchone()
    conn.close()
    
    if result:
        return result[0]
    return None

def cache_conversion(file_hash: str, target_format: str, data: bytes):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO conversion_cache (file_hash, converted_data, target_format, created_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (file_hash, data, target_format))
    conn.commit()
    conn.close()

def cleanup_old_cache():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM conversion_cache 
        WHERE created_at < datetime('now', '-10 seconds')
    """)
    conn.commit()
    conn.close()

async def convert_image(input_file: io.BytesIO, target_format: str) -> io.BytesIO:
    try:
        from PIL import Image
        image = Image.open(input_file)
        
        quality_map = {
            'jpg': 85, 'jpeg': 85,
            'webp': 80, 'png': 95,
            'gif': 90, 'bmp': 100, 'tiff': 95
        }
        
        quality = quality_map.get(target_format.lower(), 85)
        
        output = io.BytesIO()
        
        if target_format.lower() in ['jpg', 'jpeg', 'webp']:
            image.save(output, format='JPEG' if target_format.lower() == 'jpg' else target_format.upper(), quality=quality)
        elif target_format.lower() == 'png':
            image.save(output, format='PNG', optimize=True)
        elif target_format.lower() == 'gif':
            image.save(output, format='GIF', optimize=True)
        elif target_format.lower() == 'bmp':
            image.save(output, format='BMP')
        elif target_format.lower() == 'tiff':
            image.save(output, format='TIFF')
        else:
            image.save(output, format='PNG')
        
        output.seek(0)
        return output
    except Exception:
        return input_file

async def convert_audio(input_file: io.BytesIO, target_format: str, bitrate: str = '192k') -> io.BytesIO:
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(input_file)
        
        output = io.BytesIO()
        
        if target_format.lower() in ['mp3']:
            audio.export(output, format='mp3', bitrate=bitrate)
        elif target_format.lower() == 'wav':
            audio.export(output, format='wav')
        elif target_format.lower() == 'ogg':
            audio.export(output, format='ogg')
        elif target_format.lower() == 'flac':
            audio.export(output, format='flac')
        elif target_format.lower() == 'm4a':
            audio.export(output, format='mp4', bitrate=bitrate)
        elif target_format.lower() == 'aac':
            audio.export(output, format='adts')
        else:
            audio.export(output, format='mp3')
        
        output.seek(0)
        return output
    except ImportError:
        return input_file
    except Exception:
        return input_file

def parse_conversion_args(args: str) -> tuple:
    args = args.lower().split()
    target_format = None
    bitrate = '192k'
    
    if len(args) >= 1:
        target_format = args[0]
    
    if len(args) >= 2 and args[0] in AUDIO_PRESETS:
        bitrate = AUDIO_PRESETS.get(args[1], '192k')
    
    return target_format, bitrate

@router.message(F.document)
async def handle_file_upload(message: types.Message):
    try:
        doc = message.document
        if not doc:
            return
        
        file_size = doc.file_size or 0
        
        if file_size > MAX_FILE_SIZE:
            error_text = language_manager.get_text('convert_too_large', message.from_user.id)
            await message.answer(f"❌ {error_text} (100MB limit exceeded)")
            return
        
        supported_formats = {
            'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff',
            'mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac',
            'pdf', 'docx', 'xlsx', 'csv'
        }
        
        filename = doc.file_name or 'unknown'
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        if file_ext not in supported_formats:
            error_text = language_manager.get_text('convert_unsupported', message.from_user.id)
            await message.answer(f"❌ {error_text}: {file_ext}")
            return
        
        convert_text = language_manager.get_text('convert', message.from_user.id)
        text = (
            f"📁 {html.bold('File Received:')}\n"
            f"{'─' * 20}\n"
            f"📄 {html.bold('Name:')} {filename}\n"
            f"📊 {html.bold('Size:')} {file_size / 1024 / 1024:.2f} MB\n\n"
            f"💡 {convert_text}\n\n"
            f"<code>/convert png</code> - Convert to PNG\n"
            f"<code>/convert jpg</code> - Convert to JPG\n"
            f"<code>/convert webp</code> - Convert to WebP\n"
            f"<code>/convert gif</code> - Convert to GIF\n"
            f"<code>/convert mp3</code> - Convert to MP3\n"
            f"<code>/convert mp3 128k</code> - MP3 at 128kbps\n"
            f"<code>/convert mp3 high</code> - MP3 at 192kbps\n\n"
            f"📸 <b>Images:</b> PNG, JPG, WEBP, GIF, BMP, TIFF\n"
            f"🎵 <b>Audio:</b> MP3, WAV, OGG, FLAC, M4A, AAC"
        )
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        error_text = language_manager.get_text('error', message.from_user.id)
        await message.answer(f"❌ {error_text}: {type(e).__name__}")

@router.message(Command("convert"))
async def cmd_convert(message: types.Message, command: CommandObject):
    if not message.reply_to_message:
        await message.answer("❌ Please reply to a file to convert it.")
        return
    
    if not command.args:
        error_text = language_manager.get_text('error', message.from_user.id)
        await message.answer(f"❌ {error_text}: Usage: `/convert png` or `/convert mp3`")
        return
    
    try:
        reply_msg = message.reply_to_message
        
        if reply_msg.document:
            doc = reply_msg.document
            file_size = doc.file_size or 0
            
            if file_size > MAX_FILE_SIZE:
                error_text = language_manager.get_text('convert_too_large', message.from_user.id)
                await message.answer(f"❌ {error_text} (100MB limit exceeded)")
                return
            
            target_format, bitrate = parse_conversion_args(command.args)
            
            filename = doc.file_name or 'unknown'
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            
            if not file_ext:
                await message.answer("❌ Cannot determine file type.")
                return
            
            import hashlib
            file_content = io.BytesIO()
            await message.bot.download_file(doc.file_path, file_content)
            file_bytes = file_content.getvalue()
            file_hash = hashlib.md5(file_bytes).hexdigest() + '_' + target_format
            
            cached_data = get_cached_conversion(file_hash, target_format)
            cleanup_old_cache()
            
            if cached_data:
                output_file = io.BytesIO(cached_data)
                output_file.name = f"converted.{target_format}"
                success_text = language_manager.get_text('convert_success', message.from_user.id)
                await message.answer_document(
                    output_file,
                    caption=f"✅ {success_text}: {target_format} (from cache)"
                )
                return
            
            status_msg = await message.answer("⏳ Converting...")
            
            file_content.seek(0)
            
            if file_ext in ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff']:
                output_file = await convert_image(file_content, target_format)
                output_file.name = f"converted.{target_format}"
            elif file_ext in ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac']:
                output_file = await convert_audio(file_content, target_format, bitrate)
                output_file.name = f"converted.{target_format}"
            else:
                await status_msg.delete_text()
                error_text = language_manager.get_text('convert_unsupported', message.from_user.id)
                await message.answer(f"❌ {error_text}: Conversion not supported for this file type.")
                return
            
            output_file.seek(0)
            cache_conversion(file_hash, target_format, output_file.getvalue())
            
            success_text = language_manager.get_text('convert_success', message.from_user.id)
            await message.answer_document(
                output_file,
                caption=f"✅ {success_text}: {target_format}"
            )
            
            await status_msg.delete_text()
            
        elif reply_msg.photo:
            photo = reply_msg.photo[-1]
            file_info = await message.bot.get_file(photo.file_id)
            
            target_format = command.args.strip().lower()
            
            if target_format not in ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff']:
                await message.answer("❌ Invalid image format. Use: png, jpg, webp, gif, bmp, tiff")
                return
            
            status_msg = await message.answer("⏳ Converting...")
            
            file_content = io.BytesIO()
            await message.bot.download_file(file_info.file_path, file_content)
            
            output_file = await convert_image(file_content, target_format)
            output_file.name = f"converted.{target_format}"
            
            success_text = language_manager.get_text('convert_success', message.from_user.id)
            await message.answer_photo(
                output_file,
                caption=f"✅ {success_text}: {target_format}"
            )
            
            await status_msg.delete_text()
        else:
            await message.answer("❌ Please reply to a file or image to convert.")
            
    except Exception as e:
        error_text = language_manager.get_text('error', message.from_user.id)
        await message.answer(f"❌ {error_text}: {type(e).__name__}")
