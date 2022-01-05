import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

import os
import time
from chat import Chat
from config import Config
from pyrogram import Client, filters
from helper_func.progress_bar import progress_bar
from helper_func.dbhelper import Database as Db
import re
import requests
from urllib.parse import quote, unquote

db = Db()

async def _check_user(filt, c, m):
    chat_id = str(m.from_user.id)
    if chat_id in Config.ALLOWED_USERS:
        return True
    else :
        return False

check_user = filters.create(_check_user)

@Client.on_message(filters.document & check_user & filters.private)
async def save_doc(client, message):

    chat_id = message.from_user.id
    start_time = time.time()
    downloading = await client.send_message(chat_id, 'Downloading your File!')
    download_location = await client.download_media(
        message = message,
        file_name = Config.DOWNLOAD_DIR+'/',
        progress = progress_bar,
        progress_args = (
            'Initializing',
            downloading,
            start_time
        )
    )

    if download_location is None:
        return client.edit_message_text(
            text = 'Downloading Failed!',
            chat_id = chat_id,
            message_id = downloading.message_id
        )

    await client.edit_message_text(
        text = Chat.DOWNLOAD_SUCCESS.format(round(time.time()-start_time)),
        chat_id = chat_id,
        message_id = downloading.message_id
    )

    tg_filename = os.path.basename(download_location)
    try:
        og_filename = message.document.file_name
    except:
        og_filename = False

    if og_filename:
        #os.rename(Config.DOWNLOAD_DIR+'/'+tg_filename,Config.DOWNLOAD_DIR+'/'+og_filename)
        save_filename = og_filename
    else :
        save_filename = tg_filename

    ext = save_filename.split('.').pop()
    filename = str(round(start_time))+'.'+ext

    if ext in ['srt','ass']:
        os.rename(Config.DOWNLOAD_DIR+'/'+tg_filename,Config.DOWNLOAD_DIR+'/'+filename)
        db.put_sub(chat_id, filename)
        if db.check_video(chat_id):
            text = Chat.CHOOSE_CMD
        else:
            text = 'Subtitle file downloaded.\nNow send Video File!'

        await client.edit_message_text(
            text = text,
            chat_id = chat_id,
            message_id = downloading.message_id
        )

    elif ext in ['mp4','mkv']:
        os.rename(Config.DOWNLOAD_DIR+'/'+tg_filename,Config.DOWNLOAD_DIR+'/'+filename)
        db.put_video(chat_id, filename, save_filename)
        if db.check_sub(chat_id):
            text = Chat.CHOOSE_CMD
        else :
            text = 'Video file downloaded successfully.\nNow send Subtitle file!'
        await client.edit_message_text(
            text = text,
            chat_id = chat_id,
            message_id = downloading.message_id
        )

    else:
        text = Chat.UNSUPPORTED_FORMAT.format(ext)+f'\nFile = {tg_filename}'
        await client.edit_message_text(
            text = text,
            chat_id = chat_id,
            message_id = downloading.message_id
        )
        os.remove(Config.DOWNLOAD_DIR+'/'+tg_filename)


@Client.on_message(filters.video & check_user & filters.private)
async def save_video(client, message):

    chat_id = message.from_user.id
    start_time = time.time()
    downloading = await client.send_message(chat_id, 'Downloading your File!')
    download_location = await client.download_media(
        message = message,
        file_name = Config.DOWNLOAD_DIR+'/',
        progress = progress_bar,
        progress_args = (
            'Initializing',
            downloading,
            start_time
            )
        )

    if download_location is None:
        return client.edit_message_text(
            text = 'Downloading Failed!',
            chat_id = chat_id,
            message_id = downloading.message_id
        )

    await client.edit_message_text(
        text = Chat.DOWNLOAD_SUCCESS.format(round(time.time()-start_time)),
        chat_id = chat_id,
        message_id = downloading.message_id
    )

    tg_filename = os.path.basename(download_location)
    try:
        og_filename = message.video.file_name
    except:
        og_filename = False
    
    if og_filename:
        save_filename = og_filename
    else :
        save_filename = tg_filename
    
    ext = save_filename.split('.').pop()
    filename = str(round(start_time))+'.'+ext
    os.rename(Config.DOWNLOAD_DIR+'/'+tg_filename,Config.DOWNLOAD_DIR+'/'+filename)
    
    db.put_video(chat_id, filename, save_filename)
    if db.check_sub(chat_id):
        text = Chat.CHOOSE_CMD
    else :
        text = 'Video file downloaded successfully.\nNow send Subtitle file!'
    await client.edit_message_text(
            text = text,
            chat_id = chat_id,
            message_id = downloading.message_id
            )
@Client.on_message(filters.text & filters.private & filters.incoming)
async def filter(client, message):
    if update.message.via_bot != None:
        return

    search_message = client.send_message(chat_id=update.effective_chat.id, text="Searching your subtitle file")
    sub_name = update.effective_message.text
    full_index, title, keyword = search_sub(sub_name)
    inline_keyboard = []
    if len(full_index) == 0:
        client.edit_message_text(chat_id=update.effective_chat.id, message_id=search_message.message_id, text="No results found")
        return
    
    index = full_index[:15]
    for i in index:
        subtitle = title[i-1]
        key = keyword[i-1]
        inline_keyboard.append([InlineKeyboardButton(subtitle, callback_data=f"{key}")])

    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    client.edit_message_text(chat_id=update.effective_chat.id, message_id=search_message.message_id, text=f"Got the following results for your query *{sub_name}*. Select the preffered type from the below options", parse_mode="Markdown", reply_markup=reply_markup)
