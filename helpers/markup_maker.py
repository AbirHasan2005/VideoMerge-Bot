# (c) @AbirHasan2005

from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, Message


async def MakeButtons(bot: Client, m: Message, db: dict):
    markup = []
    for i in (await bot.get_messages(chat_id=m.chat.id, message_ids=db.get(m.chat.id))):
        media = i.video or i.document or None
        if media is None:
            continue
        else:
            markup.append([InlineKeyboardButton(f"{media.file_name}", callback_data=f"showFileName_{str(i.message_id)}")])
    markup.append([InlineKeyboardButton("Merge Now", callback_data="mergeNow")])
    markup.append([InlineKeyboardButton("Clear Files", callback_data="cancelProcess")])
    return markup
