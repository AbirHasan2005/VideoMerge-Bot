# (c) @AbirHasan2005
# This is very simple Telegram Videos Merge Bot.
# Coded by a Nub.
# Don't Laugh seeing the codes.
# Me learning.

import os
import time
import string
import shutil
import psutil
import random
import asyncio
from PIL import Image
from configs import Config
from pyromod import listen
from pyrogram import Client, filters
from helpers.markup_maker import MakeButtons
from helpers.streamtape import UploadToStreamtape
from helpers.clean import delete_all
from hachoir.parser import createParser
from helpers.check_gap import CheckTimeGap
from helpers.database.access_db import db
from helpers.database.add_user import AddUserToDatabase
from helpers.uploader import UploadVideo
from helpers.settings import OpenSettings
from helpers.forcesub import ForceSub
from hachoir.metadata import extractMetadata
from helpers.display_progress import progress_for_pyrogram, humanbytes
from helpers.broadcast import broadcast_handler
from helpers.ffmpeg import MergeVideo, generate_screen_shots, cult_small_video
from asyncio.exceptions import TimeoutError
from pyrogram.errors import FloodWait, UserNotParticipant, MessageNotModified
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, InputMediaPhoto

QueueDB = {}
ReplyDB = {}
FormtDB = {}
NubBot = Client(
    session_name=Config.SESSION_NAME,
    api_id=int(Config.API_ID),
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)


@NubBot.on_message(filters.private & filters.command("start"))
async def start_handler(bot: Client, m: Message):
    await AddUserToDatabase(bot, m)
    Fsub = await ForceSub(bot, m)
    if Fsub == 400:
        return
    await m.reply_text(
        text=Config.START_TEXT,
        disable_web_page_preview=True,
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Developer - @AbirHasan2005", url="https://t.me/AbirHasan2005")],
                [InlineKeyboardButton("Support Group", url="https://t.me/linux_repo"),
                 InlineKeyboardButton("Bots Channel", url="https://t.me/Discovery_Updates")],
                [InlineKeyboardButton("Open Settings", callback_data="openSettings")],
                [InlineKeyboardButton("Close", callback_data="closeMeh")]
            ]
        )
    )


@NubBot.on_message(filters.private & (filters.video | filters.document) & ~filters.edited)
async def videos_handler(bot: Client, m: Message):
    await AddUserToDatabase(bot, m)
    Fsub = await ForceSub(bot, m)
    if Fsub == 400:
        return
    media = m.video or m.document
    if media.file_name is None:
        await m.reply_text("File Name Not Found!")
        return
    if media.file_name.rsplit(".", 1)[-1].lower() not in ["mp4", "mkv", "webm"]:
        await m.reply_text("This Video Format not Allowed!\nOnly send MP4 or MKV or WEBM.", quote=True)
        return
    if QueueDB.get(m.from_user.id, None) is None:
        FormtDB.update({m.from_user.id: media.file_name.rsplit(".", 1)[-1].lower()})
    if (FormtDB.get(m.from_user.id, None) is not None) and (media.file_name.rsplit(".", 1)[-1].lower() != FormtDB.get(m.from_user.id)):
        await m.reply_text(f"First you sent a {FormtDB.get(m.from_user.id).upper()} video so now send only that type of video.", quote=True)
        return
    input_ = f"{Config.DOWN_PATH}/{m.from_user.id}/input.txt"
    if os.path.exists(input_):
        await m.reply_text("Sorry Unkil,\nAlready One in Progress!\nDon't Spam Plox.")
        return
    isInGap, sleepTime = await CheckTimeGap(m.from_user.id)
    if isInGap is True:
        await m.reply_text(f"Sorry Sir,\nNo Flooding Allowed!\nSend Video After `{str(sleepTime)}s` !!", quote=True)
    else:
        editable = await m.reply_text("Please Wait ...", quote=True)
        MessageText = "Okay,\nNow Send Me Next Video or Press **Merge Now** Button!"
        if QueueDB.get(m.from_user.id, None) is None:
            QueueDB.update({m.from_user.id: []})
        if (len(QueueDB.get(m.from_user.id)) >= 0) and (len(QueueDB.get(m.from_user.id)) <= Config.MAX_VIDEOS):
            QueueDB.get(m.from_user.id).append(m.message_id)
            if ReplyDB.get(m.from_user.id, None) is not None:
                await bot.delete_messages(chat_id=m.chat.id, message_ids=ReplyDB.get(m.from_user.id))
            if FormtDB.get(m.from_user.id, None) is None:
                FormtDB.update({m.from_user.id: media.file_name.rsplit(".", 1)[-1].lower()})
            await asyncio.sleep(Config.TIME_GAP)
            if len(QueueDB.get(m.from_user.id)) == Config.MAX_VIDEOS:
                MessageText = "Okay Unkil, Now Just Press **Merge Now** Button Plox!"
            markup = await MakeButtons(bot, m, QueueDB)
            await editable.edit(text="Your Video Added to Queue!")
            reply_ = await m.reply_text(
                text=MessageText,
                reply_markup=InlineKeyboardMarkup(markup),
                quote=True
            )
            ReplyDB.update({m.from_user.id: reply_.message_id})
        elif len(QueueDB.get(m.from_user.id)) > Config.MAX_VIDEOS:
            markup = await MakeButtons(bot, m, QueueDB)
            await editable.edit(
                text=f"Sorry Unkil,\nMax {str(Config.MAX_VIDEOS)} Videos Allowed to Merge Together!\nPress **Merge Now** Button Now!",
                reply_markup=InlineKeyboardMarkup(markup)
            )


