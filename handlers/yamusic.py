import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib
import io
import json
import random
import string
import typing
import logging
import asyncio
from datetime import datetime

import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from aiogram import Router, F, html
from aiogram.filters import Command
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message, CallbackQuery, BufferedInputFile, InlineQueryResultCachedPhoto

import yandex_music
import yandex_music.exceptions

from utils.user_logger import user_logger
from utils.crypto_manager import crypto_manager

router = Router()
logger = logging.getLogger(__name__)


def init_yamusic_table():
    db = user_logger.db_path
    import sqlite3
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS yamusic_tokens (
            user_id INTEGER PRIMARY KEY,
            token_encrypted TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("PRAGMA table_info(yamusic_tokens)")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'token' in columns and 'token_encrypted' not in columns:
        cur.execute("ALTER TABLE yamusic_tokens ADD COLUMN token_encrypted TEXT")
        cur.execute("SELECT user_id, token FROM yamusic_tokens WHERE token IS NOT NULL")
        tokens = cur.fetchall()
        for user_id, token in tokens:
            encrypted = crypto_manager.encrypt(token)
            cur.execute("UPDATE yamusic_tokens SET token_encrypted = ? WHERE user_id = ?", (encrypted, user_id))
        conn.commit()
        try:
            cur.execute("ALTER TABLE yamusic_tokens DROP COLUMN token")
        except:
            pass
    
    conn.close()

init_yamusic_table()

def get_user_token(user_id: int) -> typing.Optional[str]:
    import sqlite3
    db = user_logger.db_path
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT token_encrypted FROM yamusic_tokens WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    if not result:
        return None
    return crypto_manager.decrypt(result[0])

def set_user_token(user_id: int, token: str):
    import sqlite3
    db = user_logger.db_path
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    encrypted_token = crypto_manager.encrypt(token)
    cur.execute("""
        INSERT OR REPLACE INTO yamusic_tokens (user_id, token_encrypted, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (user_id, encrypted_token))
    conn.commit()
    conn.close()

def delete_user_token(user_id: int):
    import sqlite3
    db = user_logger.db_path
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("DELETE FROM yamusic_tokens WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

class Banners:
    def __init__(
        self,
        title: str,
        artists: list[str],
        duration: int,
        progress: int,
        track_cover: bytes,
        fonts_data: list[bytes],
        album_title: str = "Сингл",
        meta_info: str = "Music",
        is_liked: bool = False,
        repeat_mode: str = "NONE",
        blur: int = 0,
    ):
        self.title = title
        self.artists = artists
        self.duration = duration
        self.progress = progress
        self.track_cover = track_cover
        self.fonts_data = fonts_data
        self.album_title = album_title
        self.meta_info = meta_info
        self.is_liked = is_liked
        self.repeat_mode = repeat_mode
        self.blur = blur

    def ultra(self) -> io.BytesIO:
        WIDTH, HEIGHT = 2560, 1220

        def get_font(size):
            for font_bytes in self.fonts_data:
                try:
                    return ImageFont.truetype(io.BytesIO(font_bytes), size)
                except Exception:
                    continue
            return ImageFont.load_default()

        try:
            original_cover = Image.open(io.BytesIO(self.track_cover)).convert("RGBA")
        except Exception:
            original_cover = Image.new("RGBA", (1000, 1000), "black")

        dominant_color_img = original_cover.resize((1, 1), Image.Resampling.LANCZOS)
        dominant_color = dominant_color_img.getpixel((0, 0))

        r, g, b, a = dominant_color
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        if brightness < 60:
            r = min(255, r + 60)
            g = min(255, g + 60)
            b = min(255, b + 60)
            dominant_color = (r, g, b, 255)

        background = original_cover.copy()
        bg_w, bg_h = background.size

        target_ratio = WIDTH / HEIGHT
        current_ratio = bg_w / bg_h

        if current_ratio > target_ratio:
            new_w = int(bg_h * target_ratio)
            offset = (bg_w - new_w) // 2
            background = background.crop((offset, 0, offset + new_w, bg_h))
        else:
            new_h = int(bg_w / target_ratio)
            offset = (bg_h - new_h) // 2
            background = background.crop((0, offset, bg_w, offset + new_h))

        background = background.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        
        if self.blur > 0:
            background = background.filter(ImageFilter.GaussianBlur(radius=self.blur))

        dark_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 180))
        background = Image.alpha_composite(background, dark_overlay)

        cover_size = 500
        cover_x = (WIDTH - cover_size) // 2
        cover_y = 160

        glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw_glow = ImageDraw.Draw(glow_layer)

        glow_rect_size = 620
        g_x = (WIDTH - glow_rect_size) // 2
        g_y = cover_y + (cover_size - glow_rect_size) // 2

        draw_glow.rounded_rectangle(
            (g_x, g_y, g_x + glow_rect_size, g_y + glow_rect_size),
            radius=50,
            fill=dominant_color,
        )

        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=60))
        glow_layer = ImageEnhance.Brightness(glow_layer).enhance(1.4)
        glow_layer = ImageEnhance.Color(glow_layer).enhance(1.2)

        background = Image.alpha_composite(background, glow_layer)

        cover_img = original_cover.resize(
            (cover_size, cover_size), Image.Resampling.LANCZOS
        )

        mask = Image.new("L", (cover_size, cover_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle((0, 0, cover_size, cover_size), radius=45, fill=255)

        background.paste(cover_img, (cover_x, cover_y), mask)

        draw = ImageDraw.Draw(background)
        center_x = WIDTH // 2
        current_y = cover_y + cover_size + 130

        def draw_text_shadow(text, pos, font, fill="white", anchor="ms"):
            x, y = pos
            draw.text(
                (x + 2, y + 2), text, font=font, fill=(0, 0, 0, 240), anchor=anchor
            )
            draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

        font_title = get_font(100)
        title_text = self.title
        if len(title_text) > 30:
            title_text = title_text[:30] + "..."
        draw_text_shadow(title_text.upper(), (center_x, current_y), font_title)

        current_y += 85

        font_artist = get_font(65)
        artist_text = ", ".join(self.artists)
        if len(artist_text) > 45:
            artist_text = artist_text[:45] + "..."
        draw_text_shadow(
            artist_text.upper(),
            (center_x, current_y),
            font_artist,
            fill=(255, 255, 255, 240),
        )

        current_y += 80

        bar_width = 800
        bar_height = 6
        font_time = get_font(40)

        bar_start_x = center_x - (bar_width // 2)
        bar_end_x = center_x + (bar_width // 2)
        bar_y = current_y

        total_mins = self.duration // 1000 // 60
        total_secs = (self.duration // 1000) % 60
        total_time_str = f"{total_mins}:{total_secs:02d}"

        cur_mins = self.progress // 1000 // 60
        cur_secs = (self.progress // 1000) % 60
        cur_time_str = f"{cur_mins}:{cur_secs:02d}"

        draw_text_shadow(
            cur_time_str, (bar_start_x - 30, bar_y), font_time, anchor="rm"
        )
        draw_text_shadow(
            total_time_str, (bar_end_x + 30, bar_y), font_time, anchor="lm"
        )

        draw.line(
            [(bar_start_x, bar_y), (bar_end_x, bar_y)],
            fill=(255, 255, 255, 80),
            width=bar_height,
        )

        if self.duration > 0:
            progress_ratio = self.progress / self.duration
        else:
            progress_ratio = 0
        progress_px = int(bar_width * progress_ratio)
        if progress_px > bar_width:
            progress_px = bar_width

        draw.line(
            [(bar_start_x, bar_y), (bar_start_x + progress_px, bar_y)],
            fill="white",
            width=bar_height + 5,
        )
        draw.ellipse(
            (
                bar_start_x + progress_px - 10,
                bar_y - 10,
                bar_start_x + progress_px + 10,
                bar_y + 10,
            ),
            fill="white",
        )

        current_y += 80

        font_album = get_font(50)
        album_text = self.album_title
        if len(album_text) > 50:
            album_text = album_text[:50] + "..."
        draw_text_shadow(
            album_text, (center_x, current_y), font_album, fill=(230, 230, 230)
        )
        current_y += 60

        font_meta = get_font(40)

        draw_text_shadow(
            self.meta_info, (center_x, current_y), font_meta, fill=(210, 210, 210)
        )

        icon_y_center = current_y - 15

        if self.repeat_mode != "NONE":
            rep_x = bar_start_x
            rep_size = 18

            draw.arc(
                [
                    rep_x - rep_size,
                    icon_y_center - rep_size,
                    rep_x + rep_size,
                    icon_y_center + rep_size,
                ],
                start=40,
                end=320,
                fill=(220, 220, 220, 255),
                width=3,
            )

            draw.polygon(
                [
                    (rep_x + rep_size - 2, icon_y_center - 8),
                    (rep_x + rep_size + 8, icon_y_center),
                    (rep_x + rep_size - 8, icon_y_center + 4),
                ],
                fill=(220, 220, 220, 255),
            )

            if self.repeat_mode == "ONE":
                font_one = get_font(20)
                draw.text(
                    (rep_x + rep_size + 12, icon_y_center),
                    "1",
                    font=font_one,
                    fill="white",
                    anchor="lm",
                )

        heart_x = bar_end_x
        heart_size = 20

        c_r = heart_size // 2 + 2

        c1_box = (
            heart_x - c_r * 2,
            icon_y_center - c_r - 2,
            heart_x,
            icon_y_center + c_r - 2,
        )
        c2_box = (
            heart_x,
            icon_y_center - c_r - 2,
            heart_x + c_r * 2,
            icon_y_center + c_r - 2,
        )
        tri_points = [
            (heart_x - c_r * 2 + 2, icon_y_center + 1),
            (heart_x + c_r * 2 - 2, icon_y_center + 1),
            (heart_x, icon_y_center + heart_size + 5),
        ]

        by = io.BytesIO()
        background.save(by, format="PNG")
        by.seek(0)
        by.name = "banner.png"
        return by

class YaMusicClient:
    def __init__(self, token: str):
        self.token = token
        self.client = None
        self.device_id = "".join(random.choices(string.ascii_lowercase, k=16))

    async def get_client(self):
        if self.client:
            return self.client
        try:
            self.client = await yandex_music.ClientAsync(self.token).init()
            return self.client
        except Exception as e:
            logger.error(f"Failed to init Yandex Music: {e}")
            return None

    async def download_bytes(self, url: str) -> typing.Optional[bytes]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.read()
        except Exception:
            return None
        return None

    async def get_now_playing(self):
        ym_client = await self.get_client()
        if not ym_client:
            return {}

        ynison = await self._get_ynison()
        if not ynison or (
            len(
                ynison.get("player_state", {})
                .get("player_queue", {})
                .get("playable_list", [])
            )
            == 0
        ):
            return {}

        try:
            player_state = ynison["player_state"]
            raw_track = player_state["player_queue"]["playable_list"][
                player_state["player_queue"]["current_playable_index"]
            ]

            track_object = (await ym_client.tracks(raw_track["playable_id"]))[0]

            status = player_state["status"]
            progress_ms = int(status["progress_ms"])
            duration_ms = int(status["duration_ms"])

            repeat_mode = (
                player_state.get("player_queue", {})
                .get("options", {})
                .get("repeat_mode", "NONE")
            )

            return (
                {
                    "track_object": track_object,
                    "paused": status["paused"],
                    "playable_id": raw_track["playable_id"],
                    "duration_ms": duration_ms,
                    "progress_ms": progress_ms,
                    "entity_id": player_state["player_queue"]["entity_id"],
                    "entity_type": player_state["player_queue"]["entity_type"],
                    "repeat_mode": repeat_mode,
                    "device": [
                        x
                        for x in ynison["devices"]
                        if x["info"]["device_id"]
                        == ynison.get("active_device_id_optional", "")
                    ],
                    "track": {
                        "track_id": track_object.track_id,
                        "album_id": track_object.albums[0].id
                        if track_object.albums
                        else 0,
                        "title": track_object.title,
                        "artist": track_object.artists_name(),
                        "duration": track_object.duration_ms // 1000,
                        "minutes": round(track_object.duration_ms / 1000) // 60,
                        "seconds": round(track_object.duration_ms / 1000) % 60,
                    },
                }
                if raw_track["playable_type"] != "LOCAL_TRACK"
                else {}
            )
        except Exception as e:
            logger.error(f"Get Now Playing Error: {e}")
            return {}

    async def _get_ynison(self):
        async def create_ws(token, ws_proto):
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    "wss://ynison.music.yandex.ru/redirector.YnisonRedirectService/GetRedirectToYnison",
                    headers={
                        "Sec-WebSocket-Protocol": f"Bearer, v2, {json.dumps(ws_proto)}",
                        "Origin": "http://music.yandex.ru",
                        "Authorization": f"OAuth {token}",
                    },
                ) as ws:
                    response = await ws.receive()
                    return json.loads(response.data)

        ws_proto = {
            "Ynison-Device-Id": self.device_id,
            "Ynison-Device-Info": json.dumps({"app_name": "Chrome", "type": 1}),
        }

        try:
            data = await create_ws(self.token, ws_proto)
            ws_proto["Ynison-Redirect-Ticket"] = data["redirect_ticket"]
            payload = {
                "update_full_state": {
                    "player_state": {
                        "player_queue": {
                            "current_playable_index": -1,
                            "entity_id": "",
                            "entity_type": "VARIOUS",
                            "playable_list": [],
                            "options": {"repeat_mode": "NONE"},
                            "entity_context": "BASED_ON_ENTITY_BY_DEFAULT",
                            "version": {
                                "device_id": self.device_id,
                                "version": 9021243204784341000,
                                "timestamp_ms": 0,
                            },
                            "from_optional": "",
                        },
                        "status": {
                            "duration_ms": 0,
                            "paused": True,
                            "playback_speed": 1,
                            "progress_ms": 0,
                            "version": {
                                "device_id": self.device_id,
                                "version": 8321822175199937000,
                                "timestamp_ms": 0,
                            },
                        },
                    },
                    "device": {
                        "capabilities": {
                            "can_be_player": True,
                            "can_be_remote_controller": False,
                            "volume_granularity": 16,
                        },
                        "info": {
                            "device_id": self.device_id,
                            "type": "WEB",
                            "title": "Chrome Browser",
                            "app_name": "Chrome",
                        },
                        "volume_info": {"volume": 0},
                        "is_shadow": True,
                    },
                    "is_currently_active": False,
                },
                "rid": "ac281c26-a047-4419-ad00-e4fbfda1cba3",
                "player_action_timestamp_ms": 0,
                "activity_interception_type": "DO_NOT_INTERCEPT_BY_DEFAULT",
            }
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    f"wss://{data['host']}/ynison_state.YnisonStateService/PutYnisonState",
                    headers={
                        "Sec-WebSocket-Protocol": f"Bearer, v2, {json.dumps(ws_proto)}",
                        "Origin": "http://music.yandex.ru",
                        "Authorization": f"OAuth {self.token}",
                    },
                ) as ws:
                    await ws.send_str(json.dumps(payload))
                    response = await ws.receive()
                    ynison: dict = json.loads(response.data)
            return ynison
        except Exception as e:
            logger.error(f"Ynison Error: {e}")
            return {}

clients_cache = {}

def get_client(user_id: int) -> typing.Optional[YaMusicClient]:
    token = get_user_token(user_id)
    if not token:
        return None
    if user_id not in clients_cache:
        clients_cache[user_id] = YaMusicClient(token)
    return clients_cache[user_id]

DUMP_CHANNEL_ID = -1003674095314

@router.message(Command("yamusic"))
async def cmd_yamusic(message: Message):
    """Configure Yandex Music token"""
    args = message.text.split(maxsplit=1)
    
    if len(args) == 1:
        token = get_user_token(message.from_user.id)
        if token:
            await message.answer(
                f"<b>🎵 Yandex Music Configuration</b>\n\n"
                f"Token: <code>{token[:15]}...</code> (set)\n\n"
                f"Use: <code>/yamusic &lt;token&gt;</code> to set new token\n"
                f"Use: <code>/yamusic clear</code> to remove token\n\n"
                f"📜 <a href=\"https://yandex-music.rtfd.io/en/main/token.html\">Get token here</a>",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "<b>🎵 Yandex Music Configuration</b>\n\n"
                "No token set.\n\n"
                "Use: <code>/yamusic &lt;token&gt;</code> to set your token\n\n"
                "📜 <a href=\"https://yandex-music.rtfd.io/en/main/token.html\">Get token here</a>",
                parse_mode="HTML"
            )
    elif len(args) > 1:
        token_arg = args[1].strip()
        
        if token_arg.lower() == "clear":
            delete_user_token(message.from_user.id)
            if message.from_user.id in clients_cache:
                del clients_cache[message.from_user.id]
            await message.answer("✅ Yandex Music token removed.")
        else:
            set_user_token(message.from_user.id, token_arg)
            if message.from_user.id in clients_cache:
                del clients_cache[message.from_user.id]
            await message.answer("✅ Yandex Music token saved successfully!")

@router.inline_query(F.query.startswith("ym"))
async def inline_yamusic(inline_query: InlineQuery):
    """Show currently playing track via inline query"""
    query_text = inline_query.query[2:].strip()
    user_id = inline_query.from_user.id
    
    ym_client = get_client(user_id)
    if not ym_client:
        result_id = hashlib.md5(f"no_token_{user_id}".encode()).hexdigest()
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    id=result_id,
                    title="Yandex Music - Token Required",
                    description="Please set your token with /yamusic",
                    input_message_content=InputTextMessageContent(
                        message_text="🎵 <b>Yandex Music</b>\n\n❌ Please set your Yandex Music token first.\nUse /yamusic <token> in private chat with the bot."
                    )
                )
            ],
            cache_time=60
        )
        return

    now = await ym_client.get_now_playing()
    
    if not now or now.get("paused"):
        result_id = hashlib.md5(f"not_playing_{user_id}".encode()).hexdigest()
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    id=result_id,
                    title="Yandex Music - Not Playing",
                    description="No track currently playing",
                    input_message_content=InputTextMessageContent(
                        message_text="🎵 <b>Yandex Music</b>\n\n❌ Nothing is currently playing."
                    )
                )
            ],
            cache_time=30
        )
        return

    track = now["track"]
    artists = ", ".join(track["artist"])
    title = track["title"]
    
    progress_pct = int((now["progress_ms"] / now["duration_ms"]) * 100) if now["duration_ms"] > 0 else 0
    
    device_name = "Unknown"
    volume = "N/A"
    if now["device"]:
        device = now["device"][0]
        device_name = device["info"]["title"]
        volume = round(device["volume_info"]["volume"] * 100)
    
    entity_type_map = {
        "PLAYLIST": "Playlist",
        "ALBUM": "Album", 
        "ARTIST": "Artist",
        "VARIOUS": "Various"
    }
    entity_type = entity_type_map.get(now["entity_type"], "Various")
    
    progress_bar = "█" * (progress_pct // 5) + "░" * (20 - progress_pct // 5)
    
    total_mins = now["duration_ms"] // 1000 // 60
    total_secs = (now["duration_ms"] // 1000) % 60
    cur_mins = now["progress_ms"] // 1000 // 60
    cur_secs = (now["progress_ms"] // 1000) % 60
    
    time_str = f"{cur_mins}:{cur_secs:02d} / {total_mins}:{total_secs:02d}"
    
    track_link = f"https://song.link/ya/{now['playable_id']}"
    
    status_icon = "⏸️" if now["paused"] else "▶️"
    repeat_icon = {"NONE": "", "ONE": "🔂", "ALL": "🔁"}.get(now.get("repeat_mode", "NONE"), "")
    
    message_text = (
        f"<b>{status_icon} Now Playing</b>\n"
        f"🎵 <b>{title}</b>\n"
        f"👤 {artists}\n\n"
        f"⏱️ <code>{time_str}</code>\n"
        f"📊 {progress_bar} {progress_pct}%\n\n"
        f"🔊 Volume: {volume}% | 📱 {device_name}\n"
        f"📂 From: {entity_type} {repeat_icon}\n\n"
        f'<a href="{track_link}">Open in music app</a>'
    )
    
    result_id = hashlib.md5(f"playing_{now['playable_id']}_{now['progress_ms']}".encode()).hexdigest()
    
    await inline_query.answer(
        results=[
            InlineQueryResultArticle(
                id=result_id,
                title=f"{artists} — {title}",
                description=f"Playing: {time_str}",
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="HTML",
                    disable_web_page_preview=False
                )
            )
        ],
        cache_time=5
    )
