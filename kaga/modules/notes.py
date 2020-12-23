import ast
import re
from html import escape
from io import BytesIO

from telegram import (
    MAX_MESSAGE_LENGTH,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.utils.helpers import mention_html

import kaga.modules.sql.notes_sql as sql
from kaga import LOGGER, MESSAGE_DUMP, dispatcher
from kaga.modules.connection import connected
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.helper_funcs.chat_status import (
    user_admin,
    user_admin_no_reply,
)
from kaga.modules.helper_funcs.misc import build_keyboard, revert_buttons
from kaga.modules.helper_funcs.msg_types import get_note_type
from kaga.modules.helper_funcs.string_handling import (
    escape_invalid_curly_brackets,
    markdown_to_html,
)

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")
STICKER_MATCHER = re.compile(r"^###sticker(!photo)?###:")
BUTTON_MATCHER = re.compile(r"^###button(!photo)?###:(.*?)(?:\s|$)")
MYFILE_MATCHER = re.compile(r"^###file(!photo)?###:")
MYPHOTO_MATCHER = re.compile(r"^###photo(!photo)?###:")
MYAUDIO_MATCHER = re.compile(r"^###audio(!photo)?###:")
MYVOICE_MATCHER = re.compile(r"^###voice(!photo)?###:")
MYVIDEO_MATCHER = re.compile(r"^###video(!photo)?###:")
MYVIDEONOTE_MATCHER = re.compile(r"^###video_note(!photo)?###:")


ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
}


# Do not async
def get(bot, update, notename, show_none=True, no_format=False):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        user.id
    else:
        chat_id = update.effective_chat.id

    note = sql.get_note(chat_id, notename)
    message = update.effective_message

    if note:
        # If we're replying to a message, reply to that message (unless it's an
        # error)
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id

        if note.is_reply:
            if MESSAGE_DUMP:
                try:
                    bot.forward_message(
                        chat_id=update.effective_chat.id,
                        from_chat_id=MESSAGE_DUMP,
                        message_id=note.value,
                    )
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text(
                            "Pesan ini sepertinya telah hilang - Saya akan menghapusnya "
                            "dari daftar catatan Anda."
                        )
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
            else:
                try:
                    bot.forward_message(
                        chat_id=update.effective_chat.id,
                        from_chat_id=chat_id,
                        message_id=note.value,
                    )
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text(
                            "Sepertinya pengirim asli catatan ini telah dihapus "
                            "pesan mereka - maaf! Minta admin bot Anda untuk mulai menggunakan file "
                            "pesan dump untuk menghindari ini. Saya akan menghapus catatan ini dari "
                            "catatan Anda yang disimpan."
                        )
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
        else:
            VALID_NOTE_FORMATTERS = [
                "first",
                "last",
                "fullname",
                "username",
                "id",
                "chatname",
                "mention",
            ]
            valid_format = escape_invalid_curly_brackets(
                note.value, VALID_NOTE_FORMATTERS
            )
            if valid_format:
                text = valid_format.format(
                    first=escape(message.from_user.first_name),
                    last=escape(
                        message.from_user.last_name
                        or message.from_user.first_name
                    ),
                    fullname=" ".join(
                        [
                            escape(message.from_user.first_name),
                            escape(message.from_user.last_name),
                        ]
                        if message.from_user.last_name
                        else [escape(message.from_user.first_name)]
                    ),
                    username="@" + escape(message.from_user.username)
                    if message.from_user.username
                    else mention_html(
                        message.from_user.id, message.from_user.first_name
                    ),
                    mention=mention_html(
                        message.from_user.id, message.from_user.first_name
                    ),
                    chatname=escape(message.chat.title)
                    if message.chat.type != "private"
                    else escape(message.from_user.first_name),
                    id=message.from_user.id,
                )
            else:
                text = ""

            keyb = []
            parseMode = ParseMode.HTML
            buttons = sql.get_buttons(chat_id, notename)
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                text = markdown_to_html(text)
                keyb = build_keyboard(buttons)

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    bot.send_message(
                        update.effective_chat.id,
                        text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        disable_web_page_preview=True,
                        reply_markup=keyboard,
                    )
                else:
                    if (
                        ENUM_FUNC_MAP[note.msgtype]
                        == dispatcher.bot.send_sticker
                    ):
                        ENUM_FUNC_MAP[note.msgtype](
                            chat_id,
                            note.file,
                            reply_to_message_id=reply_id,
                            reply_markup=keyboard,
                        )
                    else:
                        ENUM_FUNC_MAP[note.msgtype](
                            update.effective_chat.id,
                            note.file,
                            caption=text,
                            reply_to_message_id=reply_id,
                            parse_mode=parseMode,
                            reply_markup=keyboard,
                        )

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    message.reply_text(
                        "Sepertinya Anda mencoba menyebut seseorang yang belum pernah saya lihat sebelumnya. Jika Anda benar-benar "
                        "ingin menyebutkan mereka, meneruskan salah satu pesan mereka kepada saya, dan saya akan bisa "
                        "untuk menandai mereka!"
                    )
                elif FILE_MATCHER.match(note.value):
                    message.reply_text(
                        "Catatan ini adalah file yang diimpor dengan tidak benar dari bot lain - Saya tidak dapat menggunakan "
                        "Itu. Jika Anda benar-benar membutuhkannya, Anda harus menyimpannya lagi. Di "
                        "sementara itu, saya akan menghapusnya dari daftar catatan Anda."
                    )
                    sql.rm_note(chat_id, notename)
                else:
                    message.reply_text(
                        "Catatan ini tidak dapat dikirim, karena formatnya salah."
                    )

                    LOGGER.exception(
                        "Could not parse message #%s in chat %s",
                        notename,
                        str(chat_id),
                    )
                    LOGGER.warning("Message was: %s", str(note.value))
        return
    elif show_none:
        message.reply_text("Catatan ini tidak ada")