@NubBot.on_message(filters.private & filters.photo & ~filters.edited)
async def photo_handler(bot: Client, m: Message):
    await AddUserToDatabase(bot, m)
    Fsub = await ForceSub(bot, m)
    if Fsub == 400:
        return
    editable = await m.reply_text("Saving Thumbnail to Database ...", quote=True)
    await db.set_thumbnail(m.from_user.id, thumbnail=m.photo.file_id)
    await editable.edit(
        text="Thumbnail Saved Successfully!",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Show Thumbnail", callback_data="showThumbnail")],
                [InlineKeyboardButton("Delete Thumbnail", callback_data="deleteThumbnail")]
            ]
        )
    )


@NubBot.on_message(filters.private & filters.command("settings"))
async def settings_handler(bot: Client, m: Message):
    await AddUserToDatabase(bot, m)
    Fsub = await ForceSub(bot, m)
    if Fsub == 400:
        return
    editable = await m.reply_text("Please Wait ...", quote=True)
    await OpenSettings(editable, m.from_user.id)


@NubBot.on_message(filters.private & filters.command("broadcast") & filters.reply & filters.user(Config.BOT_OWNER) & ~filters.edited)
async def _broadcast(_, m: Message):
    await broadcast_handler(m)


@NubBot.on_message(filters.private & filters.command("status") & filters.user(Config.BOT_OWNER))
async def _status(_, m: Message):
    total, used, free = shutil.disk_usage(".")
    total = humanbytes(total)
    used = humanbytes(used)
    free = humanbytes(free)
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    total_users = await db.total_users_count()
    await m.reply_text(
        text=f"**Total Disk Space:** {total} \n**Used Space:** {used}({disk_usage}%) \n**Free Space:** {free} \n**CPU Usage:** {cpu_usage}% \n**RAM Usage:** {ram_usage}%\n\n**Total Users in DB:** `{total_users}`",
        parse_mode="Markdown",
        quote=True
    )


@NubBot.on_message(filters.private & filters.command("check") & filters.user(Config.BOT_OWNER))
async def check_handler(bot: Client, m: Message):
    if len(m.command) == 2:
        editable = await m.reply_text(
            text="Checking User Details ..."
        )
        user = await bot.get_users(user_ids=int(m.command[1]))
        detail_text = f"**Name:** [{user.first_name}](tg://user?id={str(user.id)})\n" \
                      f"**Username:** `{user.username}`\n" \
                      f"**Upload as Doc:** `{await db.get_upload_as_doc(id=int(m.command[1]))}`\n" \
                      f"**Generate Screenshots:** `{await db.get_generate_ss(id=int(m.command[1]))}`\n"
        await editable.edit(
            text=detail_text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )


