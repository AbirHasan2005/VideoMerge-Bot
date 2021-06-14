# (c) @AbirHasan2005
import asyncio
import time
from configs import Config
from helpers.database.access_db import db
from helpers.display_progress import progress_for_pyrogram, humanbytes
from humanfriendly import format_timespan
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


async def UploadVideo(bot: Client, cb: CallbackQuery, merged_vid_path: str, width, height, duration, video_thumbnail, file_size):
    try:
        sent_ = None
        if (await db.get_upload_as_doc(cb.from_user.id)) is False:
            c_time = time.time()
            sent_ = await bot.send_video(
                chat_id=cb.message.chat.id,
                video=merged_vid_path,
                width=width,
                height=height,
                duration=duration,
                thumb=video_thumbnail,
                caption=Config.CAPTION.format((await bot.get_me()).username) + f"\n\n**File Name:** `{merged_vid_path.rsplit('/', 1)[-1]}`\n**Duration:** `{format_timespan(duration)}`\n**File Size:** `{humanbytes(file_size)}`",
                progress=progress_for_pyrogram,
                progress_args=(
                    "Uploading Video ...",
                    cb.message,
                    c_time
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Developer - @AbirHasan2005", url="https://t.me/AbirHasan2005")],
                        [InlineKeyboardButton("Support Group", url="https://t.me/linux_repo"),
                         InlineKeyboardButton("Bots Channel", url="https://t.me/Discovery_Updates")]
                    ]
                )
            )
        else:
            c_time = time.time()
            sent_ = await bot.send_document(
                chat_id=cb.message.chat.id,
                document=merged_vid_path,
                caption=Config.CAPTION.format((await bot.get_me()).username) + f"\n\n**File Name:** `{merged_vid_path.rsplit('/', 1)[-1]}`\n**Duration:** `{format_timespan(duration)}`\n**File Size:** `{humanbytes(file_size)}`",
                thumb=video_thumbnail,
                progress=progress_for_pyrogram,
                progress_args=(
                    "Uploading Video ...",
                    cb.message,
                    c_time
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Developer - @AbirHasan2005", url="https://t.me/AbirHasan2005")],
                        [InlineKeyboardButton("Support Group", url="https://t.me/linux_repo"),
                         InlineKeyboardButton("Bots Channel", url="https://t.me/Discovery_Updates")]
                    ]
                )
            )
        await asyncio.sleep(Config.TIME_GAP)
        forward_ = await sent_.forward(chat_id=Config.LOG_CHANNEL)
        await forward_.reply_text(
            text=f"**User:** [{cb.from_user.first_name}](tg://user?id={str(cb.from_user.id)})\n**Username:** `{cb.from_user.username}`\n**UserID:** `{cb.from_user.id}`",
            disable_web_page_preview=True,
            quote=True
        )
    except Exception as err:
        print(f"Failed to Upload Video!\nError: {err}")
        try:
            await cb.message.edit(f"Failed to Upload Video!\n**Error:**\n`{err}`")
        except:
            pass