@typing_action
def cmd_get(update, context):
    args = context.args
    if len(args) >= 2 and args[1].lower() == "noformat":
        get(
            context.bot,
            update,
            args[0].lower(),
            show_none=True,
            no_format=True,
        )
    elif len(args) >= 1:
        get(context.bot, update, args[0].lower(), show_none=True)
    else:
        update.effective_message.reply_text("Dapatkan rekt")


def hash_get(update, context):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:].lower()
    get(context.bot, update, no_hash, show_none=False)


@user_admin
@typing_action
def save(update, context):
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(context.bot, update, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    msg = update.effective_message

    try:
        note_name, text, data_type, content, buttons = get_note_type(msg)
    except IndexError:
        msg.reply_text("Ini bukanlah hal yang benar T_T\nGunakan: /save <notename> <pesan/balas ke pesan>")
        return
    note_name = note_name.lower()

    if data_type is None:
        msg.reply_text("Bruh! tidak ada catatan")
        return

    if len(text.strip()) == 0:
        text = note_name

    sql.add_note_to_db(
        chat_id, note_name, text, data_type, buttons=buttons, file=content
    )

    msg.reply_text(
        "Menyimpan '`{note_name}`' di *{chat_name}*.\nDapatkan dengan `/get {note_name}`, atau`#{note_name}`!".format(
            note_name=note_name, chat_name=chat_name
        ),
        parse_mode=ParseMode.MARKDOWN,
    )


@user_admin
@typing_action
def clear(update, context):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    conn = connected(context.bot, update, chat, user.id)

    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    if len(args) >= 1:
        notename = args[0].lower()

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text(
                "Berhasil menghapus '`{note_name}`' dari {chat_name}!".format(
                    note_name=note_name, chat_name=chat_name
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            update.effective_message.reply_text(
                "Tidak ada catatan yang disimpan di {chat_name}!".format(
                    chat_name=chat_name
                )
            )
    else:
        msg.reply_text("Yeah let me clear nothing...")
        return
    

@typing_action
def list_notes(update, context):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
        msg = "*Catatan dalam {}:*\n"
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = ""
            msg = "*Catatan Lokal:*\n"
        else:
            chat_name = chat.title
            msg = "*Catatan disimpan di {}:*\n"

    note_list = sql.get_all_chat_notes(chat_id)
    des = "Anda bisa mendapatkan catatan dengan menggunakan `/get notename`, atau `#notename`.\n"
    for note in note_list:
        note_name = " × `{}`\n".format(note.name.lower())
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(
                msg, parse_mode=ParseMode.MARKDOWN
            )
            msg = ""
        msg += note_name

    if not note_list:
        update.effective_message.reply_text("Tidak ada catatan yang disimpan di sini!")

    elif len(msg) != 0:
        try:
            update.effective_message.reply_text(
                msg.format(chat_name) + des, parse_mode=ParseMode.MARKDOWN
            )
        except ValueError:
            update.effective_message.reply_text(
                "Terjadi masalah saat menampilkan daftar catatan, mungkin karena beberapa karakter tidak valid dalam nama catatan. Tanyakan di @ZeroBotSupport jika Anda tidak dapat menemukannya!"
            )


@user_admin
def clear_notes(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    chatmem = chat.get_member(user.id)
    if chatmem.status == "creator":
        allnotes = sql.get_all_chat_notes(chat.id)
        if not allnotes:
            msg.reply_text("Tidak ada catatan yang disimpan di sini yang harus saya hapus?")
            return
        else:
            msg.reply_text(
                "Apakah Anda benar-benar ingin menghapus semua catatan??",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Ya saya yakin️",
                                callback_data="rmnotes_true",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="⚠️ Batal",
                                callback_data="rmnotes_cancel",
                            )
                        ],
                    ]
                ),
            )

    else:
        msg.reply_text("Perintah ini hanya dapat digunakan oleh PEMILIK obrolan!")