@NubBot.on_callback_query()
async def callback_handlers(bot: Client, cb: CallbackQuery):
    if "mergeNow" in cb.data:
        vid_list = list()
        await cb.message.edit(
            text="Please Wait ..."
        )
        duration = 0
        list_message_ids = QueueDB.get(cb.from_user.id, None)
        list_message_ids.sort()
        input_ = f"{Config.DOWN_PATH}/{cb.from_user.id}/input.txt"
        if list_message_ids is None:
            await cb.answer("Queue Empty!", show_alert=True)
            await cb.message.delete(True)
            return
        if len(list_message_ids) < 2:
            await cb.answer("Only One Video You Sent for Merging!", show_alert=True)
            await cb.message.delete(True)
            return
        if not os.path.exists(f"{Config.DOWN_PATH}/{cb.from_user.id}/"):
            os.makedirs(f"{Config.DOWN_PATH}/{cb.from_user.id}/")
        for i in (await bot.get_messages(chat_id=cb.from_user.id, message_ids=list_message_ids)):
            media = i.video or i.document
            try:
                await cb.message.edit(
                    text=f"Downloading `{media.file_name}` ..."
                )
            except MessageNotModified:
                QueueDB.get(cb.from_user.id).remove(i.message_id)
                await cb.message.edit("File Skipped!")
                await asyncio.sleep(3)
                continue
            file_dl_path = None
            try:
                c_time = time.time()
                file_dl_path = await bot.download_media(
                    message=i,
                    file_name=f"{Config.DOWN_PATH}/{cb.from_user.id}/{i.message_id}/",
                    progress=progress_for_pyrogram,
                    progress_args=(
                        "Downloading ...",
                        cb.message,
                        c_time
                    )
                )
            except Exception as downloadErr:
                print(f"Failed to Download File!\nError: {downloadErr}")
                QueueDB.get(cb.from_user.id).remove(i.message_id)
                await cb.message.edit("File Skipped!")
                await asyncio.sleep(3)
                continue
            metadata = extractMetadata(createParser(file_dl_path))
            try:
                if metadata.has("duration"):
                    duration += metadata.get('duration').seconds
                vid_list.append(f"file '{file_dl_path}'")
            except:
                await delete_all(root=f"{Config.DOWN_PATH}/{cb.from_user.id}/")
                QueueDB.update({cb.from_user.id: []})
                FormtDB.update({cb.from_user.id: None})
                await cb.message.edit("Video Corrupted!\nTry Again Later.")
                return
        __cache = list()
        for i in range(len(vid_list)):
            if vid_list[i] not in __cache:
                __cache.append(vid_list[i])
        vid_list = __cache
        if (len(vid_list) < 2) and (len(vid_list) > 0):
            await cb.message.edit("There only One Video in Queue!\nMaybe you sent same video multiple times.")
            return
        await cb.message.edit("Trying to Merge Videos ...")
        with open(input_, 'w') as _list:
            _list.write("\n".join(vid_list))
        merged_vid_path = await MergeVideo(
            input_file=input_,
            user_id=cb.from_user.id,
            message=cb.message,
            format_=FormtDB.get(cb.from_user.id, "mkv")
        )
        if merged_vid_path is None:
            await cb.message.edit(
                text="Failed to Merge Video!"
            )
            await delete_all(root=f"{Config.DOWN_PATH}/{cb.from_user.id}/")
            QueueDB.update({cb.from_user.id: []})
            FormtDB.update({cb.from_user.id: None})
            return
        await cb.message.edit("Successfully Merged Video!")
        await asyncio.sleep(Config.TIME_GAP)
        file_size = os.path.getsize(merged_vid_path)
        if int(file_size) > 2097152000:
            await cb.message.edit(f"Sorry Sir,\n\nFile Size Become {humanbytes(file_size)} !!\nI can't Upload to Telegram!\n\nSo Now Uploading to Streamtape ...")
            await UploadToStreamtape(file=merged_vid_path, editable=cb.message, file_size=file_size)
            await delete_all(root=f"{Config.DOWN_PATH}/{cb.from_user.id}/")
            QueueDB.update({cb.from_user.id: []})
            FormtDB.update({cb.from_user.id: None})
            return
        await cb.message.edit(
            text="Do you like to rename file?\nChoose a Button from below:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Rename File", callback_data="renameFile_Yes")],
                    [InlineKeyboardButton("Keep Default", callback_data="renameFile_No")]
                ]
            )
        )
    elif "cancelProcess" in cb.data:
        await cb.message.edit("Trying to Delete Working DIR ...")
        await delete_all(root=f"{Config.DOWN_PATH}/{cb.from_user.id}/")
        QueueDB.update({cb.from_user.id: []})
        FormtDB.update({cb.from_user.id: None})
        await cb.message.edit("Successfully Cancelled!")
    elif cb.data.startswith("showFileName_"):
        message_ = await bot.get_messages(chat_id=cb.message.chat.id, message_ids=int(cb.data.split("_", 1)[-1]))
        try:
            await bot.send_message(
                chat_id=cb.message.chat.id,
                text="This File Sir!",
                reply_to_message_id=message_.message_id,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Remove File", callback_data=f"removeFile_{str(message_.message_id)}")]
                    ]
                )
            )
        except FloodWait as e:
            await cb.answer("Don't Spam Unkil!", show_alert=True)
            await asyncio.sleep(e.x)
        except:
            media = message_.video or message_.document
            await cb.answer(f"Filename: {media.file_name}")
    elif "refreshFsub" in cb.data:
        if Config.UPDATES_CHANNEL:
            try:
                user = await bot.get_chat_member(chat_id=(int(Config.UPDATES_CHANNEL) if Config.UPDATES_CHANNEL.startswith("-100") else Config.UPDATES_CHANNEL), user_id=cb.message.chat.id)
                if user.status == "kicked":
                    await cb.message.edit(
                        text="Sorry Sir, You are Banned to use me. Contact my [Support Group](https://t.me/linux_repo).",
                        parse_mode="markdown",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                try:
                    invite_link = await bot.create_chat_invite_link(chat_id=(int(Config.UPDATES_CHANNEL) if Config.UPDATES_CHANNEL.startswith("-100") else Config.UPDATES_CHANNEL))
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    invite_link = await bot.create_chat_invite_link(chat_id=(int(Config.UPDATES_CHANNEL) if Config.UPDATES_CHANNEL.startswith("-100") else Config.UPDATES_CHANNEL))
                await cb.message.edit(
                    text="**You Still Didn't Join ☹️, Please Join My Updates Channel to use this Bot!**\n\nDue to Overload, Only Channel Subscribers can use the Bot!",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("🤖 Join Updates Channel", url=invite_link.invite_link)
                            ],
                            [
                                InlineKeyboardButton("🔄 Refresh 🔄", callback_data="refreshFsub")
                            ]
                        ]
                    ),
                    parse_mode="markdown"
                )
                return
            except Exception:
                await cb.message.edit(
                    text="Something went Wrong. Contact my [Support Group](https://t.me/linux_repo).",
                    parse_mode="markdown",
                    disable_web_page_preview=True
                )
                return
        await cb.message.edit(
            text=Config.START_TEXT,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Developer - @AbirHasan2005", url="https://t.me/AbirHasan2005"), InlineKeyboardButton("Support Group", url="https://t.me/linux_repo")], [InlineKeyboardButton("Bots Channel", url="https://t.me/Discovery_Updates")]]),
            disable_web_page_preview=True
        )
    elif "showThumbnail" in cb.data:
        db_thumbnail = await db.get_thumbnail(cb.from_user.id)
        if db_thumbnail is not None:
            await cb.answer("Sending Thumbnail ...", show_alert=True)
            await bot.send_photo(
                chat_id=cb.message.chat.id,
                photo=db_thumbnail,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Delete Thumbnail", callback_data="deleteThumbnail")]
                    ]
                )
            )
        else:
            await cb.answer("No Thumbnail Found for you in Database!")
    elif "deleteThumbnail" in cb.data:
        await db.set_thumbnail(cb.from_user.id, thumbnail=None)
        await cb.message.edit("Thumbnail Deleted from Database!")
    elif "triggerUploadMode" in cb.data:
        upload_as_doc = await db.get_upload_as_doc(cb.from_user.id)
        if upload_as_doc is False:
            await db.set_upload_as_doc(cb.from_user.id, upload_as_doc=True)
        elif upload_as_doc is True:
            await db.set_upload_as_doc(cb.from_user.id, upload_as_doc=False)
        await OpenSettings(m=cb.message, user_id=cb.from_user.id)
    elif "showQueueFiles" in cb.data:
        try:
            markup = await MakeButtons(bot, cb.message, QueueDB)
            await cb.message.edit(
                text="Here are the saved files list in your queue:",
                reply_markup=InlineKeyboardMarkup(markup)
            )
        except ValueError:
            await cb.answer("Your Queue Empty Unkil!", show_alert=True)
    elif cb.data.startswith("removeFile_"):
        if (QueueDB.get(cb.from_user.id, None) is not None) or (QueueDB.get(cb.from_user.id) != []):
            QueueDB.get(cb.from_user.id).remove(int(cb.data.split("_", 1)[-1]))
            await cb.message.edit(
                text="File removed from queue!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Go Back", callback_data="openSettings")]
                    ]
                )
            )
        else:
            await cb.answer("Sorry Unkil, Your Queue is Empty!", show_alert=True)
    elif "triggerGenSS" in cb.data:
        generate_ss = await db.get_generate_ss(cb.from_user.id)
        if generate_ss is True:
            await db.set_generate_ss(cb.from_user.id, generate_ss=False)
        elif generate_ss is False:
            await db.set_generate_ss(cb.from_user.id, generate_ss=True)
        await OpenSettings(cb.message, user_id=cb.from_user.id)
    elif "triggerGenSample" in cb.data:
        generate_sample_video = await db.get_generate_sample_video(cb.from_user.id)
        if generate_sample_video is True:
            await db.set_generate_sample_video(cb.from_user.id, generate_sample_video=False)
        elif generate_sample_video is False:
            await db.set_generate_sample_video(cb.from_user.id, generate_sample_video=True)
        await OpenSettings(cb.message, user_id=cb.from_user.id)
    elif "openSettings" in cb.data:
        await OpenSettings(cb.message, cb.from_user.id)
    elif cb.data.startswith("renameFile_"):
        if (QueueDB.get(cb.from_user.id, None) is None) or (QueueDB.get(cb.from_user.id) == []):
            await cb.answer("Sorry Unkil, Your Queue is Empty!", show_alert=True)
            return
        merged_vid_path = f"{Config.DOWN_PATH}/{str(cb.from_user.id)}/[@AbirHasan2005]_Merged.{FormtDB.get(cb.from_user.id).lower()}"
        if cb.data.split("_", 1)[-1] == "Yes":
            await cb.message.edit("Okay Unkil,\nSend me new file name!")
            try:
                ask_: Message = await bot.listen(cb.message.chat.id, timeout=300)
                if ask_.text:
                    ascii_ = e = ''.join([i if (i in string.digits or i in string.ascii_letters or i == " ") else "" for i in ask_.text])
                    new_file_name = f"{Config.DOWN_PATH}/{str(cb.from_user.id)}/{ascii_.replace(' ', '_').rsplit('.', 1)[0]}.{FormtDB.get(cb.from_user.id).lower()}"
                    await cb.message.edit(f"Renaming File Name to `{new_file_name.rsplit('/', 1)[-1]}`")
                    os.rename(merged_vid_path, new_file_name)
                    await asyncio.sleep(2)
                    merged_vid_path = new_file_name
            except TimeoutError:
                await cb.message.edit("Time Up!\nNow I will upload file with default name.")
                await asyncio.sleep(Config.TIME_GAP)
            except:
                pass
        await cb.message.edit("Extracting Video Data ...")
        duration = 1
        width = 100
        height = 100
        try:
            metadata = extractMetadata(createParser(merged_vid_path))
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds
            if metadata.has("width"):
                width = metadata.get("width")
            if metadata.has("height"):
                height = metadata.get("height")
        except:
            await delete_all(root=f"{Config.DOWN_PATH}/{cb.from_user.id}/")
            QueueDB.update({cb.from_user.id: []})
            FormtDB.update({cb.from_user.id: None})
            await cb.message.edit("The Merged Video Corrupted!\nTry Again Later.")
            return
        video_thumbnail = None
        db_thumbnail = await db.get_thumbnail(cb.from_user.id)
        if db_thumbnail is not None:
            video_thumbnail = await bot.download_media(message=db_thumbnail, file_name=f"{Config.DOWN_PATH}/{str(cb.from_user.id)}/thumbnail/")
            Image.open(video_thumbnail).convert("RGB").save(video_thumbnail)
            img = Image.open(video_thumbnail)
            img.resize((width, height))
            img.save(video_thumbnail, "JPEG")
        else:
            video_thumbnail = Config.DOWN_PATH + "/" + str(cb.from_user.id) + "/" + str(time.time()) + ".jpg"
            ttl = random.randint(0, int(duration) - 1)
            file_generator_command = [
                "ffmpeg",
                "-ss",
                str(ttl),
                "-i",
                merged_vid_path,
                "-vframes",
                "1",
                video_thumbnail
            ]
            process = await asyncio.create_subprocess_exec(
                *file_generator_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            e_response = stderr.decode().strip()
            t_response = stdout.decode().strip()
            if video_thumbnail is None:
                video_thumbnail = None
            else:
                Image.open(video_thumbnail).convert("RGB").save(video_thumbnail)
                img = Image.open(video_thumbnail)
                img.resize((width, height))
                img.save(video_thumbnail, "JPEG")
        await UploadVideo(
            bot=bot,
            cb=cb,
            merged_vid_path=merged_vid_path,
            width=width,
            height=height,
            duration=duration,
            video_thumbnail=video_thumbnail,
            file_size=os.path.getsize(merged_vid_path)
        )
        caption = f"© @{(await bot.get_me()).username}"
        if (await db.get_generate_ss(cb.from_user.id)) is True:
            await cb.message.edit("Now Generating Screenshots ...")
            generate_ss_dir = f"{Config.DOWN_PATH}/{str(cb.from_user.id)}"
            list_images = await generate_screen_shots(merged_vid_path, generate_ss_dir, 9, duration)
            if list_images is None:
                await cb.message.edit("Failed to get Screenshots!")
                await asyncio.sleep(Config.TIME_GAP)
            else:
                await cb.message.edit("Generated Screenshots Successfully!\nNow Uploading ...")
                photo_album = list()
                if list_images is not None:
                    i = 0
                    for image in list_images:
                        if os.path.exists(str(image)):
                            if i == 0:
                                photo_album.append(InputMediaPhoto(media=str(image), caption=caption))
                            else:
                                photo_album.append(InputMediaPhoto(media=str(image)))
                            i += 1
                await bot.send_media_group(
                    chat_id=cb.from_user.id,
                    media=photo_album
                )
        if ((await db.get_generate_sample_video(cb.from_user.id)) is True) and (duration >= 15):
            await cb.message.edit("Now Generating Sample Video ...")
            sample_vid_dir = f"{Config.DOWN_PATH}/{cb.from_user.id}/"
            ttl = int(duration*10 / 100)
            sample_video = await cult_small_video(
                video_file=merged_vid_path,
                output_directory=sample_vid_dir,
                start_time=ttl,
                end_time=(ttl + 10),
                format_=FormtDB.get(cb.from_user.id)
            )
            if sample_video is None:
                await cb.message.edit("Failed to Generate Sample Video!")
                await asyncio.sleep(Config.TIME_GAP)
            else:
                await cb.message.edit("Successfully Generated Sample Video!\nNow Uploading ...")
                sam_vid_duration = 5
                sam_vid_width = 100
                sam_vid_height = 100
                try:
                    metadata = extractMetadata(createParser(sample_video))
                    if metadata.has("duration"):
                        sam_vid_duration = metadata.get('duration').seconds
                    if metadata.has("width"):
                        sam_vid_width = metadata.get("width")
                    if metadata.has("height"):
                        sam_vid_height = metadata.get("height")
                except:
                    await cb.message.edit("Sample Video File Corrupted!")
                    await asyncio.sleep(Config.TIME_GAP)
                try:
                    c_time = time.time()
                    await bot.send_video(
                        chat_id=cb.message.chat.id,
                        video=sample_video,
                        thumb=video_thumbnail,
                        width=sam_vid_width,
                        height=sam_vid_height,
                        duration=sam_vid_duration,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            "Uploading Sample Video ...",
                            cb.message,
                            c_time,
                        )
                    )
                except Exception as sam_vid_err:
                    print(f"Got Error While Trying to Upload Sample File:\n{sam_vid_err}")
                    try:
                        await cb.message.edit("Failed to Upload Sample Video!")
                        await asyncio.sleep(Config.TIME_GAP)
                    except:
                        pass
        await cb.message.delete(True)
        await delete_all(root=f"{Config.DOWN_PATH}/{cb.from_user.id}/")
        QueueDB.update({cb.from_user.id: []})
        FormtDB.update({cb.from_user.id: None})
    elif "closeMeh" in cb.data:
        await cb.message.delete(True)
        await cb.message.reply_to_message.delete(True)

NubBot.run()