@user_admin_no_reply
def rmbutton(update, context):
    query = update.callback_query
    userid = update.effective_user.id
    match = query.data.split("_")[1]
    chat = update.effective_chat

    usermem = chat.get_member(userid).status

    if match == "cancel" and usermem == "creator":
        return query.message.edit_text("Penghapusan catatan dibatalkan.")

    elif match == "true" and usermem == "creator":

        allnotes = sql.get_all_chat_notes(chat.id)
        count = 0
        notelist = []
        for notename in allnotes:
            count += 1
            note = notename.name.lower()
            notelist.append(note)

        for i in notelist:
            sql.rm_note(chat.id, i)
        query.message.edit_text(
            f"Berhasil membersihkan {count} catatan di {chat.title}."
        )


def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get("extra", {}).items():
        match = FILE_MATCHER.match(notedata)
        matchsticker = STICKER_MATCHER.match(notedata)
        matchbtn = BUTTON_MATCHER.match(notedata)
        matchfile = MYFILE_MATCHER.match(notedata)
        matchphoto = MYPHOTO_MATCHER.match(notedata)
        matchaudio = MYAUDIO_MATCHER.match(notedata)
        matchvoice = MYVOICE_MATCHER.match(notedata)
        matchvideo = MYVIDEO_MATCHER.match(notedata)
        matchvn = MYVIDEONOTE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end() :].strip()
            if notedata:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.TEXT
                )
        elif matchsticker:
            content = notedata[matchsticker.end() :].strip()
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.STICKER,
                    file=content,
                )
        elif matchbtn:
            parse = notedata[matchbtn.end() :].strip()
            notedata = parse.split("<###button###>")[0]
            buttons = parse.split("<###button###>")[1]
            buttons = ast.literal_eval(buttons)
            if buttons:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.BUTTON_TEXT,
                    buttons=buttons,
                )
        elif matchfile:
            file = notedata[matchfile.end() :].strip()
            file = file.split("<###TYPESPLIT###>")
            notedata = file[1]
            content = file[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.DOCUMENT,
                    file=content,
                )
        elif matchphoto:
            photo = notedata[matchphoto.end() :].strip()
            photo = photo.split("<###TYPESPLIT###>")
            notedata = photo[1]
            content = photo[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.PHOTO,
                    file=content,
                )
        elif matchaudio:
            audio = notedata[matchaudio.end() :].strip()
            audio = audio.split("<###TYPESPLIT###>")
            notedata = audio[1]
            content = audio[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.AUDIO,
                    file=content,
                )
        elif matchvoice:
            voice = notedata[matchvoice.end() :].strip()
            voice = voice.split("<###TYPESPLIT###>")
            notedata = voice[1]
            content = voice[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VOICE,
                    file=content,
                )
        elif matchvideo:
            video = notedata[matchvideo.end() :].strip()
            video = video.split("<###TYPESPLIT###>")
            notedata = video[1]
            content = video[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VIDEO,
                    file=content,
                )
        elif matchvn:
            video_note = notedata[matchvn.end() :].strip()
            video_note = video_note.split("<###TYPESPLIT###>")
            notedata = video_note[1]
            content = video_note[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VIDEO_NOTE,
                    file=content,
                )
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(
                chat_id,
                document=output,
                filename="failed_imports.txt",
                caption="File/foto ini gagal diimpor karena aslinya "
                "dari bot lain. Ini adalah batasan API telegram, dan tidak bisa "
                "dihindari. Maaf untuk ketidaknyamanannya!",
            )


def __stats__():
    return "× {} catatan, di {} obrolan.".format(
        sql.num_notes(), sql.num_chats()
    )


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return "Ada `{}` catatan dalam obrolan ini.".format(len(notes))


__help__ = """
Simpan data untuk pengguna masa depan dengan catatan!

Catatan sangat bagus untuk menyimpan informasi acak; nomor telepon, gif yang bagus, gambar lucu - apa saja!

 × /get <notename>: Dapatkan catatan dengan notename ini
 × #<notename>: Sama dengan /get
 × /notes atau /saved: Mendaftar semua catatan yang disimpan dalam obrolan

Jika Anda ingin mengambil konten catatan tanpa pemformatan apa pun, gunakan `/get <notename> noformat`. Ini bisa \
berguna saat memperbarui catatan saat ini.

*khusus Admin:*
 × /save <notename> <notedata>: Menyimpan notedata sebagai catatan dengan nama notename
Tombol dapat ditambahkan ke catatan dengan menggunakan sintaks tautan markdown standar - tautan seharusnya hanya diawali dengan \
`buttonurl:` bagian, seperti itu: `[somelink](buttonurl:example.com)`. Periksa /markdownhelp untuk info lebih lanjut.
 × /save <notename>: Menyimpan pesan yang dibalas sebagai catatan dengan nama notename
 × /clear <notename>: Hapus catatan dengan nama ini

*Pembuat obrolan saja:*
 × /rmallnotes: Hapus semua catatan yang disimpan dalam obrolan sekaligus.

 Contoh cara menyimpan catatan adalah melalui:
`/save Data Ini adalah beberapa data!`

Sekarang, siapa pun yang menggunakan "/get notedata", atau "#notedata" akan dibalas dengan "Ini adalah beberapa data!".

Jika Anda ingin menyimpan gambar, gif, stiker, atau data lainnya, lakukan hal berikut:
`/save notename` sambil membalas stiker atau data apa pun yang Anda inginkan. Sekarang, catatan di "#notename" berisi stiker yang akan dikirim sebagai balasan.

Tip: untuk mengambil catatan tanpa pemformatan, gunakan /get <notename> noformat
Ini akan mengambil catatan dan mengirimkannya tanpa memformatnya; memberi Anda penurunan harga mentah, memungkinkan Anda melakukan pengeditan dengan mudah.
"""

__mod_name__ = "Notes"

GET_HANDLER = CommandHandler("get", cmd_get, pass_args=True, run_async=True)
HASH_GET_HANDLER = MessageHandler(
    Filters.regex(r"^#[^\s]+") & ~Filters.chat_type.channel,
    hash_get,
    run_async=True,
)

SAVE_HANDLER = CommandHandler("save", save, run_async=True)
DELETE_HANDLER = CommandHandler("clear", clear, pass_args=True, run_async=True)

LIST_HANDLER = DisableAbleCommandHandler(
    ["notes", "saved"], list_notes, admin_ok=True, run_async=True
)
CLEARALLNOTES_HANDLER = CommandHandler(
    "rmallnotes", clear_notes, filters=Filters.chat_type.groups, run_async=True
)

RMBTN_HANDLER = CallbackQueryHandler(
    rmbutton, pattern=r"rmnotes_", run_async=True
)

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
dispatcher.add_handler(CLEARALLNOTES_HANDLER)
dispatcher.add_handler(RMBTN_HANDLER)
